### demo scenarios and optimizations
import sciris as sc
from .scenarios import Scen
from .optimization import Optim

def demo_scens():
    # baseline
    kwargs0 = {'name':       'Baseline',
               'model_name': 'demo',
               'scen_type':  'coverage',
               'progvals':   sc.odict()
               }
    
    # stunting reduction
    kwargs1 = {'name':       'Stunting example',
               'model_name': 'demo',
               'scen_type':  'coverage',
               'progvals':   sc.odict({'IYCF 1':[1], 'Vitamin A supplementation':[1]})
               }
    
    # wasting reduction
    kwargs2 = {'name':       'Wasting example',
               'model_name': 'demo',
               'scen_type':  'coverage',
               'progvals':   sc.odict({'Treatment of SAM':[1]})
               }
    
    # anaemia reduction
    kwargs3 = {'name':       'Anaemia example',
               'model_name': 'demo',
               'scen_type':  'coverage',
               'progvals': sc.odict({'Micronutrient powders':[1], 'IFAS (community)':[1], 'IFAS (retailer)':[1], 'IFAS (school)':[1]})
               }

    scens = [Scen(**kwargs) for kwargs in [kwargs0, kwargs1, kwargs2, kwargs3]]
    return scens

def demo_optims():
    kwargs1 = {'name': 'Maximize thrive',
          'model_name': 'demo',
          'obj':'thrive',
          'mults':[1,2],
          'prog_set': ['Vitamin A supplementation', 'IYCF 1'],
          'fix_curr': False,
          'add_funds':1e7,
          'filter_progs':False}
    
    optims = [Optim(**kwargs1)]
    return optims
