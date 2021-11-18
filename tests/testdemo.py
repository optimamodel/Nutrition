"""
Version:
"""

import nutrition.ui as nu

do_plot = True
run_scen = True
run_optim = True
run_geo = False

P = nu.demo(scens=run_scen, optims=run_optim, geos=run_geo)

if run_scen:
    P.run_scens()
    if do_plot:
        P.plot()

if run_optim:
    P.run_optim(parallel=False)
    if do_plot:
        P.plot(-1, optim=True)

if run_geo:
    P.run_geo(parallel=False)
    if do_plot:
        P.plot(-1, geo=True)
