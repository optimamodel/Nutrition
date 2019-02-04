import sciris as sc
from nutrition import ui as nu

# Create a new project.

# Do load the default spreadsheet.

# Do a "null" save of the spreadsheet.

# Try another load of the spreadsheet (where it should crash).

fn = nu.ONpath('inputs')+'demo_national_input.xlsx'
# fn2 = 'writetest2.xlsx'

fn = 'exceltest2.xlsx'
fn2 = 'writetest2.xlsx'

S = sc.Spreadsheet(fn)

# sheet = 'Baseline year population inputs'
# cells = ['C19', 'C20']
# vals = [0.7, ('=1-frac_rice-frac_wheat-frac_maize',0.1)]
sheet = 'Sheet1'
cells = ['A3','B3']
vals = ['dummystr',('=B2*2',8)]

S.writecells(sheetname=sheet, cells=cells, vals=vals, wbargs={'data_only': False})
S.save(fn2)

# P = nu.Project(inputspath=fn2)
S = sc.Spreadsheet(fn2)
print(S.pandas().parse())

print('Done.')