import sciris as sc
from .utils import default_trackers, pretty_labels
import numpy as np

class ScenResult(sc.prettyobj):
    def __init__(self, name, model_name, model, obj=None, mult=None):
        self.name = name
        self.model_name = model_name
        self.model = model
        self.prog_info = self.model.prog_info # provides access to costing info
        self.programs = self.prog_info.programs
        self.pops = self.model.pops
        self.mult = mult
        self.obj = obj
        self.years = list(range(model.t[0], model.t[1]+1))
        self.uid = sc.uuid()
        self.created = sc.now()
        self.modified = sc.now()
        #self.results = []
        
    def model_attr(self):
        return self.model.__dict__
    
    def get_outputs(self, outcomes=None, seq=False, asdict=True, pretty=False):
        """
        outcomes: a list of model outcomes to return
        return: a list of outputs with same order as outcomes
        """
        if outcomes is None:
            outcomes = default_trackers()
        if sc.isstring(outcomes):
            outcomes = sc.promotetolist(outcomes)
        outs = self.model.get_output(outcomes, seq=seq)
        if asdict:
            output = sc.odict()
            for o,outcome in enumerate(outcomes):
                output[outcome] = outs[o]
        else: 
            output = outs
            if pretty and not seq:
                prettyvals = []
                for out, val in zip(outcomes, output):
                    if 'prev' in out:
                        prettyval = round(val* 100, 2)
                    else:
                        prettyval = round(val,0)
                    prettyvals.append(prettyval)
                output = prettyvals
        return output

    def get_allocs(self, ref=True, current=False):
        allocs = sc.odict()
        delta = 1e-5
        for name, prog in self.programs.items():
            spend = prog.annual_spend
            new_spend = np.zeros(len(self.years))
            new_spend[0] = spend[0]
            if not ref and prog.reference:
                spend -= spend[0] # baseline year is reference spending, subtracted from every year
            if current:
                spend = spend[:1]
            else:
                for i in range(1, len(self.years)):
                    if (spend[i] - new_spend[i-1])/(new_spend[i-1] + delta) > prog.max_inc:
                        new_spend[i] = new_spend[i-1]*(1 + prog.max_inc)
                    elif (spend[i] - new_spend[i-1])/(new_spend[i-1] + delta) < (-1)*prog.max_dec:
                        new_spend[i] = new_spend[i-1]*(1 - prog.max_dec)
                    else:
                        new_spend[i] = spend[i]
            # if not fixed and not prog.reference:
            #     spend -= spend[0]
            allocs[name] = new_spend
                    
        return allocs

    def get_covs(self, ref=True, unrestr=True):
        covs = sc.odict()
        #new_cov = np.zeros(len(self.years))
        for name, prog in self.programs.iteritems():
            cov = prog.get_cov(unrestr=unrestr)
            new_cov = np.zeros(len(self.years))
            new_cov[1] = cov[1]
            for i in range(2, len(self.years)):
                if cov[i] - new_cov[i-1] > prog.max_inc:
                   new_cov[i] = new_cov[i-1] +  prog.max_inc
                elif cov[i] - new_cov[i-1] < (-1)* prog.max_dec:
                    new_cov[i] = new_cov[i-1] - prog.max_dec
                else:
                    new_cov[i] = cov[i]
            if not ref and prog.reference:
                cov -= cov[0] # baseline year is reference cov, subtracted from every year
            covs[name] = new_cov
        return covs
    
    def get_freefunds(self):
        free = self.model.prog_info.free
        if self.mult is not None:
            free *= self.mult
        return free

    def get_currspend(self):
        return self.model.prog_info.curr

    def get_childscens(self):
        """ For calculating the impacts of each scenario with single intervention set to 0 coverage """
        cov = [0]
        allkwargs = []
        progset = self.programs.keys()
        base_progset = self.prog_info.base_progset()
        # zero cov scen
        kwargs = {'name': 'Scenario overall',
                  'model_name': self.model_name,
                  'scen_type': 'budget',
                  'progvals': {prog: cov for prog in base_progset}}
        allkwargs.append(kwargs)
        # scale down each program to 0 individually
        progvals = self.get_allocs(ref=True)
        for prog in progset:
            new_progvals = sc.dcp(progvals)
            new_progvals[prog] = cov
            kwargs = {'name': prog,
                      'model_name': self.model_name,
                      'scen_type': 'budget',
                      'progvals': new_progvals}
            allkwargs.append(kwargs)
        return allkwargs

    def plot(self, toplot=None):
        from .plotting import make_plots # This is here to avoid a circular import
        figs = make_plots(self, toplot=toplot)
        return figs
    
def reduce(results, quantiles=None, use_mean=False, bounds=None): # need to removal once finalized
        '''
        Combine multiple sims into a single sim statistically: by default, use
        the median value and the 10th and 90th percentiles for the lower and upper
        bounds. If use_mean=True, then use the mean and ±2 standard deviations
        for lower and upper bounds.

        Args:
            quantiles (dict): the quantiles to use, e.g. [0.1, 0.9] or {'low : '0.1, 'high' : 0.9}
            use_mean (bool): whether to use the mean instead of the median
            bounds (float): if use_mean=True, the multiplier on the standard deviation for upper and lower bounds (default 2)
            output (bool): whether to return the "reduced" sim (in any case, modify the multirun in-place)

        '''

        if use_mean:
            if bounds is None:
                bounds = 2
        else:
            if quantiles is None:
                quantiles = {'low':0.1, 'high':0.9}
            if not isinstance(quantiles, dict):
                try:
                    quantiles = {'low':float(quantiles[0]), 'high':float(quantiles[1])}
                except Exception as E:
                    errormsg = f'Could not figure out how to convert {quantiles} into a quantiles object: must be a dict with keys low, high or a 2-element array ({str(E)})'
                    raise ValueError(errormsg)

        # Store information on the sims
        outcomes = default_trackers()
        out = sc.odict()
        years = results[0].years
        
        #n_runs = len(self)
        #outputs = self.get_output()
        #reduced_res = sc.dcp(outputs[0])
        #reduced_res.metadata = dict(multi_run=True, n_runs=n_runs, quantiles=quantiles, use_mean=use_mean, bounds=bounds) # Store how this was parallelized
        
        # perform the statistcal calculations
        for r, res in enumerate(results):
            if res.name != 'Excess budget':
                out[res] = res.get_outputs(outcomes, seq=True, pretty=True)
                raw = {}
                for reskey in outcomes:
                    raw[reskey] = np.zeros(len(outcomes), len(years))
                    vals = res[reskey].values
                    raw[reskey][:,r] = vals
                for reskeys in outcomes:
                    axis = 1
                    output = out[res]
                    if use_mean:
                        r_mean = np.mean(raw[reskey], axis=axis)
                        r_std =  np.std(raw[reskey], axis=axis)
                        output[reskey].values[:] = r_mean
                        output[reskey].low = r_mean - bounds * r_std
                        output[reskey].high = r_mean + bounds * r_std
                    else:
                        output[reskey].values[:] = np.quantile(raw[reskey], q=0.5, axis=axis)
                        output[reskey].low = np.quantile(raw[reskey], q=quantiles['low'], axis=axis)
                        output[reskey].high = np.quantile(raw[reskey], q=quantiles['high'], axis=axis)
        return 
            
def mean(bounds=None, **kwargs):
    '''
    Alias for reduce(use_mean=True). See reduce() for full description.

    Args:
        bounds (float): multiplier on the standard deviation for the upper and lower bounds (default, 2)
        kwargs (dict): passed to reduce()
    '''
    return reduce(use_mean=True, bounds=bounds, **kwargs)

def median(quantiles=None, **kwargs):
    '''
    Alias for reduce(use_mean=False). See reduce() for full description.

    Args:
        quantiles (list or dict): upper and lower quantiles (default, 0.1 and 0.9)
        kwargs (dict): passed to reduce()
    '''
    return reduce(use_mean=False, quantiles=quantiles, **kwargs)

def write_results(results, projname=None, filename=None, folder=None):
    from .version import version
    from datetime import date
    """ Writes outputs and program allocations to an xlsx book.
    For each scenario, book will include:
        - sheet called 'outcomes' which contains all outputs over time
        - sheet called 'budget and coverage' which contains all program cost and coverages over time """
    if projname is None: projname = ''
    outcomes = default_trackers()
    labs = pretty_labels()
    rows = [labs[out] for out in outcomes]
    if filename is None: filename = 'outputs.xlsx'
    filepath = sc.makefilepath(filename=filename, folder=folder, ext='xlsx', default='%s outputs.xlsx' % projname)
    outputs = []
    sheetnames = ['Version', 'Outcomes', 'Budget & coverage']
    alldata = []
    allformats = []
    years = results[0].years
    nullrow = [''] * len(years)
    ### Version sheet
    data = [['Version', 'Date'], [version, date.today()]]
    alldata.append(data)

    # Formatting
    nrows = len(data)
    ncols = len(data[0])
    formatdata = np.zeros((nrows, ncols), dtype=object)
    formatdata[:, :] = 'plain'  # Format data as plain
    formatdata[:, 0] = 'bold'  # Left side bold
    formatdata[0, :] = 'header'  # Top with green header
    allformats.append(formatdata)
    
    ### Outcomes sheet
    headers = [['Scenario', 'Outcome'] + years + ['Cumulative']]
    '''names=[]
    for r, res in enumerate(results):
        this_name=res.name
        names.append(this_name)
    main_names = []
    for nm in names:
        if nm not in main_names:
            main_names.append(nm)
    n_runs = int(len(names) / len(main_names))
    
    raw = {nm: {out: np.zeros((n_runs, len(years))) for out in outcomes} for nm in main_names}
    #print(raw)
    out={} 
    for r, res in enumerate(results):
        for name in main_names:
            out[name] = res.get_outputs(outcomes, seq=True, pretty=True)
            print(out)
            for nm_key in main_names:
                   for out_key in outcomes:
                    vals = out[nm_key][out_key]
                    raw[nm_key][out_key][:] = vals
            print(raw)'''
                
    for r, res in enumerate(results):
        if res.name != 'Excess budget':
            out = res.get_outputs(outcomes, seq=True, pretty=True)
            for o, outcome in enumerate(rows):
                name = [res.name] if o == 0 else ['']
                thisout = out[o]
                if 'prev' in outcome.lower():
                    cumul = 'N/A'
                elif 'mortality' in outcome.lower():
                    cumul = 'N/A'
                else:
                    cumul = sum(thisout)
                outputs.append(name + [outcome] + list(thisout) + [cumul])
            outputs.append(nullrow)
    data = headers + outputs
    alldata.append(data)
    
    # Formatting
    nrows = len(data)
    ncols = len(data[0])
    formatdata = np.zeros((nrows, ncols), dtype=object)
    formatdata[:, :] = 'plain'  # Format data as plain
    formatdata[:, 0] = 'bold'  # Left side bold
    formatdata[0, :] = 'header'  # Top with green header
    allformats.append(formatdata)

    ### Cost & coverage sheet
    # this is grouped not by program, but by coverage and cost (within each scenario)
    outputs = []
    headers = [['Scenario', 'Program', 'Type', 'Cost-coverage type'] + years]
    for r, res in enumerate(results):
        if res.name != 'Excess budget':
            rows = res.programs.keys()
            spend = res.get_allocs(ref=True)
            cov = res.get_covs(unrestr=False) 
            #print(spend)
            # collate coverages first
            for r, prog in enumerate(rows):
                name = [res.name] if r == 0 else ['']
                costcov = res.programs[prog].costtype
                thiscov = cov[prog]
                outputs.append(name + [prog] + ['Coverage'] + [costcov] + list(thiscov))
            # collate spending second
            for r, prog in enumerate(rows):
                thisspend = spend[prog]
                costcov = res.programs[prog].costtype
                outputs.append([''] + [prog] + ['Budget'] + [costcov] + list(thisspend))
            outputs.append(nullrow)
        else:
            spend = res.get_allocs(ref=True)
            thisspend = spend['Excess budget not allocated']
            outputs.append(['Excess budget not allocated'] + ['N/A'] + ['Budget'] + ['N/A'] + list(thisspend))
            outputs.append(nullrow)
    data = headers + outputs
    alldata.append(data)

    # Formatting
    nrows = len(data)
    ncols = len(data[0])
    formatdata = np.zeros((nrows, ncols), dtype=object)
    formatdata[:, :] = 'plain'  # Format data as plain
    formatdata[:, 0] = 'bold'  # Left side bold
    formatdata[0, :] = 'header'  # Top with green header
    allformats.append(formatdata)

    formats = {
        'header': {'bold': True, 'bg_color': '#3c7d3e', 'color': '#ffffff'},
        'plain': {},
        'bold': {'bold': True}}
    sc.savespreadsheet(filename=filename, data=alldata, sheetnames=sheetnames, formats=formats, formatdata=allformats)
    return filepath