"""
Version:
"""

import sciris as sc
import scirisweb as sw
import nutrition.ui as nu
from nutrition_app import main, rpcs, apptasks as apt
from flask_login import login_user

runall = False

torun = [
#'file_tests'
'datastore', # WARNING, doesn't work
#'spreadsheet_io',
#'input_io',
#'scen_io',
#'optim_io',
#'run_scenarios',
#'run_optimization',
#'export_results',
]



###########################################################################
### Definitions
###########################################################################

def demoproj(proj_id):
    P = nu.demo(scens=True, optims=True)
    P.name = 'RPCs test %s' % proj_id[:6]
    P.uid = proj_id
    P = rpcs.cache_results(P)
    rpcs.save_new_project(P)
    return P

def heading(string, style=None):
    divider = '='*60
    sc.blank()
    if style == 'big': string = '\n'.join([divider, string, divider])
    sc.colorize('blue', string)
    return None


T = sc.tic()
app = main.make_app()
#user = sw.make_default_users(app)[0] # WARNING, broken!
#login_user(user)
proj_id  = sc.uuid(as_string=True) # These can all be the same
proj = demoproj(proj_id)


###########################################################################
### Run the tests
###########################################################################

string = 'Starting tests for proj = %s' % proj_id
heading(string, 'big')

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


if 'datastore' in torun or runall:
    ds = sw.flaskapp.datastore

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