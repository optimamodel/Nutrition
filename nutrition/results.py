import copy

class ScenResult(object):
    def __init__(self, res):
        self.name = res.name
        self.model = res.model
        self.programs = self.model.prog_info.programs
        self.pops = self.model.pops
        self.t = res.t

    def get_outcomes(self, outcomes):
        """ outcomes: a list of model outcomes to return
         return: a dict of (outcome,output) pairs"""
        outs = {name:self.model.get_outcome(name) for name in outcomes}
        return outs

class Result(object):
    def __init__(self, model, comb, alloc):
        self.name = model.name
        self.model = model
        self.comb = comb
        self.alloc = alloc

    def get_outcomes(self, outcomes):
        outs = {name:self.model.get_outcome(name) for name in outcomes}
        return outs

class OptimResult(object):
    def __init__(self, optim):
        self.name = optim.name
        self.model = optim.model
        self.combs = optim.combs
        self.t = optim.t
        self.programs = optim.model.prog_info.programs
        self.optim_allocs = optim.optim_allocs
        self.curr_alloc = optim.curr
        self.optim_scens = self.get_optim_scens()
        self.curr_scen = self.get_curr_scen()

    def get_optim_scens(self):
        optim_scens = []
        for i, comb in enumerate(self.combs):
            alloc = self.optim_allocs[i]
            optim_model = self.run_model(alloc)
            optim_scens.append(Result(optim_model, comb, alloc))
        return optim_scens

    def get_curr_scen(self):
        curr_model = self.get_curr_model()
        curr_scen = Result(curr_model, 'curr', self.curr_alloc)
        return curr_scen

    def get_curr_model(self):
        curr_model = self.run_model(self.curr_alloc)
        return curr_model

    def run_model(self, alloc):
        model = copy.deepcopy(self.model)
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