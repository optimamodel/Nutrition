import nutrition.ui as nu
from nutrition.optimization import Optim
from nutrition.geospatial import Geospatial
import sciris as sc

# load in data to create model
p = nu.Project('Demo')
p.load_data('demo', 'demoregion1', name='Demo1')
p.load_data('demo', 'demoregion2', name='Demo2')


kwargs = {'name': 'test1',
          'model_names': ['Demo1', 'Demo2'],
          'region_names': ['demoregion1', 'demoregion2'],
          'weights': 'thrive',
          'fix_curr': True,
          # 'mults': [1,2],
          'add_funds': 10e6,
          'prog_set': ['IFA fortification of maize', 'Zinc for treatment + ORS', 'IFAS (community)', 'IFAS (hospital)', 'IYCF 1', 'Lipid-based nutrition supplements',
           'Multiple micronutrient supplementation', 'Micronutrient powders', 'Kangaroo mother care',
           'Public provision of complementary foods', 'Treatment of SAM',
           'Vitamin A supplementation', 'Zinc supplementation', 'Calcium supplementation', 'Mg for eclampsia', 'Mg for pre-eclampsia'],}
geo = Geospatial(**kwargs)
p.run_geospatial(geo=geo, maxtime=40, maxiter=5, swarmsize=5)
