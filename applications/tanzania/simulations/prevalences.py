import os, sys
from nutrition import play
from csv import writer

root = os.pardir
moduleDir = os.path.join(os.path.dirname(__file__), root)
sys.path.append(moduleDir)

regions = ['Arusha', 'Dar_es_Salaam', 'Dodoma', 'Kaskazini_Pemba', 'Kaskazini_Unguja', 'Katavi',
           'Kilimanjaro', 'Kusini_Pemba', 'Kusini_Unguja', 'Lindi', 'Manyara', 'Mara', 'Mjini_Magharibi',
           'Morogoro', 'Mtwara', 'Pwani', 'Rukwa', 'Ruvuma', 'Simiyu', 'Singida', 'Tabora', 'Tanga']

outcomes = ['wasting_prev', 'anaemia_prev_children', 'anaemia_prev_PW', 'anaemia_prev_WRA']

with open('prevalences.csv', 'wb') as f:
    w = writer(f)
    w.writerow(['Region'] + outcomes)
    for region in regions:
        filePath = play.getFilePath(root, 'regional', region)
        model = play.setUpModel(filePath)
        row = [region]
        for outcome in outcomes:
            row.append(model.getOutcome(outcome))
        w.writerow(row)



