# assumes we have BOCs in a csv format, and only need to run the optimisation component
rootpath = '../../..'

import os, sys

moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)
import optimisation

# read in BOCs
import csv
from scipy.interpolate import pchip
import numpy as np
from itertools import izip

country = 'Tanzania'
date = '2017Sep'
spreadsheetDate = '2017Sep'
haveFixedProgCosts = False

rerunMCSampleSize = 4
geoMCSampleSize = 200
geneticIter = 70
popSize = 70


regionNameList = ['Arusha', 'Dar_es_Salaam', 'Dodoma', 'Geita', 'Iringa', 'Kagera',
                   'Kaskazini_Pemba', 'Kaskazini_Unguja', 'Katavi', 'Kigoma', 'Kilimanjaro',
                   'Kusini_Pemba', 'Kusini_Unguja', 'Lindi', 'Manyara', 'Mara', 'Mbeya',
                   'Mjini_Magharibi', 'Morogoro', 'Mtwara', 'Mwanza', 'Njombe', 'Pwani',
                   'Rukwa', 'Ruvuma', 'Shinyanga', 'Simiyu', 'Singida', 'Tabora', 'Tanga']
# get BOC curve
regionalBOCs = []
for region in regionNameList:
    with open(region+"_regionalBOC.csv", 'rb') as f:
        regionalSpending = []
        regionalOutcome = []
        reader = csv.reader(f)
        for row in reader:
            regionalSpending.append(row[0])
            regionalOutcome.append(row[1])
    # remove named cells
    regionalSpending = np.array(regionalSpending[1:])
    regionalOutcome = np.array(regionalOutcome[1:])
    regionalBOCs.append(pchip(regionalSpending, regionalOutcome))

# get data
spreadsheetFileStem = rootpath + '/input_spreadsheets/' + country + '/' + spreadsheetDate + '/regions/InputForCode_'
spreadsheetList = []
for regionName in regionNameList:
    spreadsheet = spreadsheetFileStem + regionName + '.xlsx'
    spreadsheetList.append(spreadsheet)

for optimise in ['thrive']:
    print 'running GA for:  ', optimise

    resultsFileStem = rootpath + '/Results/' + date + '/' + optimise + '/noConstraints/'+'newOptimisation/'
    GAFile = 'GA_progNotFixed'

    geospatialOptimisation = optimisation.GeospatialOptimisation(spreadsheetList, regionNameList, 'dummynumsteps',
                                                                 'dummycascade', optimise, resultsFileStem, 'dummycostcurve')
    optimisedRegionalBudgetList, outcome = geospatialOptimisation.getOptimisedRegionalBudgetListGivenBOCs(geoMCSampleSize, regionalBOCs, geneticIter, popSize)
    with open('newRegionalAllocations' + str(geoMCSampleSize) +'MC_' + str(geneticIter) + 'Gen_' + str(popSize)+'pop'+'.csv', 'wb') as f:
        writer = csv.writer(f)
        writer.writerows(izip(regionNameList, optimisedRegionalBudgetList))
        writer.writerow(['total ' + optimise, outcome])