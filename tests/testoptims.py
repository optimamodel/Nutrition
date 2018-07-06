import nutrition.ui as nu
from nutrition.optimization import Optim

# load in data to create model
p = nu.Project('eg')
p.load_data('demo', 'demo', name='eg')

## define custom optimization
kwargs = {'name':'test',
          'model_name': 'eg',
          'obj':'thrive',
          'mults':[1,2],
          'prog_set': ['IYCF 1', 'Vitamin A supplementation', 'Micronutrient powders'],
          'add_funds':10000000.}

optims = [Optim(**kwargs)]
p.add_optims(optims)
p.run_optims()

p.plot(keys=['test'] ,optim=True)




