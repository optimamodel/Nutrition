import nutrition.ui as nu
from nutrition.optimization import Optim
from nutrition.geospatial import Geospatial
import sciris as sc

# load in data to create model
p = nu.Project('eg')
p.load_data('demo', 'demo', name='eg')

kwargs = {'name': 'test1',
          'model_name': 'eg',
          'region_names': ['demo', 'demo'],
          'weights': 'thrive',
          'mults':[0,1],
          'prog_set': ['IFAS (community)', 'IFAS (hospital)', 'IYCF 1', 'Lipid-based nutrition supplements',
           'Multiple micronutrient supplementation', 'Micronutrient powders', 'Kangaroo mother care',
           'Public provision of complementary foods', 'Treatment of SAM',
           'Vitamin A supplementation', 'Zinc supplementation', 'Calcium supplementation', 'Mg for eclampsia', 'Mg for pre-eclampsia'],}
geo = Geospatial(**kwargs)
p.run_geospatial(geo=geo, maxtime=1, maxiter=1, swarmsize=1)
