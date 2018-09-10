"""
Version:
"""

import sciris as sc
import nutrition.ui as nu
from nutrition_app import rpcs, apptasks as apt

runall = False

torun = [
#'file_tests'
#'spreadsheet_io',
#'input_io',
#'scen_io',
#'optim_io',
#'run_scenarios',
#'run_optimization',
'export_results',
]

T = sc.tic()

def heading(string, style=None):
    divider = '#'*60
    sc.blank()
    if style == 'big': string = '\n'.join([divider, string, divider])
    sc.colorize('blue', string)
    return None


if 'file_tests' in torun or runall:
    filename = 'file_tests.prj'
    heading('Running file_tests', 'big')
    
    proj = nu.demo(scens=True)
    print('Project size before running scenarios:')
    sc.checkmem(proj, descend=True)
    sc.checkmem(proj, descend=False)
    proj.run_scens()
    print('Project size after running scenarios:')
    sc.checkmem(proj, descend=True)
    sc.checkmem(proj, descend=False)
    startsave = sc.tic()
    proj.save(filename)
    savetime = sc.toc(startsave, output=True)
    startload = sc.tic()
    proj2 = sc.loadobj(filename)
    loadtime = sc.toc(startload, output=True)
    print('Time to save: %s s' % savetime)
    print('Time to load: %s s' % loadtime)


if 'spreadsheet_io' in torun or runall:
    heading('Running spreadsheet_io', 'big')
    filename = 'nutrition_test.xlsx'
    proj = nu.demo()
    proj.input_sheet.openpyxl(data_only=True).save(filename)
    proj.dataset().load(filename, project=proj)


if 'input_io' in torun or runall:
    heading('Running input_io', 'big')
    proj = nu.demo()
    sheetjson = rpcs.get_sheet_data(proj, online=False)
    rpcs.save_sheet_data(proj, sheetdata=sheetjson['tables'], online=False)
    sc.pp(sheetjson)


if 'scen_io' in torun or runall:
    heading('Running scen_io', 'big')
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
    heading('Running optim_io', 'big')
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
    

if 'run_scenarios' in torun or runall:
    heading('Running run_scenarios', 'big')
    doplot = False
    proj = nu.demo(scens=True)
    output = rpcs.run_scens(proj, online=False, doplot=doplot)
    sc.pp(output)


if 'run_optimization' in torun or runall:
    heading('Running run_optimization', 'big')
    doplot = True
    maxtime = 10
    proj = nu.demo(optims=True)
    proj = apt.run_optim(proj, 'placeholder_ID', online=False)
    if doplot:
        output = rpcs.plot_optimization(proj, proj.results.keys()[-1], online=False)
        print('Output:')
        sc.pp(output)


if 'export_results' in torun or runall:
    heading('Running export_results', 'big')
    proj = nu.demo(scens=True)
    proj.run_scens()
    fn1 = rpcs.export_results(proj, online=False)
    fn2 = rpcs.export_graphs(proj, online=False)
    print('Output files:')
    print(fn1)
    print(fn2)
    

sc.toc(T)
print('Done.')