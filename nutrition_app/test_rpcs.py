"""
Version:
"""

import sciris as sc
import scirisweb as sw
import nutrition.ui as nu
from nutrition_app import main, rpcs, apptasks as apt

torun = [
'file_tests'
'sanitization',
'datastore',
'spreadsheet_io',
'input_io',
'scen_io',
'optim_io',
'run_scenarios',
'run_optimization',
'export_results',
]


###########################################################################
### Definitions
###########################################################################

def demoproj(proj_id, username):
    P = nu.demo(scens=True, optims=True)
    P.name = 'RPCs test %s' % proj_id[:6]
    P.uid = sc.uuid(proj_id)
    P = rpcs.cache_results(P)
    rpcs.save_new_project(P, username, uid=P.uid) # Force a matching uid
    return P

def heading(string, style=None):
    divider = '='*60
    sc.blank()
    if style == 'big': string = '\n'.join([divider, string, divider])
    sc.colorize('blue', string)
    return None

# Launch app
T = sc.tic()
app = main.make_app()
user = sw.make_default_users(app)[0]
proj_id  = sc.uuid(tostring=True) # These can all be the same
proj = demoproj(proj_id, user.username)


###########################################################################
### Run the tests
###########################################################################

string = 'Starting tests for proj = %s' % proj_id
heading(string, 'big')

if 'file_tests' in torun:
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


if 'sanitization' in torun:
    heading('Running sanitization', 'big')
    testentries = [None, '', 3, '3', '3%', '$3', '$3,000.00', '$3.000,00', [23,23], ['24','24'], '[25,25]']
    inputstrings = []
    outputstrings = []
    for entry in testentries:
        try:                   sanitized = repr(rpcs.sanitize(entry))
        except Exception as E: sanitized = repr(E)
        inputstrings.append('%s' % repr(entry))
        outputstrings.append('%s' % sanitized)
    inlen = 0
    outlen = 0
    for  instr in  inputstrings:  inlen = max( inlen, len( instr))
    for outstr in outputstrings: outlen = max(outlen, len(outstr))
    outlen = min(outlen,20)
    inctrl  = '%' + ('%i' % inlen)  + 's'
    outctrl = '%' + ('%i' % outlen) + 's'
    ctrlstring = '  Original: { ' + inctrl + ' } --> Sanitized: { ' + outctrl + ' }'
    for instr,outstr in zip(inputstrings,outputstrings):
        print(ctrlstring % (instr, outstr))
    

if 'datastore' in torun:
    heading('Running datastore', 'big')
    ds = rpcs.find_datastore()


if 'spreadsheet_io' in torun:
    heading('Running spreadsheet_io', 'big')
    filename = 'nutrition_test.xlsx'
    proj.input_sheet.openpyxl(data_only=True).save(filename)
    proj.dataset().load(filename, project=proj)


if 'input_io' in torun:
    heading('Running input_io', 'big')
    sheetjson = rpcs.get_sheet_data(proj.uid)
    rpcs.save_sheet_data(proj.uid, sheetdata=sheetjson['tables'])
    sc.pp(sheetjson)


if 'scen_io' in torun:
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


if 'optim_io' in torun:
    heading('Running optim_io', 'big')
    dorun = True
    optim_summaries = rpcs.get_optim_info(proj.uid)
    rpcs.set_optim_info(proj.uid, optim_summaries)
    if dorun: # Do not use Celery, do not pass go
        R = proj.run_optim(maxtime=5, parallel=False)
        heading('Results:')
        print(R)
    heading('Optimization summaries:')
    sc.pp(optim_summaries)
    

if 'run_scenarios' in torun:
    heading('Running run_scenarios', 'big')
    doplot = False
    output = rpcs.run_scens(proj.uid, doplot=doplot)
    sc.pp(output)


if 'run_optimization' in torun:
    heading('Running run_optimization', 'big')
    doplot = True
    proj_id = apt.run_optim(proj.uid, 'placeholder_ID', runtype='test')
    if doplot:
        output = rpcs.plot_optimization(proj_id, proj.results.keys()[-1])
        print('Output:')
        sc.pp(output)


if 'export_results' in torun:
    heading('Running export_results', 'big')
    proj.run_scens()
    fn1 = rpcs.export_results(proj.uid)
    fn2 = rpcs.export_graphs(proj.uid)
    print('Output files:')
    print(fn1)
    print(fn2)
    

sc.toc(T)
print('Done.')