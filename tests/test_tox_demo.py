import nutrition.ui as nu
nu.logger.setLevel(0)


testdir = nu.ONpath/'tests'
tempdir = testdir/'temp'


P = nu.Project('eg')
P.load_data(inputspath='demo_input_en_fr.xlsx')  # Reset the project name to a new project name that is unique.

proj1 = nu.demo(scens=True, optims=True, geos=True)
proj2 = nu.demo(scens=True, optims=True, geos=True, locale='fr')
#
# P2 = sc.loadobj('testobj')

proj2.load_data(inputspath='demo_input_en_fr.xlsx')  # Reset the project name to a new project name that is unique.



"""
Version:
"""

import nutrition.ui as nu

do_plot   = True
run_scen  = False
run_optim = False
run_geo   = True

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