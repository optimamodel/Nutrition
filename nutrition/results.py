import sciris as sc
from .plotting import make_plots
from .model import default_trackers

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

    def get_allocs(self, ref=True):
        allocs = sc.odict()
        for name, prog in self.programs.iteritems():
            spend = prog.annual_spend
            if not ref and prog.reference:
                spend -= spend[0] # baseline year is reference spending, subtracted from every year
            allocs[name] = spend
        return allocs

    def get_childscens(self):
        """ For calculating the impacts of each scenario with single intervention set to 0 coverage """
        cov = [0]
        allkwargs = []
        progset = self.programs.iterkeys()
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
        figs = make_plots(self, toplot=toplot)
        return figs