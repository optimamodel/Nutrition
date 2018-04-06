import os, sys
root = '../..'
moduleDir = os.path.join(os.path.dirname(__file__), root)
sys.path.append(moduleDir)
import optimisation3 as optimisation
import play
from csv import writer
from multiprocessing import Process
from datetime import date
import csv
from collections import OrderedDict
import pickle


regions = ['Arusha', 'Dar_es_Salaam', 'Dodoma', 'Kaskazini_Pemba', 'Kaskazini_Unguja', 'Katavi',
           'Kilimanjaro', 'Kusini_Pemba', 'Kusini_Unguja', 'Lindi', 'Manyara', 'Mara', 'Mjini_Magharibi',
           'Morogoro', 'Mtwara', 'Pwani', 'Rukwa', 'Ruvuma', 'Simiyu', 'Singida', 'Tabora', 'Tanga']

objectives = ['healthy_children']
budgetMultiples = [1]

# current + additional US$40 distributed on per-capita basis, all optimised
# need to distribute the funds first, then optimise
additionalFunds = 32833333.
# get total population
popSizes = []
for region in regions:
    filePath = play.getFilePath(root=root, country='Tanzania/regions', name=region)
    model = play.setUpModel(filePath, adjustCoverage=False, numYears=6, calibrate=False)
    thisPop = 0
    for pop in model.populations:
        thisPop += pop.getTotalPopulation()
    popSizes.append(thisPop)
totalPop = sum(popSizes)
dollarPerHead = additionalFunds/totalPop
funding = [pop*dollarPerHead for pop in popSizes]

# get funding distribution
jobs = []
thisDate = date.today().strftime('%Y%b%d')
resultsPath = '{}/Results/Tanzania/geospatial/{}/additionalPerCapita'.format(root, thisDate)
for i, region in enumerate(regions):
    funds = funding[i]
    fileInfo = [root, 'Tanzania/regions', region, '']
    thisOptim = optimisation.Optimisation(objectives, budgetMultiples, fileInfo, additionalFunds=funds, resultsPath=resultsPath)
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
        thisOptim = optimisation.Optimisation(objectives, budgetMultiples, fileInfo, resultsPath='')
        fixedAllocations = thisOptim.fixedAllocations
        fixedAllocationsDict = thisOptim.createDictionary(fixedAllocations)
        fixedAllocations = OrderedDict(sorted(fixedAllocationsDict.items())).values()
        optimisedAdditional = [a - b for a, b in zip(allocations.values(), fixedAllocations)]
        w.writerow([region] + optimisedAdditional)