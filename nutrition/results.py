import sciris as sc
from .utils import default_trackers, pretty_labels
import numpy as np
import math as mt

class ScenResult(sc.prettyobj):
    def __init__(self, name, model_name, model, obj=None, mult=None, ramping=True):
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
        self.ramping = ramping
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
    
    def get_covs(self, ref=True, unrestr=True):
        covs = sc.odict()
        cov_diffs = []
        if self.ramping:
            for name, prog in self.programs.iteritems():
                check_cov = prog.get_cov(unrestr=unrestr)
                cov_diffs.append(mt.ceil(abs(check_cov[-1] - check_cov[0]) / prog.max_inc))
            max_time = np.nanmax(cov_diffs)
        for name, prog in self.programs.iteritems():
            cov = prog.get_cov(unrestr=unrestr)
            if self.ramping:
                new_cov = np.zeros(len(self.years))
                new_cov[0] = cov[0]
                if mt.ceil(abs(cov[-1] - cov[0]) / prog.max_inc) < max_time and abs(cov[-1] - cov[0]) != 0:
                    prog.max_inc = abs(cov[-1] - cov[0]) / max_time
                if mt.ceil(abs(cov[-1] - cov[0]) / prog.max_dec) < max_time and abs(cov[-1] - cov[0]) != 0:
                    prog.max_dec = abs(cov[-1] - cov[0]) / max_time
                for i in range(1, len(self.years)):
                    if cov[i] - new_cov[i-1] > prog.max_inc:
                       new_cov[i] = new_cov[i-1] + prog.max_inc
                    elif cov[i] - new_cov[i-1] < (-1) * prog.max_dec:
                        new_cov[i] = new_cov[i-1] - prog.max_dec
                    else:
                        new_cov[i] = cov[i]
               # if not ref and prog.reference:
                    #cov -= cov[0] # baseline year is reference cov, subtracted from every year
                covs[name] = new_cov
            else:
                if not ref and prog.reference:
                    cov -= cov[0] # baseline year is reference cov, subtracted from every year
                covs[name] = cov
        return covs

    def get_allocs(self, ref=True, current=False):
        allocs = sc.odict()
        n_years =  []
        for name, prog in self.programs.items():
            spend = prog.annual_spend
            covs = self.get_covs(unrestr=False)[name]
            rate = np.zeros(len(self.years))
            rate[0] = 0
            new_spend = np.zeros(len(self.years))
            new_spend[0] = spend[0]
            if self.ramping:
                for k in range(1, len(self.years)):
                    rate[k] = covs[k]/covs[k-1] if covs[k-1] != 0 else 1
                    new_spend[k] = new_spend[k-1] * rate[k]
                    
                allocs[name] = new_spend
                n = list(rate).index(1)
                n_years.append(n)
                max_length = max(n_years)
            
                
            else:
                if not ref and prog.reference:
                    spend -= spend[0] # baseline year is reference spending, subtracted from every year
                if current:
                    spend = spend[:1]
            # if not fixed and not prog.reference:
            #     spend -= spend[0]
            
                allocs[name] = spend
            
        return allocs

    
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


def reduce(results, n_runs, use_mean=False, quantiles=None, bounds=None, output=False):
    years = results[0].years
    esti = ['point', 'low', 'high']
    outcomes = default_trackers()
    if use_mean:
        if bounds is None:
            bounds = 2
    else:
        if quantiles is None:
            quantiles = {'low': 0.1, 'high': 0.9}
        if not isinstance(quantiles, dict):
            try:
                quantiles = {'low': float(quantiles[0]), 'high': float(quantiles[1])}
            except Exception as E:
                errormsg = f'Could not figure out how to convert {quantiles} into a quantiles object: must be a dict with keys low, high or a 2-element array ({str(E)})'
                raise ValueError(errormsg)
    reduce = {}

    for i in range(int(len(results)/n_runs)):
        raw = {o: {n: np.zeros(len(years)) for n in range(n_runs)} for o in outcomes}
        reduce[results[i * n_runs].name] = {o: {es: np.zeros(len(years)) for es in esti} for o in outcomes}

        for j in range(n_runs):
            out = results[i * n_runs + j].get_outputs(outcomes, seq=True, pretty=True)
            for out_key in outcomes:
                vals = out[out_key]
                raw[out_key][j] = vals
                # print(raw)
            # for default tracker outcomes
            for out_key in outcomes:
                axis = 0
                if use_mean:
                    r_mean = np.mean(list(raw[out_key].values()), axis=axis)
                    r_std = np.std(list(raw[out_key].values()), axis=axis)
                    reduce[results[i * n_runs].name][out_key]['point'] = r_mean
                    reduce[results[i * n_runs].name][out_key]['low'] = r_mean - bounds * r_std
                    reduce[results[i * n_runs].name][out_key]['high'] = r_mean + bounds * r_std
                else:
                    reduce[results[i * n_runs].name][out_key]['point'] = np.quantile(list(raw[out_key].values()), q=0.5, axis=axis)
                    reduce[results[i * n_runs].name][out_key]['low'] = np.quantile(list(raw[out_key].values()), q=quantiles['low'], axis=axis)
                    reduce[results[i * n_runs].name][out_key]['high'] = np.quantile(list(raw[out_key].values()), q=quantiles['high'], axis=axis)
    #df = pd.DataFrame(reduce)
    #df.to_excel('reduce_test.xlsx')
    return reduce


def write_results(results, reduced_results={}, projname=None, filename=None, folder=None, full_outcomes=False):
    """ Writes outputs and program allocations to an xlsx book.
    For each scenario, book will include:
        - sheet called 'outcomes' which contains all outputs over time
        - sheet called 'budget and coverage' which contains all program cost and coverages over time """
    if reduced_results:
        filepath = write_reduced_results(results, reduced_results, projname=projname, filename=filename, folder=folder)
        if not full_outcomes:
            return filepath
        filename = 'full_' + filename


    years = results[0].years
    rows, filepath, outputs, outcomes, sheetnames, nullrow, allformats, alldata = _write_results_outcomes(projname, filename, folder, years)

    ### Outcomes sheet
    headers = [['Scenario', 'Outcome'] + years + ['Cumulative']]
    for r, res in enumerate(results):
        if res.name != 'Excess budget':
            out = res.get_outputs(outcomes, seq=True, pretty=True)
            #print(out)
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

    nrows, ncols, formatdata, allformats, outputs, headers = _write_results_costcov(data, allformats, years)

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

    _write_results_finalise(data, allformats, filename, alldata, sheetnames)

    return filepath


def write_reduced_results(results, reduced_results, projname=None, filename=None, folder=None):
    """ Writes outputs and program allocations to an xlsx book.
    For each scenario, book will include:
        - sheet called 'outcomes' which contains all outputs over time
        - sheet called 'budget and coverage' which contains all program cost and coverages over time """

    estimate_labels = list(reduced_results[list(reduced_results.keys())[0]][list(reduced_results[list(reduced_results.keys())[0]].keys())[0]].keys())
    years = results[0].years
    rows, filepath, outputs, outcomes, sheetnames, nullrow, allformats, alldata = _write_results_outcomes(projname, filename, folder, years)

    ### Outcomes sheet
    headers = [['Scenario', 'Estimate', 'Outcome'] + years + ['Cumulative']]
    for r, res in enumerate(reduced_results):
        for esti in estimate_labels:
            if res != 'Excess budget':
                out = []
                for measure in list(reduced_results[res].keys()):
                    out.append(reduced_results[res][measure][esti])
                    #print(out)
                for o, outcome in enumerate(rows):
                    name = [res] if o == 0 else ['']
                    thisout = out[o]
                    if 'prev' in outcome.lower():
                        cumul = 'N/A'
                    elif 'mortality' in outcome.lower():
                        cumul = 'N/A'
                    else:
                        cumul = sum(thisout)
                    outputs.append(name + [esti] + [outcome] + list(thisout) + [cumul])
                outputs.append(nullrow)
    data = headers + outputs
    alldata.append(data)

    nrows, ncols, formatdata, allformats, outputs, headers = _write_results_costcov(data, allformats, years)

    ### Cost & coverage sheet
    # this is grouped not by program, but by coverage and cost (within each scenario)

    for r, res in enumerate(results):
        if res.name != 'Excess budget' and '#' not in res.name:
            rows = res.programs.keys()
            spend = res.get_allocs(ref=True)
            cov = res.get_covs(unrestr=False)
            # print(spend)
            # collate coverages first
            for p, prog in enumerate(rows):
                name = [res.name] if p == 0 else ['']
                costcov = res.programs[prog].costtype
                thiscov = cov[prog]
                outputs.append(name + [prog] + ['Coverage'] + [costcov] + list(thiscov))
            # collate spending second
            for p, prog in enumerate(rows):
                thisspend = spend[prog]
                costcov = res.programs[prog].costtype
                outputs.append([''] + [prog] + ['Budget'] + [costcov] + list(thisspend))
            outputs.append(nullrow)
        elif '#' not in res.name:
            spend = res.get_allocs(ref=True)
            thisspend = spend['Excess budget not allocated']
            outputs.append(['Excess budget not allocated'] + ['N/A'] + ['Budget'] + ['N/A'] + list(thisspend))
            outputs.append(nullrow)
    data = headers + outputs
    alldata.append(data)

    _write_results_finalise(data, allformats, filename, alldata, sheetnames)

    return filepath

def _write_results_outcomes(projname, filename, folder, years):
    from .version import version
    from datetime import date
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
    #print(results[1])
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

    return rows, filepath, outputs, outcomes, sheetnames, nullrow, allformats, alldata

def _write_results_costcov(data, allformats, years):
    # Formatting
    nrows = len(data)
    ncols = len(data[0])
    formatdata = np.zeros((nrows, ncols), dtype=object)
    formatdata[:, :] = 'plain'  # Format data as plain
    formatdata[:, 0] = 'bold'  # Left side bold
    formatdata[0, :] = 'header'  # Top with green header
    allformats.append(formatdata)

    outputs = []
    headers = [['Scenario', 'Program', 'Type', 'Cost-coverage type'] + years]

    return nrows, ncols, formatdata, allformats, outputs, headers

def _write_results_finalise(data, allformats, filename, alldata, sheetnames):
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

    return
