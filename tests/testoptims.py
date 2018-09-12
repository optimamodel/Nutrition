import nutrition.ui as nu
from nutrition.optimization import Optim
import numpy as np

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
          'add_funds':1e7,
          'filter_progs':False}

kwargs2 = {'name':'test2',
          'model_name': 'eg',
          'obj':'thrive',
          'mults':[1,2],
          'prog_set':  ['IFAS (community)', 'IFAS (hospital)', 'IYCF 1', 'Lipid-based nutrition supplements',
           'Multiple micronutrient supplementation', 'Micronutrient powders',
           'Public provision of complementary foods', 'Treatment of SAM',
           'Vitamin A supplementation', 'Zinc supplementation', 'Calcium supplementation', 'Mg for eclampsia', 'Mg for pre-eclampsia'],
          'fix_curr': False}

# custom objective
kwargs3 = {'name': 'test3',
           'model_name': 'eg',
           'obj': 'thrive_anaem',
           'mults':[1,2,4],
           'weights': np.array([-1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
           'prog_set':  ['IYCF 3', 'Balanced energy-protein supplementation',
                         'Multiple micronutrient supplementation',
                         'Public provision of complementary foods',
                         'Vitamin A supplementation', 'IPTp', 'IFAS (school)'],
           'fix_curr': False}

optims = [Optim(**kwargs2)]
p.add_optims(optims)
p.run_optim(parallel=True)
if doplot: p.plot(optim=True)
if dosave: p.write_results('optim_results.xlsx')
