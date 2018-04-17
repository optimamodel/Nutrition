from csv import writer
from nutrition import play
import os, sys
root = '../..'
moduleDir = os.path.join(os.path.dirname(__file__), root)
sys.path.append(moduleDir)

regions = ['Arusha', 'Dar_es_Salaam', 'Dodoma', 'Kaskazini_Pemba', 'Kaskazini_Unguja', 'Katavi',
           'Kilimanjaro', 'Kusini_Pemba', 'Kusini_Unguja', 'Lindi', 'Manyara', 'Mara', 'Mjini_Magharibi',
           'Morogoro', 'Mtwara', 'Pwani', 'Rukwa', 'Ruvuma', 'Simiyu', 'Singida', 'Tabora', 'Tanga']

#current spending
# can't forget to use the workbook values for IYCF, so that coverage is scaled-up after calibration year
filename = 'outcome_current_spending.csv'
outcomes = ['healthy_children']

with open(filename, 'wb') as f:
    w = writer(f)
    w.writerow(['Regions'] + outcomes)

for region in regions:
    output = []
    filePath = play.getFilePath(root=root, country='Tanzania/regions', name=region)
    model = play.setUpModel(filePath, adjustCoverage=False, numYears=6)  # already run a year
    model.runSimulationFromWorkbook()
    for outcome in outcomes:
        output.append(model.getOutcome(outcome))
    with open(filename, 'a') as f:
        w = writer(f)
        w.writerow([region] + output)