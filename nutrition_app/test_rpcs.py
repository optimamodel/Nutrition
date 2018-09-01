"""
Version:
"""

import sciris as sc
import nutrition.ui as nu
from nutrition_app import rpcs, apptasks as apt

runall = False

torun = [
'optim_io',
#'run_optimization',
]

T = sc.tic()

def heading(string):
    sc.colorize('blue', string)
    return None

if 'optim_io' in torun or runall:
    proj = nu.demo(optims=True)
    optim_summaries = rpcs.get_optim_info(proj, online=False)
    rpcs.set_optim_info(proj, optim_summaries, online=False)
    R = proj.run_optim(maxtime=5, parallel=False)
    heading('Optimization summaries:')
    print(optim_summaries)
    heading('Results:')
    print(R)


if 'run_optimization' in torun or runall:
    maxtime = 10
    proj = nu.demo(optims=True)
    output = apt.run_optim(proj, online=False)
    print('Output:')
    print(output)


sc.toc(T)
print('Done.')