"""
Version:
"""

import sciris.core as sc
import nutrition.ui as nu
import os

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



#%% Optimizations



sc.toc()
print('Done.')