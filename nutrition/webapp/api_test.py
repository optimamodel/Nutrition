"""
Version:
"""

import sciris.core as sc
import nutrition.ui as nu
import os
from numpy import nan

sc.tic()

#%% Projects

# Create a blank projects
filename = 'temp_nutrition_project.prj'
P = nu.Project(name='Blank')
P.save(filename=filename)
os.remove(filename)

# Create a demo project
D = nu.demo()

#%% Scenarios
json = sc.odict()
json['name'] = 'API test'
json['t'] = [2017,2025]
json['prog_set'] = ['Cash transfers', 'IFA fortification of maize', 'IFAS for pregnant women (community)', 'IPTp', 'IYCF 1', 'Micronutrient powders', 'Treatment of SAM', 'Vitamin A supplementation', 'Zinc for treatment + ORS']
json['scen_type'] = 'coverage'
json['scen'] = {'Vitamin A supplementation': [nan, 0.94999999999999996, nan, nan, nan, nan, nan, nan, nan], 'IYCF 1': [nan, 0.94999999999999996, nan, nan, nan, nan, nan, nan, nan], 'IPTp': [nan, nan, nan, nan, nan, nan, nan, nan, nan], 'IFA fortification of maize': [nan, nan, nan, nan, nan, nan, nan, nan, nan], 'Zinc for treatment + ORS': [nan, nan, nan, nan, nan, nan, nan, nan, nan], 'IFAS for pregnant women (community)': [nan, 0.94999999999999996, nan, nan, nan, nan, nan, nan, nan], 'Treatment of SAM': [nan, 0.94999999999999996, nan, nan, nan, nan, nan, nan, nan], 'Micronutrient powders': [nan, nan, nan, nan, nan, nan, nan, nan, nan], 'Cash transfers': [nan, nan, nan, nan, nan, nan, nan, nan, nan]}
D.add_scen(json=json)
D.run_scens()
figs = D.result().plot()


#%% Optimizations



sc.toc()
print('Done.')