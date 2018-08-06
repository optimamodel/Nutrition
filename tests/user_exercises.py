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
         'progvals': {'IYCF': [0.95]}}

# scale-up treatment of SAM
opts2 = {'name': 'Treat SAM at 95%',
         'model_name': 'Demo',
         'scen_type': 'coverage',
         'progvals': {'Treatment of SAM': [0.95]}}

# scale-up micronutrient powders
opts3 = {'name': 'Micro. powders at 95%',
         'model_name': 'Demo',
         'scen_type': 'coverage',
         'progvals': {'Micronutrient powders': [0.95]}}

# add to project
scens = [Scen(**kwargs) for kwargs in [opts1]]
# p.run_scens(scens=scens)
# keys = [opts['name'] for opts in [opts1, opts2, opts3]]
# p.plot(keys=keys) # plots all scens


### BUDGET SCENARIOS
opts4 = {'name': 'IYCF at $10 mil',
         'model_name': 'Demo',
         'scen_type': 'budget',
         'progvals': {'IYCF 1': [10e6]}}

scens = [Scen(**opts4)]
p.run_scens(scens=scens)
p.plot('IYCF at $10 mil')
pl.show()

# TIME-VARYING SCALE-UP
# todo



###### CHANGE PARAMETERS
### LOAD IN NEW DATA
# explicitly load in the data so we can tinker with params



######## OPTIMIZATIONS











