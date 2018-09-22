"""
Creates defaults for the user in the web app.
Defaults are the following:
    - continued current program expenditure
Defaults correspond to the data set which is loaded by the user.
"""
from .scenarios import make_scens
import sciris as sc

def get_defaults(modelname, model, basename='Baseline'):
    """
    Assumes user has selected a data set to upload into the project.
    Baseline will be based on all the programs uploaded in the data book.
    :param modelname: the name of the Model object
    :param model: a Model object for the baseline scenario.
    :param basename: the name of the baseline scenario
    :return: a list of default scenarios
    """
    progset = model.prog_info.base_progset()
    # maintain current coverage
    progvals = sc.odict([(prog,[]) for prog in progset])
    kwargs1 = {'name': basename,
              'model_name': modelname,
              'scen_type': 'cov',
              'progvals': progvals}
    defaults = make_scens(kwargs1)
    return defaults
