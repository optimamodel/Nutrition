import nutrition.ui as nu
from nutrition.geospatial import Geospatial

if __name__ == '__main__':
    # load in data to create model
    p = nu.Project('eg')
    # three test regions
    #p.load_data(inputspath='PNG 2019 databook_' + 'Highlands' + ' 20190322.xlsx', name='PNG_Highlands')
    #p.load_data(inputspath='PNG 2019 databook_' + 'Islands' + ' 20190322.xlsx', name='PNG_Islands')
    #p.load_data(inputspath='PNG 2019 databook_' + 'Southern' + ' 20190322.xlsx', name='PNG_Southern')
    #p.load_data(inputspath='PNG 2019 databook_' + 'Momase' + ' 20190322.xlsx', name='PNG_Momase')
    p.load_data('demo', 'region1', name='Demo1')
    p.load_data('demo', 'region2', name='Demo2')
    p.load_data('demo', 'region3', name='Demo3')

    kwargs = {'name': 'test1',
              'modelnames': ['Demo1', 'Demo2', 'Demo3'],
              'weights': 'thrive',
              'fix_curr': False,
              'fix_regionalspend': False,
              'add_funds': 5e6,
              'prog_set': ['IFA fortification of maize', 'IYCF 1', 'Lipid-based nutrition supplements',
                            'Multiple micronutrient supplementation', 'Micronutrient powders', 'Kangaroo mother care',
                            'Public provision of complementary foods', 'Treatment of SAM',  'Vitamin A supplementation',
                           'Mg for eclampsia', 'Zinc supplementation', 'Iron and iodine fortification of salt']}

    geo = Geospatial(**kwargs)
    results = p.run_geo(geo=geo, maxiter=20, swarmsize=20, maxtime=200, dosave=True, parallel=False)
    p.write_results('testing.xlsx')
    #p.plot(toplot=['alloc'], geo=True)
