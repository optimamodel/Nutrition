import numpy as np
import sciris as sc

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
        self.model_name = model_name
        self.scen_type = scen_type
        self.vals = list(progvals.values())
        self.prog_set = list(progvals.keys())
        self.active = active

    def get_attr(self):
        return self.__dict__

def run_scen(scen, model, obj=None, mult=None, setcovs=True, restrictcovs=True):
    """ Function to run associated Scen and Model objects """
    from .results import ScenResult # This is here to avoid a potentially circular import
    model = sc.dcp(model)
    model.setup(scen, setcovs=setcovs, restrictcovs=restrictcovs)
    model.runsim()
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

def convert_scen(scen, model):
    """ In order to access the complimentary spending/coverage, the results object must be obtained. """
    result = run_scen(scen, model)
    if 'ov' in scen.scen_type:
        convertedvals = result.get_allocs()
        scen_type = 'budget'
    else:
        convertedvals = result.getcovs(popcov=False)
        scen_type = 'coverage'
    newprogvals = sc.odict() # Create new dict to hold the converted values
    for k,key in convertedvals.enumkeys(): # Loop over programs
        newprogvals[key] = sc.dcp(scen.vals[k]) # Copy current values list
        for v,val in enumerate(newprogvals[key]): # Loop over values
            if val is not None and not np.isnan(val):
                newprogvals[key][v] = convertedvals[key][v+1]
    name = scen.name + ' (%s)' % scen_type
    converted = Scen(name=name, model_name=scen.model_name, scen_type=scen_type, progvals=newprogvals)
    return converted