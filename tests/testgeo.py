import nutrition.ui as nu
from nutrition.optimization import Optim
from nutrition.geospatial import Geospatial
import sciris as sc

# load in data to create model
p = nu.Project('Demo')
# three identical regions (same spreadsheet)
p.load_data('demo', 'demoregion1', name='Demo1')
p.load_data('demo', 'demoregion1', name='Demo2')
p.load_data('demo', 'demoregion1', name='Demo3')

kwargs = {'name': 'test1',
          'model_names': ['Demo1', 'Demo2', 'Demo3'],
          'region_names': ['demoregion1', 'demoregion2', 'demoregion3'],
          'weights': 'thrive',
          'fix_curr': False,
          'fix_regionalspend': False,
          'add_funds': 1e6,
          'prog_set': ['IFA fortification of maize', 'IYCF 1', 'Lipid-based nutrition supplements',
                        'Multiple micronutrient supplementation', 'Micronutrient powders', 'Kangaroo mother care',
                        'Public provision of complementary foods', 'Treatment of SAM',  'Vitamin A supplementation',
                       'Mg for eclampsia', 'Zinc for treatment + ORS', 'Iron and iodine fortification of salt']}

geo = Geospatial(**kwargs)
results = p.run_geospatial(geo=geo)
p.plot(geo=True)
