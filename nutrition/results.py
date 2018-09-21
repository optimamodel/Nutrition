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

    def get_allocs(self, ref=True, current=False):
        allocs = sc.odict()
        for name, prog in self.programs.iteritems():
            spend = prog.annual_spend
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

    def plot(self, toplot=None):
        figs = make_plots(self, toplot=toplot)
        return figs