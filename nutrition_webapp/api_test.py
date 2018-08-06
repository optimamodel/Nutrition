"""
Version:
"""

import os
from numpy import nan
import sciris.core as sc
import nutrition.ui as nu



#%% Setup
sc.tic()
doplot     = 1
run_scens  = 1
run_optims = 1


#%% Projects

# Create a blank projects
filename = 'temp_nutrition_project.prj'
P = nu.Project(name='Blank')
P.save(filename=filename)
os.remove(filename)

# Create a demo project
D = nu.demo()

#%% Scenarios
if run_scens:
    D.scens.clear() # Reset the odict
    
    json = sc.odict()
    json['name'] = 'API test 1'
    json['scen_type'] = 'coverage' # ['coverage', 'budget']
    json['active'] = True
    json['prog_set'] = ['Cash transfers', 'IFA fortification of maize', 'IFAS for pregnant women (community)', 'IPTp', 'IYCF 1', 'Micronutrient powders', 'Treatment of SAM', 'Vitamin A supplementation', 'Zinc for treatment + ORS']
    json['vals'] = sc.odict({'Vitamin A supplementation': [nan, 0.94999999999999996, nan, nan, nan, nan, nan, nan, nan], 'IYCF 1': [nan, 0.94999999999999996, nan, nan, nan, nan, nan, nan, nan], 'IPTp': [nan, nan, nan, nan, nan, nan, nan, nan, nan], 'IFA fortification of maize': [nan, nan, nan, nan, nan, nan, nan, nan, nan], 'Zinc for treatment + ORS': [nan, nan, nan, nan, nan, nan, nan, nan, nan], 'IFAS for pregnant women (community)': [nan, 0.94999999999999996, nan, nan, nan, nan, nan, nan, nan], 'Treatment of SAM': [nan, 0.94999999999999996, nan, nan, nan, nan, nan, nan, nan], 'Micronutrient powders': [nan, nan, nan, nan, nan, nan, nan, nan, nan], 'Cash transfers': [nan, nan, nan, nan, nan, nan, nan, nan, nan]})
    D.add_scen(json=json)
    
    json2 = sc.dcp(json)
    json2['name'] = 'API test 2'
    json2['vals'] = sc.odict({'Vitamin A supplementation': [nan, nan, nan, nan, nan, nan, nan, nan, nan], 'IYCF 1': [nan, nan, nan, nan, nan, nan, nan, nan, nan], 'IPTp': [nan, nan, nan, nan, nan, nan, nan, nan, nan], 'IFA fortification of maize': [nan, nan, nan, nan, nan, nan, nan, nan, nan], 'Zinc for treatment + ORS': [nan, nan, nan, nan, nan, nan, nan, nan, nan], 'IFAS for pregnant women (community)': [nan, nan, nan, nan, nan, nan, nan, nan, nan], 'Treatment of SAM': [nan, nan, nan, nan, nan, nan, nan, nan, nan], 'Micronutrient powders': [nan, nan, nan, nan, nan, nan, nan, nan, nan], 'Cash transfers': [nan, nan, nan, nan, nan, nan, nan, nan, nan]})
    D.add_scen(json=json2)
    
    D.run_scens()
    if doplot:
        figs = D.plot(toplot=['prevs', 'outputs'])


#%% Optimizations
if run_optims:
    D.optims.clear() # Reset the odict
    
    json = sc.odict()
    json['name'] = 'Optimization test 1'
    json['prog_set'] = D.dataset().prog_names() # ['Cash transfers', 'IFA fortification of maize', 'IFAS for pregnant women (community)', 'IPTp', 'IYCF 1', 'Micronutrient powders', 'Treatment of SAM', 'Vitamin A supplementation', 'Zinc for treatment + ORS']
    json['mults'] = [1]
    json['add_funds'] = 10e6
    json['obj'] = 'thrive' # ['thrive', 'child_deaths', 'stunting_prev', 'wasting_prev', 'anaemia_prev']
    D.add_optim(json=json)
    
    D.run_optims(parallel=False)
    if doplot:
        figs = D.plot(toplot=['alloc'])


sc.toc()
print('Done.')