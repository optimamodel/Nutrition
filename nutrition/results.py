import sciris.core as sc
from .plotting import make_plots

class ScenResult(object):
    def __init__(self, name, model_name, model, obj=None, mult=None):
        self.name = name
        self.model_name = model_name
        self.model = model
        self.programs = self.model.prog_info.programs
        self.pops = self.model.pops
        self.mult = mult
        self.obj = obj
        self.year_names = range(model.t[0], model.t[1]+1)
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