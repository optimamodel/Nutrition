import os, sys
root = '../..'
moduleDir = os.path.join(os.path.dirname(__file__), root)
sys.path.append(moduleDir)
import optimisation3 as optimisation
from multiprocessing import Process
from datetime import date
import csv
import pickle
from collections import OrderedDict

regions = ['Arusha', 'Dar_es_Salaam', 'Dodoma', 'Kaskazini_Pemba', 'Kaskazini_Unguja', 'Katavi',
           'Kilimanjaro', 'Kusini_Pemba', 'Kusini_Unguja', 'Lindi', 'Manyara', 'Mara', 'Mjini_Magharibi',
           'Morogoro', 'Mtwara', 'Pwani', 'Rukwa', 'Ruvuma', 'Simiyu', 'Singida', 'Tabora', 'Tanga']

objectives = ['healthy_children']
budgetMultiples = [1]

# optimised current spending
# no geospatial optimisation necessary
objectives = ['healthy_children']
budgetMultiples = [1]

jobs = []
thisDate = date.today().strftime('%Y%b%d')
resultsPath = '{}/Results/Tanzania/geospatial/{}/optimisedCurrent'.format(root, thisDate)
for region in regions:
    fileInfo = [root, 'Tanzania/regions', region, '']
    thisOptim = optimisation.Optimisation(objectives, budgetMultiples, fileInfo, resultsPath=resultsPath,
                                          filterProgs=False, numYears=6)
    prc = Process(target=thisOptim.optimise)
    jobs.append(prc)
optimisation.runJobs(jobs, 50)

# collate results
filename = '{}/allocations_{}.csv'.format(resultsPath, objectives[0])
sortedProgs = sorted([prog.name for prog in thisOptim.programs])
with open(filename, 'wb') as f:
    w = csv.writer(f)
    w.writerow(['Region'] + sortedProgs)
    pass

with open(filename, 'a') as f:
    w = csv.writer(f)
    for region in regions:
        targetFile = '{}/{}_{}_{}.pkl'.format(resultsPath, region, objectives[0], 1)
        infile = open(targetFile, 'rb')
        thisAllocation = pickle.load(infile)
        infile.close()
        allocations = OrderedDict(sorted(thisAllocation.items()))
        # remove fixed allocations
        fileInfo = [root, 'Tanzania/regions', region, '']
        thisOptim = optimisation.Optimisation(objectives, budgetMultiples, fileInfo, resultsPath='',
                                              numYears=6)
        fixedAllocations = thisOptim.fixedAllocations
        fixedAllocationsDict = thisOptim.createDictionary(fixedAllocations)
        fixedAllocations = OrderedDict(sorted(fixedAllocationsDict.items())).values()
        optimisedAdditional = [a - b for a, b in zip(allocations.values(), fixedAllocations)]
        w.writerow([region] + optimisedAdditional)












