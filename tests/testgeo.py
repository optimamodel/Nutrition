import nutrition.ui as nu
from nutrition.geospatial import Geospatial

time_trends = True
# load in data to create model
p = nu.Project('Demo')
# three identical regions (same spreadsheet)
p.load_data('demo', 'region1', name='Demo1', time_trend=time_trends)
p.load_data('demo', 'region2', name='Demo2', time_trend=time_trends)
# p.load_data('demo', 'region3', name='Demo3', time_trend=time_trends)

kwargs = {'name': 'test1',
          'modelnames': ['Demo1', 'Demo2'],
          'weights': 'thrive',
          'fix_curr': False,
          'fix_regionalspend': False,
          'add_funds': 5e6,
          'prog_set': ['IYCF 1', 'IFA fortification of maize', 'Lipid-based nutrition supplements',
                        'Multiple micronutrient supplementation', 'Micronutrient powders', 'Kangaroo mother care',
                        'Public provision of complementary foods', 'Treatment of SAM',  'Vitamin A supplementation',
                       'Mg for eclampsia', 'Zinc supplementation', 'Iron and iodine fortification of salt'][:3]}

geo = Geospatial(**kwargs)
results = p.run_geo(geo=geo, maxiter=4, swarmsize=4, maxtime=20, parallel=False)
p.write_results('geo_results_compare.xlsx')
p.plot(geo=True)
