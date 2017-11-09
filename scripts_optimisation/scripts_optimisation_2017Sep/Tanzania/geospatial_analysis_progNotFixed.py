rootpath = '../../..'

import os, sys

moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)
import optimisation
from multiprocessing import Process

country = 'Tanzania'
date = '2017Sep'
spreadsheetDate = '2017Sep'
haveFixedProgCosts = False

rerunMCSampleSize = 4
# WARNING: these must match values used in the other geospatial scripts
numModelSteps = 180
cascadeValues = [0.0, 0.1, 0.2, 0.4, 0.8, 1.0, 1.1, 1.25, 1.5, 1.7, 2.0, 3., 4., 5., 6., 8., 10., 15.0, 20.0, 50.0, 100.0, 200.0, 400.0, 600.0, 'extreme']
costCurveType = 'standard'
regionNameList = ['Arusha', 'Dar_es_Salaam', 'Dodoma', 'Geita', 'Iringa', 'Kagera',
                  'Kaskazini_Pemba', 'Kaskazini_Unguja', 'Katavi', 'Kigoma', 'Kilimanjaro',
                  'Kusini_Pemba', 'Kusini_Unguja', 'Lindi', 'Manyara', 'Mara', 'Mbeya',
                  'Mjini_Magharibi', 'Morogoro', 'Mtwara', 'Mwanza', 'Njombe', 'Pwani',
                  'Rukwa', 'Ruvuma', 'Shinyanga', 'Simiyu', 'Singida', 'Tabora', 'Tanga']

spreadsheetFileStem = rootpath + '/input_spreadsheets/' + country + '/' + spreadsheetDate + '/regions/InputForCode_'
spreadsheetList = []
for regionName in regionNameList:
    spreadsheet = spreadsheetFileStem + regionName + '.xlsx'
    spreadsheetList.append(spreadsheet)

numCores = 30  # need this number times the number of outcomes you're optimising for
for optimise in ['thrive', 'deaths']:
    print 'running GA for:  ', optimise

    resultsFileStem = rootpath + '/Results/' + date + '/' + optimise + '/geospatialProgNotFixed/'
    BOCsFileStem = resultsFileStem + 'regionalBOCs/'
    GAFile = 'GA_progNotFixed'

    geospatialOptimisation = optimisation.GeospatialOptimisation(spreadsheetList, regionNameList, numModelSteps,
                                                                 cascadeValues, optimise, resultsFileStem, costCurveType, BOCsFileStem)
    # parallel for each optimise                                                             
    prc = Process(target=geospatialOptimisation.performParallelGeospatialOptimisation, args=(rerunMCSampleSize, GAFile, numCores, haveFixedProgCosts))
    prc.start()                                                                 
                                                                 
#    geospatialOptimisation.performParallelGeospatialOptimisation(geoMCSampleSize, rerunMCSampleSize, GAFile,
#                                                                           numCores, haveFixedProgCosts)