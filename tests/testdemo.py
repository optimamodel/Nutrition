"""
Version:
"""

import nutrition.ui as nu

do_plot = True
run_scen = False
run_optim = False
run_geo = True

P = nu.demo(scens=run_scen, optims=run_optim, geos=run_geo)

if run_scen:
    P.run_scens()
    if do_plot:
        P.plot()

if run_optim:
    P.run_optim(parallel=True)
    if do_plot:
        P.plot(-1, optim=True)

if run_geo:
    P.run_geo(parallel=True)
    if do_plot:
        P.plot(-1, geo=True)
