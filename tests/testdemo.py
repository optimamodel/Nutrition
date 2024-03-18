"""
Version:
"""

import nutrition.ui as nu

do_plot = True
run_scen = True
run_optim = False
run_geo = True

P = nu.demo(scens=run_scen, optims=run_optim, geos=run_geo)

if run_scen:
    P.run_scens(n_samples=5)
    if do_plot:
        P.plot()

if run_optim:
    P.run_optim(parallel=False, n_samples=5)
    if do_plot:
        P.plot(-1, optim=True)

if run_geo:
    P.run_geo(parallel=False)
    if do_plot:
        P.plot(-1, geo=True)
