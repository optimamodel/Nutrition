import nutrition.ui as nu
from nutrition.optimization import Optim

doplot = 1
dosave = 0

# load in data to create model
p = nu.Project('eg')
p.load_data('demo', 'demo', name='eg')

## define custom optimization
kwargs1 = {'name':'test1',
          'model_name': 'eg',
          'obj':'thrive',
          'mults':[1,2],
          'prog_set': ['Vitamin A supplementation', 'IYCF 1'], # ['Micronutrient powders', 'IYCF 1'],
          'fix_curr': False,
          'add_funds':10000000}

kwargs2 = {'name':'test2',
          'model_name': 'eg',
          'obj':'thrive',
          'mults':[1,2],
          'prog_set': p.dataset().prog_names(), # ['Micronutrient powders', 'Vitamin A supplementation'],
          'fix_curr': False,
          'add_funds':10000000}

optims = [Optim(**kwargs1), Optim(**kwargs2)]
p.add_optims(optims)
p.run_optims(['test1'], swarmsize=1, maxiter=10, maxtime=10)
if doplot: p.plot(keys=['test1'], optim=True)
if dosave: p.write_results('optim_results.xlsx')
