import sciris.core as sc
from .results import ScenResult

class Scen(object):
    def __init__(self, name=None, model_name=None, scen_type=None, progvals=None, active=True):
        """
        Structure to define a scenario which can be used to fully instantiate a model instance in the project class.
        :param name: The name of the scenario (string)
        :param model_name: The name of the corresponding model object stored in Project (string)
        :param scen_type: Either 'coverage' or 'budget', depending on whether vals is an array of coverages or spending (string)
        :param progvals: an odict of lists, structured (progname, scenario)
        :param active: whether or not the scenario is to be run (boolean)
        """
        self.name = name
        self.model_name = model_name if model_name else None
        self.scen_type = scen_type
        self.vals = progvals.values()
        self.prog_set = progvals.keys()
        self.active = active

    def __repr__(self):
        output  = sc.desc(self)
        return output

    def get_attr(self):
        return self.__dict__

def run_scen(scen, model, obj=None, mult=None, setcovs=True):
    """ Function to run associated Scen and Model objects """
    model = sc.dcp(model)
    model.setup(scen, setcovs=setcovs)
    model.run_sim()
    res = ScenResult(scen.name, scen.model_name, model, obj=obj, mult=mult)
    return res
