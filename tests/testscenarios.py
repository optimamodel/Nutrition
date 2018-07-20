import nutrition.ui as nu
from nutrition.scenarios import Scen
from nutrition.data import Dataset
import sciris.core as sc

# load in data to create model
p = nu.Project('eg')
p.load_data('demo', 'demo', name='eg')

### define custom scenarios
kwargs1 = {'name':'test1',
         'model_name': 'eg',
         'scen_type': 'coverage',
         'covs': [[.95], [0.95]],
         'prog_set': ['Vitamin A supplementation', 'Micronutrient powders']}

kwargs2 = sc.dcp(kwargs1)
kwargs2.update({'name': 'test2',
                'covs': [[.95]],
                'prog_set': ['IYCF 1']})

scen_list = [Scen(**kwargs1), Scen(**kwargs2)]
p.add_scens(scen_list)
p.run_scens()
p.plot(keys=['test1', 'test2'])