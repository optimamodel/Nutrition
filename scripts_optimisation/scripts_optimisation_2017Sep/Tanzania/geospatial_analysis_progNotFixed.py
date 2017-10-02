rootpath = '../..'

import os, sys

moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)
import optimisation

country = 'Tanzania'
date = '2017Sep'
spreadsheetDate = '2017Sep'

haveFixedProgCosts = False

rerunMCSampleSize = 25
geoMCSampleSize = 25
# WARNING: these must match values used in the other geospatial scripts
numModelSteps = 180
cascadeValues = [0.0, 0.1, 0.2, 0.4, 0.8, 1.0, 1.1, 1.25, 1.5, 1.7, 2.0, 'extreme']
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

numCores = 8  # need this number times the number of outcomes you're optimising for
for optimise in ['thrive']:
    print 'running GA for:  ', optimise

    resultsFileStem = rootpath + '/Results/' + date + '/' + optimise + '/geospatialProgNotFixed/'
    GAFile = 'GA_progNotFixed'

    geospatialOptimisation = optimisation.GeospatialOptimisation(spreadsheetList, regionNameList, numModelSteps,
                                                                 cascadeValues, optimise, resultsFileStem, costCurveType)
    geospatialOptimisation.performParallelGeospatialOptimisation(geoMCSampleSize, rerunMCSampleSize, GAFile,
                                                                           numCores, haveFixedProgCosts)