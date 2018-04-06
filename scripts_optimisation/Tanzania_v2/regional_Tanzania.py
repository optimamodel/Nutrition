# running optimisation for the various scenarios for Tanzania
import os, sys
root = '../..'
moduleDir = os.path.join(os.path.dirname(__file__), root)
sys.path.append(moduleDir)
import optimisation3 as optimisation
import play
from csv import writer
from multiprocessing import Process
from datetime import date

# regions = ['Arusha', 'Dar_es_Salaam', 'Dodoma', 'Kaskazini_Pemba', 'Kaskazini_Unguja', 'Katavi',
#            'Kilimanjaro', 'Kusini_Pemba', 'Kusini_Unguja', 'Lindi', 'Manyara', 'Mara', 'Mjini_Magharibi',
#            'Morogoro', 'Mtwara', 'Pwani', 'Rukwa', 'Ruvuma', 'Simiyu', 'Singida', 'Tabora', 'Tanga']
regions = ['Arusha', 'Dodoma']

objectives = ['healthy_children']
budgetMultiples = [1]


#

# optimised current spending
# no geospatial optimisation necessary
objectives = ['healthy_children']
budgetMultiples = [1]

jobs = []
for region in regions:
    fileInfo = [root, 'Tanzania/regions', region, '']
    thisDate = date.today().strftime('%Y%b%d')
    resultsPath = '{}/Results/Tanzania/geospatial/{}/optimisedCurrent'.format(root, thisDate)
    thisOptim = optimisation.Optimisation(objectives, budgetMultiples, fileInfo, resultsPath=resultsPath)
    prc = Process(target=thisOptim.optimise)
    jobs.append(prc)

optimisation.runJobs(jobs, 50)

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
for i, region in enumerate(regions):
    funds = funding[i]
    fileInfo = [root, 'Tanzania/regions', region, '']
    resultsPath = '{}/Results/Tanzania/geospatial/{}/additionalPerCapita'.format(root, thisDate)
    thisOptim = optimisation.Optimisation(objectives, budgetMultiples, fileInfo, additionalFunds=funds, resultsPath=resultsPath)
    thisOptim.optimise()
    prc = Process(target=thisOptim.optimise)
    jobs.append(prc)

optimisation.runJobs(jobs, 50)









