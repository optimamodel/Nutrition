### demo scenarios and optimizations
import sciris as sc
from .scenarios import Scen
from .optimization import Optim

def demo_scens():
    # stunting reduction
    kwargs1 = {'name':       'Stunting example (coverage)',
               'model_name': 'demo',
               'scen_type':  'coverage',
               'progvals':   sc.odict({'IYCF 1':[1], 'Vitamin A supplementation':[1]})
               }
    
    kwargs2 = {'name':       'Stunting example (budget)',
               'model_name': 'demo',
               'scen_type':  'budget',
               'progvals':   sc.odict({'IYCF 1':[2e6], 'Vitamin A supplementation':[2e6]})
               }
    
    # wasting reduction
    kwargs3 = {'name':       'Wasting example',
               'model_name': 'demo',
               'scen_type':  'coverage',
               'progvals':   sc.odict({'Treatment of SAM':[1]})
               }
    
    # anaemia reduction
    kwargs4 = {'name':       'Anaemia example',
               'model_name': 'demo',
               'scen_type':  'coverage',
               'progvals': sc.odict({'Micronutrient powders':[1], 'IFAS (community)':[1], 'IFAS (retailer)':[1], 'IFAS (school)':[1]})
               }

    scens = [Scen(**kwargs) for kwargs in [kwargs1, kwargs2, kwargs3, kwargs4]]
    return scens

def demo_optims():
    kwargs1 = {'name': 'Maximize thrive',
              'model_name': 'demo',
              'mults':[1,2],
               'weights': sc.odict({'thrive': 1}),
              'prog_set': ['Vitamin A supplementation', 'IYCF 1', 'IFA fortification of maize',
                           'Balanced energy-protein supplementation',
                           'Public provision of complementary foods',
                           'Iron and iodine fortification of salt'],
              'fix_curr': False,
              'add_funds': 0,
              'filter_progs':False}
    
    optims = [Optim(**kwargs1)]
    return optims
