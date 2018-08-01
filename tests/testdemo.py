"""
Version:
"""

import nutrition.ui as nu

do_plot   = True
run_scen  = False
run_optim = False

P = nu.demo()

if run_scen:
    P.run_scens()
    if do_plot:
        P.plot()

if run_optim:
    P.run_optims(keys=[P.optim().name], parallel=False)
    if do_plot:
        P.plot(-1, optim=True)