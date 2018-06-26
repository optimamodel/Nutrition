import sciris.core as sc
from .plotting import make_plots

class BaseResult(object):
    def __init__(self, name=None):
        self.name = name
        self.uid = sc.uuid()
        self.created = sc.today()
        self.modified = sc.today()
    
    def __repr__(self):
        output = sc.desc(self)
        return output
    
    def model_attr(self):
        return self.model.__dict__
    
    def get_outputs(self, outcomes, seq=False):
        """ outcomes: a list of model outcomes to return
         return: a dict of (outcome,output) pairs"""
        outs = [self.model.get_output(name, seq=seq) for name in outcomes]
        return outs
    
    def plot(self, toplot=None):
        figs = make_plots(self, toplot=toplot)
        return figs


class ScenResult(BaseResult):
    def __init__(self, res):
        BaseResult.__init__(self)
        self.name = res.name
        self.model = res.model
        self.programs = self.model.prog_info.programs
        self.pops = self.model.pops
        self.year_names = res.year_names

    

class Result(BaseResult):
    def __init__(self, model, comb, alloc):
        self.name = model.name
        self.model = model
        self.comb = comb
        self.alloc = alloc


class OptimResult(BaseResult):
    def __init__(self, optim):
        self.name = optim.name
        self.model = optim.model
        self.mults = optim.mults
        self.combs = optim.combs
        self.year_names = optim.year_names
        self.programs = optim.model.prog_info.programs
        self.optim_allocs = optim.optim_allocs
        self.curr_alloc = optim.curr
        self.optim_scens = self._get_optim_scens()
        self.curr_scen = self._get_curr_scen()

    def _get_optim_scens(self):
        optim_scens = []
        for i, comb in enumerate(self.combs):
            alloc = self.optim_allocs[i]
            optim_model = self._run_model(alloc)
            optim_scens.append(Result(optim_model, comb, alloc))
        return optim_scens

    def _get_curr_scen(self):
        curr_model = self._get_curr_model()
        curr_scen = Result(curr_model, 'curr', self.curr_alloc)
        return curr_scen

    def _get_curr_model(self):
        curr_model = self._run_model(self.curr_alloc)
        return curr_model

    def _run_model(self, alloc):
        model = sc.dcp(self.model)
        covs = self.get_covs(alloc)
        model.run_sim(covs, restr_cov=False)
        return model

    def get_covs(self, alloc):
        covs = []
        for i, prog in enumerate(self.programs):
            covs.append(prog.func(alloc[i]))
        return covs

    def create_dict(self, allocations):
        """Ensure keys and values have matching orders"""
        keys = [program.name for program in self.programs]
        returnDict = {key: value for key, value in zip(keys, allocations)}
        return returnDict