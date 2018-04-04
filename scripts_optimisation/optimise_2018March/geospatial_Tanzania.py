import os, sys
root = '../..'
moduleDir = os.path.join(os.path.dirname(__file__), root)
sys.path.append(moduleDir)
import optimisation3 as optimisation

# regions = ['Arusha', 'Dar_es_Salaam', 'Dodoma', 'Kaskazini_Pemba', 'Kaskazini_Unguja', 'Katavi',
#            'Kilimanjaro', 'Kusini_Pemba', 'Kusini_Unguja', 'Lindi', 'Manyara', 'Mara', 'Mjini_Magharibi',
#            'Morogoro', 'Mtwara', 'Pwani', 'Rukwa', 'Ruvuma', 'Simiyu', 'Singida', 'Tabora', 'Tanga']
regions = ['Arusha']

objectives = ['healthy_children'] # individual programs don't have much impact, so can't filter progs
fileInfo = [root, 'Tanzania']

if __name__ == '__main__':
    thisOptimisation = optimisation.GeospatialOptimisation(objectives, fileInfo, regions, numYears=6)
    thisOptimisation.optimiseScenarios()