### demo scenarios and optimizations
import sciris as sc
from .scenarios import Scen
from .optimization import Optim
from .geospatial import Geospatial

def demo_scens(default=None, scen_type=None):
    if default is None:
        default = False
    if scen_type is None:
        scen_type = 'coverage'
    
    if default:
        kwargs = {'name':       'Default scenario (%s)' % scen_type,
                  'model_name': 'demo',
                  'scen_type':  scen_type,
                  'progvals':   sc.odict()
           }
        scen = Scen(**kwargs)
        return scen
    else:
        
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
              'model_name': None,
              'mults':[1,2],
               'weights': sc.odict({'thrive': 1}),
              'prog_set': ['Vitamin A supplementation', 'IYCF 1', 'IFA fortification of maize',
                           'Balanced energy-protein supplementation',
                           'Public provision of complementary foods',
                           'Iron and iodine fortification of salt'],
              'fix_curr': False,
              'add_funds': 0,
              'filter_progs':True}
    
    optims = [Optim(**kwargs1)]
    return optims

def demo_geos():
    kwargs1 = {'name': 'Geospatial optimization',
          'modelnames': [None],
          'weights': 'thrive',
          'fix_curr': False,
          'fix_regionalspend': False,
          'add_funds': 0,
          'prog_set': ['IFA fortification of maize', 'IYCF 1', 'Lipid-based nutrition supplements',
                        'Multiple micronutrient supplementation', 'Micronutrient powders', 'Kangaroo mother care',
                        'Public provision of complementary foods', 'Treatment of SAM',  'Vitamin A supplementation',
                       'Mg for eclampsia', 'Zinc for treatment + ORS', 'Iron and iodine fortification of salt']}
    
    geos = [Geospatial(**kwargs1)]
    return geos


