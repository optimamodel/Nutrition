### demo scenarios and optimizations
from .scenarios import Scen
from .optimization import Optim

def demo_scens():
    # stunting reduction
    kwargs1 = {'name': 'stunt',
         'model_name': 'demo',
         'scen_type': 'coverage',
         'covs': [[1], [1]],
         'prog_set': ['IYCF 1', 'Vitamin A supplementation']}
    # wasting reduction
    kwargs2 = {'name': 'wast',
                         'model_name': 'demo',
                         'scen_type': 'coverage',
                         'covs': [[1]],
                         'prog_set': ['Treatment of SAM']}
    # anaemia reduction
    kwargs3 = {'name': 'anaem',
                         'model_name': 'demo',
                         'scen_type': 'coverage',
                         'covs': [[1], [1], [1]],
                         'prog_set': ['Micronutrient powders', 'IFAS (community)', 'IFAS (retailer)', 'IFAS (school)']}

    scens = [Scen(**kwargs) for kwargs in [kwargs1, kwargs2, kwargs3]]
    return scens

def demo_optims():
    kwargs1 = {'name': 'thrive',
          'model_name': 'demo',
          'obj': 'thrive',
          'mults': [1,2],
          'prog_set': ['Vitamin A supplementation', 'IYCF 1'],
          'fix_curr': False,
          'add_funds':5000000}
    optims = [Optim(**kwargs1)]
    return optims
