import sciris.core as sc
from .results import ScenResult

class Scen(object):
    def __init__(self, name=None, model_name=None, scen_type=None, covs=None, prog_set=None, active=True):
        self.name = name
        self.model_name = model_name if model_name else name
        self.scen_type = scen_type
        self.covs = [] if covs is None else covs
        self.prog_set = prog_set if prog_set else []
        self.active = active

    def __repr__(self):
        output  = sc.desc(self)
        return output

    def get_attr(self):
        return self.__dict__

def run_scen(scen, model, obj=None, mult=None, setcovs=True):
    model = sc.dcp(model)
    model.setup(scen, setcovs=setcovs)
    model.run_sim()
    res = ScenResult(scen.name, scen.model_name, model, obj=obj, mult=mult)
    return res
