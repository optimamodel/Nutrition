##########################
### Contains the exercises for the second user group (3/8/18) ####

import nutrition.ui as nu
from nutrition.scenarios import Scen
from nutrition.data import Dataset
from nutrition.utils import restratify
from nutrition.settings import Settings
import pylab as pl

ss = Settings()
## Create project

p = nu.Project('Demo')

# load a dataset
p.load_data('demo', 'demo', name='Demo')

###### SINGLE SCALE-UP EXAMPLES

### COVERAGE SCENARIOS
# scale-up IYCF 1 to 95%
opts1 = {'name': 'IYCF at 95%',
         'model_name': 'Demo',
         'scen_type': 'coverage',
         'covs': [[.95]],
         'prog_set': ['IYCF 1']}

# scale-up treatment of SAM
opts2 = {'name': 'Treat SAM at 95%',
         'model_name': 'Demo',
         'scen_type': 'coverage',
         'covs': [[.95]],
         'prog_set': ['Treatment of SAM']}

# scale-up micronutrient powders
opts3 = {'name': 'Micro. powders at 95%',
         'model_name': 'Demo',
         'scen_type': 'coverage',
         'covs': [[.95]],
         'prog_set': ['Micronutrient powders']}

# add to project
scens = [Scen(**kwargs) for kwargs in [opts1]]
# p.run_scens(scens=scens)
# keys = [opts['name'] for opts in [opts1, opts2, opts3]]
# p.plot(keys=keys) # plots all scens


### BUDGET SCENARIOS # todo: doesn't seem to work properly
opts4 = {'name': 'IYCF at $10 mil',
         'model_name': 'Demo',
         'scen_type': 'budget',
         'covs': [[10e6]],
         'prog_set': ['IYCF 1']}
scens = [Scen(**opts4)]
p.run_scens(scens=scens)
p.plot('IYCF at $10 mil')
pl.show()

# TIME-VARYING SCALE-UP
# todo



###### CHANGE PARAMETERS
### LOAD IN NEW DATA
# explicitly load in the data so we can tinker with params


# TODO: check that the baseline plots work correctly..


######## OPTIMIZATIONS











