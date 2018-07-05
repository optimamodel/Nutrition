import nutrition.ui as nu
from nutrition.scenarios import Scen
from nutrition.data import Dataset
import sciris.core as sc

p = nu.Project('example')
dataset = Dataset('default', 'default', name='example', doload=True)
p.add_dataset(dataset)

### define custom scenarios
kwargs1 = {'name':'test1',
         'model_name': 'example',
         'scen_type': 'coverage',
         'covs': [[.95]],
         'prog_set': ['Vitamin A supplementation']}

kwargs2 = sc.dcp(kwargs1)
kwargs2.update({'name': 'test2',
                'covs': [[.95]],
                'prog_set': ['IYCF 1']})

scen_list = [Scen(**kwargs1), Scen(**kwargs2)]
p.add_scens(scen_list)
p.run_scens()
p.plot(key='test1', toplot=['prevs'])
p.plot(key='test2', toplot=['prevs'])
p.plot(key='baseline', toplot=['prevs'])
import pylab as pl
pl.show()

# load in new dataset
dataset = Dataset('default', 'default', name='default2', doload=True)
p.add_dataset(dataset)


