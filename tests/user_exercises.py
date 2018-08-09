##########################
### Contains the exercises for Nutrition training workshops ###

import nutrition.ui as nu
from nutrition.scenarios import make_scens
from nutrition.settings import Settings
from nutrition.utils import default_trackers
import sciris.core as sc
import pylab as pl

ss = Settings()

#### OPTIONS
cov = [.95]
modelname = 'Demo'
scentype = 'coverage'

## Create project

p = nu.Project(modelname)

# load a dataset
p.load_data('demo', 'demo', name=modelname)

def make_kwargs(name, progvals, modelname='Demo', scentype='coverage'):
    kwargs = {'name': name,
     'model_name': modelname,
     'scen_type': scentype,
     'progvals': progvals}
    return kwargs


##### MODEL COMPONENT EXERCISES #####
outcomes = default_trackers()

#### baseline scenario ####
#1a
a = make_kwargs('Baseline', {})

###########################
#### Stunting model ######

# QUESTION 1

# 1b
b = make_kwargs('1b', {'Public provision of complementary foods': cov})
# 1c
c = make_kwargs('1c', {'Lipid-based nutrition supplements': cov})
# 1d
d = make_kwargs('1d', {'Zinc supplementation': cov})
# 1e
e = make_kwargs('1e', {'Public provision of complementary foods': cov,
                                    'Lipid-based nutrition supplements': cov,
                                    'Zinc supplementation': cov})
f = make_kwargs('1f', {'Public provision of complementary foods': cov,
                                    'Lipid-based nutrition supplements': cov})

# QUESTION 2
#todo: IYCF packages defined in spreadsheet, but would like to be able to manually do this in code. waiting on web app implementation

# 2a
aa = make_kwargs('2a', {'IYCF 1': cov})
# 2b
bb = make_kwargs('2b', {'IYCF 2': cov})
cc = make_kwargs('2c', {'IYCF 3': cov})

scens = make_scens([a, b, c, d, e, f, aa, bb, cc])

p.run_scens(scens)

p.write_results(filename='stunting_ans.xlsx')

p.remove('scens')

####### WASTING MODEL #########
base = make_kwargs('Baseline', {})
## QUESTION 1

a = make_kwargs('1a', {'Cash transfers': cov,
                       'Public provision of complementary foods': cov})
scens = make_scens([base, a])
p.run_scens(scens)




## QUESTION 2

a = make_kwargs('2a', {'Treatment of SAM': cov})
# todo: turn on management of mam, not currently implemented.
# b = make


p.write_results(filename='wasting_ans.xlsx')


#######



import pylab as pl
p.plot()
pl.show()






