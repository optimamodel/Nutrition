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
        self.years = range(model.t[0], model.t[1]+1)
        self.uid = sc.uuid()
        self.created = sc.now()
        self.modified = sc.now()
        
    def model_attr(self):
        return self.model.__dict__
    
    def get_outputs(self, outcomes=None, seq=False, asdict=False, pretty=False):
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
        for name, prog in self.programs.items():
            spend = prog.annualspend
            if not ref and prog.reference:
                spend -= spend[0] # baseline year is reference spending, subtracted from every year
            if current:
                spend = spend[:1]
            allocs[name] = spend
        return allocs

    def get_covs(self, ref=True, popcov=True):
        covs = sc.odict()
        for name, prog in self.programs.iteritems():
            cov = prog.getcov(popcov=popcov)
            if not ref and prog.reference:
                cov -= cov[0] # baseline year is reference cov, subtracted from every year
            covs[name] = cov
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

def write_results(results, projname=None, filename=None, folder=None):
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
    sheetnames = ['Outcomes', 'Budget & coverage']
    alldata = []
    allformats = []
    years = results[0].years
    nullrow = [''] * len(years)

    ### Outcomes sheet
    headers = [['Scenario', 'Outcome'] + years + ['Cumulative']]
    for r, res in enumerate(results):
        out = res.get_outputs(outcomes, seq=True, pretty=True)
        for o, outcome in enumerate(rows):
            name = [res.name] if o == 0 else ['']
            thisout = out[o]
            if 'prev' in outcome.lower():
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
    headers = [['Scenario', 'Program', 'Type'] + years]
    for r, res in enumerate(results):
        rows = res.programs.keys()
        spend = res.get_allocs(ref=True)
        cov = res.get_covs(unrestr=False)
        # collate coverages first
        for r, prog in enumerate(rows):
            name = [res.name] if r == 0 else ['']
            thiscov = cov[prog]
            outputs.append(name + [prog] + ['Coverage'] + list(thiscov))
        # collate spending second
        for r, prog in enumerate(rows):
            thisspend = spend[prog]
            outputs.append([''] + [prog] + ['Budget'] + list(thisspend))
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