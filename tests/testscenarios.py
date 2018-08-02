import nutrition.ui as nu
import sciris.core as sc

doplot = 0
dosave = 1

# load in data to create model
p = nu.Project('eg')
p.load_data('demo', 'demo', name='eg')

### define custom scenarios
kwargs1 = {'name':'test1',
         'model_name': 'eg',
         'scen_type': 'coverage',
         'covs': [[.95], [0.], [0.8]],
         'prog_set': ['IFAS for pregnant women (community)', 'Multiple micronutrient supplementation', 'Vitamin A supplementation']}

kwargs2 = sc.dcp(kwargs1)
kwargs2.update({'name': 'test2',
                'covs': [[.95]],
                'prog_set': ['IYCF 1', 'Treatment of SAM']})

kwargs3 = {'name': 'IYCF at $10 mil',
         'model_name': 'eg',
         'scen_type': 'budget',
         'covs': [[10e6]],
         'prog_set': ['IYCF 1']}

scen_list = [nu.Scen(**kwargs1), nu.Scen(**kwargs2), nu.Scen(**kwargs3)]
p.add_scens(scen_list)
p.run_scens()
if doplot: p.plot()
if dosave: p.write_results('scen_results.xlsx')