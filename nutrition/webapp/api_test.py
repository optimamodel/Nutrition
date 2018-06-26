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
json['prog_set'] = [u'Cash transfers', u'IFA fortification of maize', u'IFAS for pregnant women (community)', u'IPTp', u'IYCF 1', u'Micronutrient powders', u'Treatment of SAM', u'Vitamin A supplementation', u'Zinc for treatment + ORS']
json['scen_type'] = 'coverage'
json['scen'] = {u'Vitamin A supplementation': [nan, 0.94999999999999996, nan, nan, nan, nan, nan, nan, nan], u'IYCF 1': [nan, 0.94999999999999996, nan, nan, nan, nan, nan, nan, nan], u'IPTp': [nan, nan, nan, nan, nan, nan, nan, nan, nan], u'IFA fortification of maize': [nan, nan, nan, nan, nan, nan, nan, nan, nan], u'Zinc for treatment + ORS': [nan, nan, nan, nan, nan, nan, nan, nan, nan], u'IFAS for pregnant women (community)': [nan, 0.94999999999999996, nan, nan, nan, nan, nan, nan, nan], u'Treatment of SAM': [nan, 0.94999999999999996, nan, nan, nan, nan, nan, nan, nan], u'Micronutrient powders': [nan, nan, nan, nan, nan, nan, nan, nan, nan], u'Cash transfers': [nan, nan, nan, nan, nan, nan, nan, nan, nan]}
D.add_scen(json=json)
D.run_scens()


#%% Optimizations



sc.toc()
print('Done.')