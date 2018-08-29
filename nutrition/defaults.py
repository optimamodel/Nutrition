"""
Creates defaults for the user in the web app.
Defaults are the following:
    - continued current program expenditure
    - program coverage scaled-down to zero
Defaults correspond to the data set which is loaded by the user.
"""
from .scenarios import make_scens

def get_defaults(modelname, model):
    """
    Assumes user has selected a data set to upload into the project.
    Both baseline and the zero scenario will be based on all the programs uploaded in the data book
    :param modelname: the name of the Model object
    :param model: a Model object for the baseline and zero coverage scenarios.
    :return: a list of default scenarios
    """
    # maintain current coverage
    progset = model.prog_info.prog_data.base_prog_set # todo: make this easier to access
    progvals = {prog:[] for prog in progset}
    kwargs1 = {'name': 'Baseline',
              'model_name': modelname,
              'scen_type': 'cov',
              'progvals': progvals}
    # scale down to zero coverage
    progvals = {prog: [0] for prog in progset}
    kwargs2 = {'name': 'Zero cov',
              'model_name': modelname,
              'scen_type': 'cov',
              'progvals': progvals}
    defaults = make_scens([kwargs1, kwargs2])
    return defaults
