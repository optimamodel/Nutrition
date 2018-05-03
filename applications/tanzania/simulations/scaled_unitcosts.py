import os, sys
from nutrition import optimisation
from csv import writer

root = os.pardir
moduleDir = os.path.join(os.path.dirname(__file__), root)
sys.path.append(moduleDir)

regions = ['Arusha', 'Dar_es_Salaam', 'Dodoma', 'Kaskazini_Pemba', 'Kaskazini_Unguja', 'Katavi',
           'Kilimanjaro', 'Kusini_Pemba', 'Kusini_Unguja', 'Lindi', 'Manyara', 'Mara', 'Mjini_Magharibi',
           'Morogoro', 'Mtwara', 'Pwani', 'Rukwa', 'Ruvuma', 'Simiyu', 'Singida', 'Tabora', 'Tanga']


with open('scaled_unit_costs.csv', 'wb') as f:
    w = writer(f)
    w.writerow(['Region', 'Scale Factor'])
    for region in regions:
        fileInfo = [root, 'Tanzania/regions', region, '']
        thisRegion = optimisation.Optimisation([], [], fileInfo)
        scaleFactor = thisRegion.scaleFactor
        w.writerow([region, scaleFactor])




