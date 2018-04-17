import os, sys
from nutrition import optimisation

root = os.pardir
moduleDir = os.path.join(os.path.dirname(__file__), root)
sys.path.append(moduleDir)

regions = ['Arusha', 'Dar_es_Salaam', 'Dodoma', 'Kaskazini_Pemba', 'Kaskazini_Unguja', 'Katavi',
           'Kilimanjaro', 'Kusini_Pemba', 'Kusini_Unguja', 'Lindi', 'Manyara', 'Mara', 'Mjini_Magharibi',
           'Morogoro', 'Mtwara', 'Pwani', 'Rukwa', 'Ruvuma', 'Simiyu', 'Singida', 'Tabora', 'Tanga']

objectives = ['healthy_children']

if __name__ == '__main__':
    thisOptimisation = optimisation.GeospatialOptimisation(objectives, root, regions, numYears=6)
    thisOptimisation.optimiseScenarios()