import nutrition.ui as nu
from nutrition.optimization import Optim

doplot = True
dosave = False

# load in data to create model
p = nu.Project('eg')
p.load_data('demo', 'demo', name='eg')

## define custom optimization
kwargs1 = {'name':'test1',
          'model_name': 'eg',
          'obj':'thrive',
          'mults':[1,2],
          'prog_set': ['Vitamin A supplementation', 'IYCF 1'],
          'fix_curr': False,
          'add_funds':1e7}

kwargs2 = {'name':'test2',
          'model_name': 'eg',
          'obj':'thrive',
          'mults':[1,2],
          'prog_set': ['Micronutrient powders', 'Vitamin A supplementation', "IYCF 1"],
          'fix_curr': False,
          'add_funds':4e6}

optims = [Optim(**kwargs2)]
p.add_optims(optims)
p.run_optims(swarmsize=1, maxiter=1, maxtime=1)
if doplot: p.plot(optim=True)
if dosave: p.write_results('optim_results.xlsx')
