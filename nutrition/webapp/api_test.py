"""
Version:
"""

import sciris.core as sc
import nutrition.ui as nu

sc.tic()

# Create blank and demo projects
P = nu.Project(name='Blank')
D = nu.demo()


sc.toc()
print('Done.')