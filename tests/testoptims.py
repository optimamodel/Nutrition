import nutrition.ui as nu
from nutrition.data import Dataset
from nutrition.optimization import Optim

p = nu.Project('eg')
dataset = Dataset('default', 'default', name='eg', doload=True)
p.add_dataset(dataset)

kwargs = {'name':'test',
          'model_name': 'eg',
          'obj':'thrive',
          'mults':[1,2],
          'prog_set': ['IYCF 1', 'Vitamin A supplementation', 'Micronutrient powders'],
          'add_funds':10000000.}

optims = [Optim(**kwargs)]
p.add_optims(optims)
p.run_optims()

p.plot(key='test', toplot=['alloc'])
import pylab as pl
pl.show()



