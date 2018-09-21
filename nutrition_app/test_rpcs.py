"""
Version:
"""

import sciris as sc
import scirisweb as sw
import nutrition.ui as nu
from nutrition_app import main, rpcs, apptasks as apt

runall = False

torun = [
#'file_tests'
#'datastore', # WARNING, doesn't work
#'spreadsheet_io',
#'input_io',
'scen_io',
#'optim_io',
#'run_scenarios',
#'run_optimization',
#'export_results',
]



###########################################################################
### Definitions
###########################################################################

def demoproj(proj_id, username):
    P = nu.demo(scens=True, optims=True)
    P.name = 'RPCs test %s' % proj_id[:6]
    P.uid = proj_id
    P = rpcs.cache_results(P)
    rpcs.save_new_project(P, username)
    return P

def heading(string, style=None):
    divider = '='*60
    sc.blank()
    if style == 'big': string = '\n'.join([divider, string, divider])
    sc.colorize('blue', string)
    return None


T = sc.tic()
app = main.make_app()
user = sw.make_default_users(app)[0] # WARNING, broken!
proj_id  = sc.uuid(as_string=True) # These can all be the same
proj = demoproj(proj_id, user.username)


###########################################################################
### Run the tests
###########################################################################

string = 'Starting tests for proj = %s' % proj_id
heading(string, 'big')

if 'file_tests' in torun or runall:
    filename = 'file_tests.prj'
    heading('Running file_tests', 'big')
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


if 'datastore' in torun or runall:
    ds = sw.flaskapp.datastore

if 'spreadsheet_io' in torun or runall:
    heading('Running spreadsheet_io', 'big')
    filename = 'nutrition_test.xlsx'
    proj.input_sheet.openpyxl(data_only=True).save(filename)
    proj.dataset().load(filename, project=proj)


if 'input_io' in torun or runall:
    heading('Running input_io', 'big')
    sheetjson = rpcs.get_sheet_data(proj.uid)
    rpcs.save_sheet_data(proj.uid, sheetdata=sheetjson['tables'])
    sc.pp(sheetjson)


if 'scen_io' in torun or runall:
    heading('Running scen_io', 'big')
    dorun = True
    scen_summaries = rpcs.get_scen_info(proj.uid)
    rpcs.set_scen_info(proj.uid, scen_summaries)
    if dorun:
        R = proj.run_scens()
        heading('Results:')
        print(R)
    heading('Scenario summaries:')
    sc.pp(scen_summaries)


if 'optim_io' in torun or runall:
    heading('Running optim_io', 'big')
    dorun = True
    optim_summaries = rpcs.get_optim_info(proj.uid)
    rpcs.set_optim_info(proj.uid, optim_summaries)
    if dorun:
        R = proj.run_optim(maxtime=5, parallel=False)
        heading('Results:')
        print(R)
    heading('Optimization summaries:')
    sc.pp(optim_summaries)
    

if 'run_scenarios' in torun or runall:
    heading('Running run_scenarios', 'big')
    doplot = False
    output = rpcs.run_scens(proj.uid, doplot=doplot)
    sc.pp(output)


if 'run_optimization' in torun or runall:
    heading('Running run_optimization', 'big')
    doplot = True
    maxtime = 10
    proj = apt.run_optim(proj.uid, 'placeholder_ID')
    if doplot:
        output = rpcs.plot_optimization(proj.uid, proj.results.keys()[-1])
        print('Output:')
        sc.pp(output)


if 'export_results' in torun or runall:
    heading('Running export_results', 'big')
    proj.run_scens()
    fn1 = rpcs.export_results(proj.uid)
    fn2 = rpcs.export_graphs(proj.uid)
    print('Output files:')
    print(fn1)
    print(fn2)
    

sc.toc(T)
print('Done.')