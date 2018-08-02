import nutrition.ui as nu
from nutrition.optimization import Optim

doplot = False
dosave = True

# load in data to create model
p = nu.Project('eg')
p.load_data('demo', 'demo', name='eg')

## define custom optimization
kwargs1 = {'name':'test1',
          'model_name': 'eg',
          'obj':'thrive',
          'mults':[1,2],
          'prog_set': ['Micronutrient powders', 'IYCF 1'],
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
p.run_optims(['test2'], swarmsize=1, maxiter=1, maxtime=1)
if doplot: p.plot(keys=['test2'], optim=True)
if dosave: p.write_results('optim_results.xlsx')
