##########################
### Contains the exercises for Nutrition training workshops ###

import nutrition.ui as nu
from nutrition.scenarios import make_scens
from nutrition.optimization import Optim
from nutrition.settings import Settings
from nutrition.utils import default_trackers
import sciris.core as sc
import numpy as np

ss = Settings()

results = sc.odict()

#### OPTIONS
cov = [0.95]
filler = [np.nan, np.nan]
modelname = "Demo"
scentype = "coverage"

## Create project

p = nu.Project(modelname)

# load a dataset
p.load_data("demo", "demo", name=modelname)
data = p.dataset()


def make_kwargs(name, progvals, modelname="Demo", scentype="coverage"):
    kwargs = {"name": name, "model_name": modelname, "scen_type": scentype, "progvals": progvals}
    return kwargs


def make_kwargs_opt(name, progset, weights, mults, modelname="Demo", fixcurr=False, addfunds=0.0):
    kwargs = {"name": name, "model_name": modelname, "weights": weights, "mults": mults, "prog_set": progset, "fix_curr": fixcurr, "add_funds": addfunds}
    return kwargs


##### MODEL COMPONENT EXERCISES #####
outcomes = default_trackers()

###########################
#### MODULE 2: Stunting model ######

## QUESTION 1
base = make_kwargs("Baseline", {})

## QUESTION 2

a = make_kwargs("2.2a", {"Public provision of complementary foods": cov})
b = make_kwargs("2.2b", {"Lipid-based nutrition supplements": cov})
c = make_kwargs("2.2c", {"Zinc supplementation": cov})
d = make_kwargs("2.2d", {"Public provision of complementary foods": cov, "Zinc supplementation": cov})

## QUESTION 3

mydata = sc.dcp(data)
mydata.name = "IYCF"
for age in ss.child_ages:
    mydata.prog_data.prog_target["IYCF 1"][age] = 0.37
    mydata.prog_data.prog_target["IYCF 2"][age] = 0
    mydata.prog_data.prog_target["IYCF 3"][age] = 1
for age in ss.pw_ages + ss.wra_ages:
    mydata.prog_data.prog_target["IYCF 1"][age] = 0
    mydata.prog_data.prog_target["IYCF 3"][age] = 1
    if "PW" in age:
        mydata.prog_data.prog_target["IYCF 2"][age] = 1

p.add_data(mydata)

aa = make_kwargs("2.3a", {"IYCF 1": cov}, modelname="IYCF")
bb = make_kwargs("2.3b", {"IYCF 2": cov}, modelname="IYCF")
cc = make_kwargs("2.3c", {"IYCF 3": cov}, modelname="IYCF")

## QUESTION 4

mydata = sc.dcp(data)
mydata.name = "PPCF at 50%"
# change baseline
mydata.prog_data.base_cov["Public provision of complementary foods"] = 0.5
p.add_data(mydata)

aaa = make_kwargs("2.4a", {"Public provision of complementary foods": cov}, modelname="PPCF at 50%")
scens = make_scens([base, a, b, c, d, aa, bb, cc, aaa])
p.add_scens(scens)

################################
####### MODULE 3: WASTING MODEL #########

## QUESTION 2

a = make_kwargs("3.2a", {"Cash transfers": cov, "Public provision of complementary foods": cov})
scens = make_scens([base, a])
p.add_scens(scens)

## QUESTION 3

a = make_kwargs("3.3a", {"Treatment of SAM": cov})

## QUESTION 4
# ToS saturation at $18 mil, so no change
a = make_kwargs("3.4a", {"Treatment of SAM": 18e6}, scentype="budget")
b = make_kwargs("3.4b", {"Treatment of SAM": 19e6}, scentype="budget")
scens = make_scens([base, a, b])
p.add_scens(scens)

#####################
### MODULE 4: ANAEMIA MODEL ###

## QUESTION 1
a = make_kwargs("4.1a", {"Micronutrient powders": filler + cov})

# spend same amount on both IFAS, see which is better. ATM both have the same OR but community is cheaper and greater reach, so this is much better
b = make_kwargs("4.1c", {"IFAS for pregnant women (community)": 4e6}, scentype="budget")
c = make_kwargs("4.1d", {"IFAS for pregnant women (health facility)": 4e6}, scentype="budget")

## QUESTION 2

# first test exclusion dependency then threshold dependency
aa = make_kwargs("4.2a", {"IFAS for pregnant women (community)": cov})
bb = make_kwargs("4.2b", {"Multiple micronutrient supplementation": cov})
cc = make_kwargs("4.2c", {"IFAS for pregnant women (community)": cov, "Multiple micronutrient supplementation": cov})
dd = make_kwargs("4.2d", {"IPTp": cov, "Multiple micronutrient supplementation": cov})
ee = make_kwargs("4.2e", {"IPTp": [0], "Multiple micronutrient supplementation": cov})

scens = make_scens([base, a, b, c, aa, bb, cc, dd, ee])
p.add_scens(scens)

#####################
# MODULE 5: NUTRION-SENSITIVE INTERVENTIONS ##

# QUESTION 1
a = make_kwargs("5.1a", {"Family planning": cov})

## QUESTION 2
a = make_kwargs("5.2a", {"Vitamin A supplementation": filler + cov})
b = make_kwargs("5.2b", {"Zinc supplementation": filler + cov})

scens = make_scens([base, a])
p.add_scens(scens)

p.run_scens(scens)
p.write_results("solutions.xlsx")


######################
# MODULE 9: OPTIMIZATION II
#
# mydata = sc.dcp(data)
# for age in ss.child_ages:
#     mydata.prog_data.prog_target['IYCF 1'][age] = 1
# p.add_data(mydata)
#
# ## QUESTION 1
#
# progset = ['IYCF 1', 'Lipid-based nutrition supplements',
#            'Multiple micronutrient supplementation', 'Micronutrient powders',
#            'Public provision of complementary foods', 'Treatment of SAM',
#            'Vitamin A supplementation', 'Zinc supplementation']
# objs = ['child_anaemprev']
# names = ['9.1c']
# mults = [1]
# optimres = []
# for i, obj in enumerate(objs):
#     kwarg = make_kwargs_opt(names[i], progset, obj, mults)
#     optim = Optim(**kwarg)
#     p.run_optim(optim=optim)
#     p.write_results('solutions2.xlsx')

## QUESTION 2

# obj = 'healthy_children'
# for obj in objs:
#     kwargs = make_kwargs_opt(obj, progset, obj, mults, fixcurr=True, addfunds=10e6)
#     optim = Optim(**kwargs)
#     p.run_optim(optim=optim, swarmsize=1, maxtime=1, maxiter=1)
#
# p.write_results('solutions3.xlsx')
