"""
Version:
"""

import sciris as sc
import nutrition.ui as nu
from nutrition_app import rpcs, apptasks as apt

runall = False

torun = [
#'spreadsheet_io',
'input_io',
#'scen_io',
#'optim_io',
#'run_optimization',
]

T = sc.tic()

def heading(string):
    sc.blank()
    sc.colorize('blue', string)
    return None

if 'spreadsheet_io' in torun or runall:
    filename = 'nutrition_test.xlsx'
    proj = nu.demo()
    proj.dataset().input_sheet.openpyxl().save(filename)
    proj.dataset().load(filename, recalc=True)


if 'input_io' in torun or runall:
    proj = nu.demo()
    sheetjson = rpcs.get_sheet_data(proj, online=False)
    rpcs.save_sheet_data(proj, sheetjson=sheetjson, online=False)
    sc.pp(sheetjson)


if 'scen_io' in torun or runall:
    dorun = True
    proj = nu.demo(scens=True)
    scen_summaries = rpcs.get_scen_info(proj, online=False)
    rpcs.set_scen_info(proj, scen_summaries, online=False)
    if dorun:
        R = proj.run_scens()
        heading('Results:')
        print(R)
    heading('Scenario summaries:')
    sc.pp(scen_summaries)


if 'optim_io' in torun or runall:
    dorun = True
    proj = nu.demo(optims=True)
    optim_summaries = rpcs.get_optim_info(proj, online=False)
    rpcs.set_optim_info(proj, optim_summaries, online=False)
    if dorun:
        R = proj.run_optim(maxtime=5, parallel=False)
        heading('Results:')
        print(R)
    heading('Optimization summaries:')
    sc.pp(optim_summaries)
    

if 'run_optimization' in torun or runall:
    doplot = True
    maxtime = 10
    proj = nu.demo(optims=True)
    proj = apt.run_optim(proj, 'placeholder_ID', online=False)
    if doplot:
        output = rpcs.plot_optimization(proj, proj.results.keys()[-1], online=False)
        print('Output:')
        sc.pp(output)


sc.toc(T)
print('Done.')