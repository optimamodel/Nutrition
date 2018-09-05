import sciris as sc
from .results import ScenResult

class Scen(sc.prettyobj):
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

    def get_attr(self):
        return self.__dict__

    def get_childscens(self, base_progset=None):
        """ For calculating the impacts of each scenario with single intervention set to 0 coverage """
        cov = [0]
        allkwargs = []
        # zero cov scen
        baseprogs = base_progset if base_progset is not None else self.prog_set
        kwargs = {'name': 'Zero cov',
                  'model_name': self.model_name,
                  'scen_type': self.scen_type,
                  'progvals': {prog: cov for prog in baseprogs}}
        allkwargs.append(kwargs)
        # scale down each program to 0 individually
        progvals = {prog: val for prog, val in zip(self.prog_set, self.vals)}
        for prog in self.prog_set:
            new_progvals = sc.dcp(progvals)
            new_progvals[prog] = cov
            kwargs = {'name': prog,
                      'model_name': self.model_name,
                      'scen_type': self.scen_type,
                      'progvals': new_progvals}
            allkwargs.append(kwargs)
        return allkwargs

def run_scen(scen, model, obj=None, mult=None, setcovs=True):
    """ Function to run associated Scen and Model objects """
    model = sc.dcp(model)
    model.setup(scen, setcovs=setcovs)
    model.run_sim()
    res = ScenResult(scen.name, scen.model_name, model, obj=obj, mult=mult)
    return res

def make_scens(kwargs):
    """
    Makes the requested scenarios
    :param kwargs: a list of key word args
    :return: a list of scenarios
    """
    kwargs = sc.promotetolist(kwargs)
    scens = []
    for kwarg in kwargs:
        scens.append(Scen(**kwarg))
    return scens