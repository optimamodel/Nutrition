rootpath = '../..'
import os, sys

moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)
import optimisation

country = 'Tanzania'
date = '2017Sep'
spreadsheetDate = '2017Sep'

optimise = 'thrive'
haveFixedProgCosts = False
nCores = 96 #(8*12)

costCurveType = 'standard'
numModelSteps = 180
MCSampleSize = 4
cascadeValues = [0.0, 0.1, 0.2, 0.4, 0.8, 1.0, 1.1, 1.25, 1.5, 1.7, 2.0, 'extreme']

regionNameList = ['Arusha', 'Dar_es_Salaam', 'Dodoma', 'Geita', 'Iringa', 'Kagera', 'Kaskazini_Pemba', 'Kaskazini_Unguja']
#regionNameList = ['Katavi', 'Kigoma', 'Kilimanjaro', 'Kusini_Pemba', 'Kusini_Unguja', 'Lindi', 'Manyara', 'Mara']
#regionNameList = ['Mbeya', 'Mjini_Magharibi', 'Morogoro', 'Mtwara', 'Mwanza', 'Njombe', 'Pwani']
#regionNameList = ['Rukwa', 'Ruvuma', 'Shinyanga', 'Simiyu', 'Singida', 'Tabora', 'Tanga']

spreadsheetFileStem = rootpath + '/input_spreadsheets/' + country + '/' + spreadsheetDate + '/regions/'
spreadsheetList = []
for regionName in regionNameList:
    spreadsheet = spreadsheetFileStem + '/InputForCode_' + regionName + '.xlsx'
    spreadsheetList.append(spreadsheet)

resultsFileStem = rootpath + '/Results/' + date + '/' + optimise + '/geospatialProgNotFixed/'

geospatialOptimisation = optimisation.GeospatialOptimisation(spreadsheetList, regionNameList, numModelSteps,
                                                             cascadeValues, optimise, resultsFileStem, costCurveType)
geospatialOptimisation.generateParallelResultsForGeospatialCascades(nCores, MCSampleSize, haveFixedProgCosts)