import os, sys

rootpath = '..'
moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)
import optimisation

country = 'Bangladesh'
date = '2017Apr'
spreadsheetDate = '2016Oct'

numModelSteps = 180

cascadeValues = [1.0, 1.1, 1.25, 1.5, 1.7, 2.0, 'extreme']

# GEOSPATIAL
optimise = 'thrive'
regionNameList = ['Barisal', 'Chittagong', 'Dhaka', 'Khulna', 'Rajshahi', 'Rangpur', 'Sylhet']
spreadsheetFileStem = rootpath+'/input_spreadsheets/'+country+'/'+spreadsheetDate+'/subregionSpreadsheets/'
spreadsheetList = []
for regionName in regionNameList:
    spreadsheet = spreadsheetFileStem + regionName + '.xlsx'
    spreadsheetList.append(spreadsheet)


extraMoney = 0
analysis = 'geospatialNotFixed'
# stunting extra money: bar graph/region, trade off curves, cascade and outcomes
GAFile = 'GA_notFixedProg_extra_'+str(extraMoney)
resultsFileStem = rootpath+'/Results/'+date+'/'+optimise +'/'+analysis+'/'

geospatialOptimisation = optimisation.GeospatialOptimisation(spreadsheetList, regionNameList, numModelSteps, cascadeValues, optimise, resultsFileStem)
geospatialOptimisation.outputRegionalCurrentSpendingToCSV()
geospatialOptimisation.outputRegionalPostGAOptimisedSpendingToCSV(GAFile)
geospatialOptimisation.outputTradeOffCurves()
geospatialOptimisation.outputToCSVTimeSeriesPostGAReallocationByRegion(GAFile)

