import numpy as np
import sciris as sc
from . import utils
import multiprocessing

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

def run_scen_(scen, model, obj=None, mult=None, setcovs=True, restrictcovs=True): # Single run supports previous version with no uncertainty
    """ Function to run associated Scen and Model objects """
    from .results import ScenResult # This is here to avoid a potentially circular import
    model = sc.dcp(model)
    model.setup(scen, setcovs=setcovs, restrictcovs=restrictcovs)
    model.run_sim()
    res = ScenResult(scen.name, scen.model_name, model, obj=obj, mult=mult)
    return res

def run_scen(scen, model, obj=None, mult=None, setcovs=True, restrictcovs=True, multi_run=False, num_procs=3, n_runs=4):
    """" Purspose is to consider multiple runs for each random parameter values generated."""
    num_cpus = multiprocessing.cpu_count()
    args = [scen, model, obj, mult, setcovs, restrictcovs]
    if multi_run:
        res = sc.odict()
        num_procs = num_procs if num_procs else num_cpus
        iterkwargs = [None] * n_runs
        for i in range(0, n_runs):
            iterkwargs[i] = args
        try:
            this_res = utils.run_parallel(one_run_scene_parallel, iterkwargs, num_procs)
            res.update(this_res)
        except RuntimeError as E: # Handle if run outside of __main__ on Windows
            if 'freeze_support' in E.args[0]: # For this error, add additional information
                errormsg = '''
                It appears you are trying to run with multiprocessing on Windows outside
                of the __main__ block; please see https://docs.python.org/3/library/multiprocessing.html
                for more information. The correct syntax to use is e.g.

                            if __name__ == '__main__':
                                p.run_scens()

                Alternatively, to run without multiprocessing, set multi_run=False.'''
                
                raise RuntimeError(errormsg) from E
            else: # For all other runtime errors, raise the original exception
                raise E
    else:
        res = one_run_scene(args)           
    return res
       
def one_run_scene(args):
    from .results import ScenResult # This is here to avoid a potentially circular import
    scen = args[0]
    model, obj, mult, setcovs, restrictcovs = args[1:]
    model = sc.dcp(model)
    model.setup(scen, setcovs=setcovs, restrictcovs=restrictcovs)
    model.run_sim()
    res = ScenResult(scen.name, scen.model_name, model, obj=obj, mult=mult)
    return res

@utils.trace_exception
def one_run_scene_parallel(args):
    res = one_run_scene(args)
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
        convertedvals = result.get_covs(unrestr=False)
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

def make_default_scen(modelname=None, model=None, scen_type=None, basename='Baseline'):
    """
    Creates and returns a prototype / default scenario for a particular Model.
    """

    # Default to 'coverage' scenario if not set.
    if scen_type is None:
        scen_type = 'coverage'

    # Get the set of programs in the model.
    progset = model.prog_info.base_progset()
    progvals = sc.odict([(prog,[]) for prog in progset])

    kwargs1 = {'name': basename,
              'model_name': modelname,
              'scen_type': scen_type,
              'progvals': progvals}

    default = Scen(**kwargs1)
    return default


