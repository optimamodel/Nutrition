rootpath = '../../..'
import os, sys

moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)
import optimisation

country = 'Tanzania'
date = '2017Sep'
spreadsheetDate = '2017Sep'

optimise = 'thrive'
haveFixedProgCosts = False
nCores = 360 #(12*30 - not actually using all these)

costCurveType = 'standard'
numModelSteps = 180
MCSampleSize = 4
cascadeValues = [15.0, 20.0, 50.0, 100.0, 200.0, 400.0, 600.0] #[0.0, 0.1, 0.2, 0.4, 0.8, 1.0, 1.1, 1.25, 1.5, 1.7, 2.0, 3., 4., 5., 6., 8., 10., 'extreme']
splitCascade = False


regionNameList = ['Arusha', 'Dar_es_Salaam', 'Dodoma', 'Geita', 'Iringa', 'Kagera',
                 'Kaskazini_Pemba', 'Kaskazini_Unguja', 'Katavi', 'Kigoma', 'Kilimanjaro',
                 'Kusini_Pemba', 'Kusini_Unguja', 'Lindi', 'Manyara', 'Mara', 'Mbeya',
                 'Mjini_Magharibi', 'Morogoro', 'Mtwara', 'Mwanza', 'Njombe', 'Pwani',
                 'Rukwa', 'Ruvuma', 'Shinyanga', 'Simiyu', 'Singida', 'Tabora', 'Tanga']

spreadsheetFileStem = rootpath + '/input_spreadsheets/' + country + '/' + spreadsheetDate + '/regions/'
spreadsheetList = []
for regionName in regionNameList:
    spreadsheet = spreadsheetFileStem + '/InputForCode_' + regionName + '.xlsx'
    spreadsheetList.append(spreadsheet)

resultsFileStem = rootpath + '/Results/' + date + '/' + optimise + '/geospatialProgNotFixed/'

geospatialOptimisation = optimisation.GeospatialOptimisation(spreadsheetList, regionNameList, numModelSteps,
                                                             cascadeValues, optimise, resultsFileStem, costCurveType)
geospatialOptimisation.generateParallelResultsForGeospatialCascades(nCores, MCSampleSize, haveFixedProgCosts, splitCascade)