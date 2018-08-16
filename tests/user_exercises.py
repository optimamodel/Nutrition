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
#1
base = make_kwargs('Baseline', {})

###########################
#### Stunting model ######

# QUESTION 2

a = make_kwargs('2a', {'Public provision of complementary foods': cov})
b = make_kwargs('2b', {'Lipid-based nutrition supplements': cov})
c = make_kwargs('2c', {'Zinc supplementation': cov})
d = make_kwargs('2d', {'Public provision of complementary foods': cov,
                                    'Lipid-based nutrition supplements': cov,
                                    'Zinc supplementation': cov})
e = make_kwargs('2e', {'Public provision of complementary foods': cov,
                                    'Lipid-based nutrition supplements': cov})

# QUESTION 3
#todo: IYCF packages defined in spreadsheet, but would like to be able to manually do this in code. waiting on web app implementation

aa = make_kwargs('3a', {'IYCF 1': cov})
bb = make_kwargs('3b', {'IYCF 2': cov})
cc = make_kwargs('3c', {'IYCF 3': cov})

scens = make_scens([base, a, b, c, d, e, aa, bb, cc])

p.run_scens(scens)

p.write_results(filename='stunting_ans.xlsx')

p.remove('scens')

################################
####### WASTING MODEL #########

## QUESTION 2

a = make_kwargs('2a', {'Cash transfers': cov,
                       'Public provision of complementary foods': cov})
scens = make_scens([base, a])
p.run_scens(scens)

## QUESTION 3

a = make_kwargs('3a', {'Treatment of SAM': cov})
# todo: turn on management of mam, waiting on webapp implementation
# b = make

## QUESTION 4
# ToS saturation at $18 mil, so no change
a = make_kwargs('4a', {'Treatment of SAM': 18e6})
b = make_kwargs('4b', {'Treatment of SAM': 19e6})
scens = make_scens([base, a, b])
p.run_scens(scens)

p.write_results(filename='wasting_ans.xlsx')

p.remove('scens')

#####################
### ANAEMIA MODEL ###

## QUESTION 1
a = make_kwargs('1a', {'Micronutrient powders': cov})

# spend same amount on both IFAS, see which is better. ATM both have the same OR but community is cheaper and greater reach, so this is much better
b = make_kwargs('1c', {'IFAS for pregnant women (community)': 1e6}, scentype='budget')
c = make_kwargs('1d', {'IFAS for pregnant women (hospital)': 1e6}, scentype='budget')

scens = make_scens([base, a, b, c])
p.run_scens(scens)

p.write_results(filename='anaemia_ans.xlsx')


# todo: run at saturation for IFAS preg women



# import pylab as pl
# p.plot()
# pl.show()






