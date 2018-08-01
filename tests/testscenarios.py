import nutrition.ui as nu
import sciris.core as sc

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
                'prog_set': ['IYCF 1']})

scen_list = [nu.Scen(**kwargs1), nu.Scen(**kwargs1)]
p.add_scens(scen_list)
p.run_scens()
p.plot()