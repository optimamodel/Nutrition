rootpath = '../../..'

import os, sys

moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)
import optimisation
from multiprocessing import Process
import pandas

country = 'Tanzania'
date = '2017Sep'
spreadsheetDate = '2017Sep'
haveFixedProgCosts = False  # programs are not fixed, adding extra money automatically fixes regional spending and distributes the extra

rerunMCSampleSize = 4
numModelSteps = 180
cascadeValues = [0.0, 0.1, 0.2, 0.4, 0.8, 1.0, 1.1, 1.25, 1.5, 1.7, 2.0, 3., 4., 5., 6., 8., 10., 15.0, 20.0, 50.0, 100.0]
costCurveType = 'standard'
regionNameList = ['Arusha', 'Dar_es_Salaam', 'Dodoma', 'Geita', 'Iringa', 'Kagera',
                  'Kaskazini_Pemba', 'Kaskazini_Unguja', 'Katavi', 'Kigoma', 'Kilimanjaro',
                  'Kusini_Pemba', 'Kusini_Unguja', 'Lindi', 'Manyara', 'Mara', 'Mbeya',
                  'Mjini_Magharibi', 'Morogoro', 'Mtwara', 'Mwanza', 'Njombe', 'Pwani',
                  'Rukwa', 'Ruvuma', 'Shinyanga', 'Simiyu', 'Singida', 'Tabora', 'Tanga']

spreadsheetFileStem = rootpath + '/input_spreadsheets/' + country + '/' + spreadsheetDate + '/regions/InputForCode_'
spreadsheetList = []
spreadsheet2List = []
for regionName in regionNameList:
    spreadsheet = spreadsheetFileStem + regionName + '.xlsx'
    spreadsheet2 = spreadsheetFileStem + regionName + '_IYCF.xlsx'
    spreadsheetList.append(spreadsheet)
    spreadsheet2List.append(spreadsheet2)
    
Location = 'IYCF_coverage.xlsx'
df = pandas.read_excel(Location, sheetname = 'Sheet1')
IYCF_cov_regional = list(df['Coverage'])

numCores = 30  # need this number times the number of outcomes you're optimising for
extraMoney = 20000000 #45695801
for optimise in ['thrive', 'deaths']:
    print 'running GA for:  ', optimise
    resultsFileStem = rootpath + '/Results/' + date + '/' + optimise + '/geospatialProgNotFixedIYCF/'
    BOCsFileStem = resultsFileStem + 'regionalBOCs/'
    GAFile = 'GA_progNotFixed_extra20m'
    geospatialOptimisation = optimisation.GeospatialOptimisation(spreadsheetList, regionNameList, numModelSteps,
                                                                 cascadeValues, optimise, resultsFileStem, costCurveType, BOCsFileStem, IYCF_cov_regional)
    # parallel for each optimise                                                             
    prc = Process(target=geospatialOptimisation.performParallelGeospatialOptimisationExtraMoney, args=(rerunMCSampleSize, GAFile, numCores, extraMoney, haveFixedProgCosts, IYCF_cov_regional, spreadsheet2List))
    prc.start()                                                                 
                              
    #geospatialOptimisation.performParallelGeospatialOptimisationExtraMoney(geoMCSampleSize, rerunMCSampleSize, GAFile, numCores, extraMoney, haveFixedProgCosts)
