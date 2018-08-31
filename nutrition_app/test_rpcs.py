"""
Version:
"""

import sciris as sc
import nutrition.ui as nu
from nutrition_app import rpcs, apptasks as apt


torun = [
 'run_optimization',
]

T = sc.tic()

proj = None

if 'run_optimization' in torun:
    maxtime = 10
    if proj is None: proj = nu.demo(optims=True)
    output = apt.run_optim(proj, online=False)
    print('Output:')
    print(output)


sc.toc(T)
print('Done.')