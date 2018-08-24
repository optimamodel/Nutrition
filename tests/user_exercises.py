##########################
### Contains the exercises for Nutrition training workshops ###

import nutrition.ui as nu
from nutrition.scenarios import make_scens
from nutrition.optimization import Optim
from nutrition.settings import Settings
from nutrition.utils import default_trackers, pretty_labels
import sciris.core as sc
import pylab as pl

ss = Settings()

results = sc.odict()

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

def make_kwargs_opt(name, progset, obj, mults, modelname='Demo', fixcurr=False, addfunds=0):
    kwargs = {'name': name,
               'model_name': modelname,
               'obj': obj,
               'mults': mults,
               'prog_set': progset,
               'fix_curr': fixcurr,
               'add_funds': addfunds}
    return kwargs

def write_results(filename, results):
    """ results is an odict with all results from each exercise """
    outcomes = default_trackers()
    labs = pretty_labels()
    headers = [['Exercise'] + [labs[out] for out in outcomes]]
    sheetnames = []
    data = []
    allocs = []
    for module, result in results.iteritems():
        sheetnames.append(module)
        outputs = []
        for res in result:
            output = res.get_outputs(outcomes, seq=False)
            outputs.append([res.name] + output)
            # if res.obj is not None: # optimization
            #     for i, prog in enumerate(res.programs):
            #         alloc = prog.annual_spend[1] - res.prog_info.ref_spend[i]
            #         allocs.append([res.name] + alloc)
        data.append(headers + outputs)
    sc.export_xlsx(filename=filename, data=data, sheetnames=sheetnames)
    return

##### MODEL COMPONENT EXERCISES #####
outcomes = default_trackers()

#### baseline scenario ####
#1
base = make_kwargs('Baseline', {})

###########################
#### MODULE 2: Stunting model ######
#
# # QUESTION 2

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

## QUESTION 4
# todo: need functionality to change baseline in web app to do this
# aaa = make_kwargs('4a', {})

scens = make_scens([base, a, b, c, d, e, aa, bb, cc])

p.run_scens(scens)

results['module 2'] = p.get_results()

# p.write_results(filename='stunting_ans.xlsx')

p.remove('scens')

################################
####### MODULE 3: WASTING MODEL #########

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

results['Module 3'] = p.get_results()

# p.write_results(filename='wasting_ans.xlsx')

p.remove('scens')

#####################
### MODULE 4: ANAEMIA MODEL ###

## QUESTION 1
a = make_kwargs('1a', {'Micronutrient powders': cov})

# spend same amount on both IFAS, see which is better. ATM both have the same OR but community is cheaper and greater reach, so this is much better
b = make_kwargs('1c', {'IFAS for pregnant women (community)': 1e6}, scentype='budget')
c = make_kwargs('1d', {'IFAS for pregnant women (hospital)': 1e6}, scentype='budget')

## QUESTION 2

# first test exclusion dependency then threshold dependency
aa = make_kwargs('2a', {'IFAS for pregnant women (community)': cov})
bb = make_kwargs('2b', {'Multiple micronutrient supplementation': cov})
cc = make_kwargs('2c', {'IFAS for pregnant women (community)': cov,
                        'Multiple micronutrient supplementation': cov})
dd = make_kwargs('2d', {'IPTp': cov,
                        'Multiple micronutrient supplementation': cov})
ee = make_kwargs('2e', {'IPTp': [0],
                        'Multiple micronutrient supplementation': cov})

## QUESTION 3
aaa = make_kwargs('3a', {'Vitamin A supplementation': cov})
bbb = make_kwargs('3b', {'Zinc supplementation': cov})


scens = make_scens([base,a,b,c,aa,bb,cc,dd,ee, aaa, bbb])
p.run_scens(scens)

results['Module 4'] = p.get_results()

# p.write_results(filename='anaemia_ans.xlsx')

p.remove('scens')
#
#####################
# MODULE 5: FP & WASH ##

# QUESTION 1
a = make_kwargs('1a', {'Family planning': cov})

scens = make_scens([base, a])
p.run_scens(scens)

results['Module 5'] = p.get_results()


######################
# MODULE 9: OPTIMIZATION II
# todo: actually want to return allocation, not outcomes
# args
progset = ['Family planning', 'IFAS (community)', 'IFAS (hospital)', 'IYCF 1', 'Lipid-based nutrition supplements',
           'Multiple micronutrient supplementation', 'Micronutrient powders',
           'Public provision of complementary foods', 'Treatment of SAM',
           'Vitamin A supplementation', 'Zinc supplementation']
objs = default_trackers()
names = ['1a', '1b', '1c', '1d', '1e', '1f', '1g']
mults = [1]
optimres = []
for obj in objs:
    kwarg = make_kwargs_opt(obj, progset, obj, mults)
    optim = [Optim(**kwarg)]
    p.run_optims(optims=optim, swarmsize=1, maxtime=1, maxiter=1)
    optimres += p.get_results(obj)
    p.plot(optim=True)

# 2a
progset += ['WASH: Handwashing', 'WASH: Piped water']

obj = 'child_anaemprev'
kwargs = make_kwargs_opt(obj, progset, obj, mults)
optim = [Optim(**kwargs)]
p.run_optims(optims=optim, swarmsize=1, maxtime=1, maxiter=1)
optimres += p.get_results(obj)

results['module 9'] = optimres




write_results('solutions.xlsx', results)




######






