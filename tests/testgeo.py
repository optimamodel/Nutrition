import nutrition.ui as nu
from nutrition.geospatial import Geospatial

# load in data to create model
p = nu.Project('Demo')
# three identical regions (same spreadsheet)
p.load_data('demo', 'demoregion1', name='Demo1')
p.load_data('demo', 'demoregion2', name='Demo2')
p.load_data('demo', 'demoregion3', name='Demo3')

kwargs = {'name': 'test1',
          'modelnames': ['Demo1', 'Demo2', 'Demo3'],
          'weights': 'thrive',
          'fix_curr': False,
          'fix_regionalspend': False,
          'add_funds': 0,
          'prog_set': ['IFA fortification of maize', 'IYCF 1', 'Lipid-based nutrition supplements',
                        'Multiple micronutrient supplementation', 'Micronutrient powders', 'Kangaroo mother care',
                        'Public provision of complementary foods', 'Treatment of SAM',  'Vitamin A supplementation',
                       'Mg for eclampsia', 'Zinc supplementation', 'Iron and iodine fortification of salt']}

geo = Geospatial(**kwargs)
results = p.run_geo(geo=geo, maxtime=999, parallel=True)
p.plot(geo=True)
import pylab as pl
pl.show()
