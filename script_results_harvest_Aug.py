# -*- coding: utf-8 -*-
"""
Created on Fri Aug  5 15:15:58 2016

@author: ruth
"""
import optimisation
optimiseList = ['deaths', 'stunting'] #['DALYs'] #, 'deaths', 'stunting']
numModelSteps = 180
MCSampleSize = 25

# NATIONAL
dataSpreadsheetName = 'input_spreadsheets/Bangladesh/2016Aug02/InputForCode_Bangladesh.xlsx'
cascadeValues = [0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 4.0]  
# DALYs: bar graph, all 3 time series when optimising for DALYs
optimise = 'DALYs'
resultsFileStem = 'Results2016Aug10/'+optimise+'/national/Bangladesh'
thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem)
thisOptimisation.outputCurrentSpendingToCSV() 
thisOptimisation.outputTimeSeriesToCSV('DALYs')
thisOptimisation.outputTimeSeriesToCSV('deaths')
thisOptimisation.outputTimeSeriesToCSV('stunting')
# all 3 cascades and outcomes
for optimise in optimiseList:
    resultsFileStem = 'Results2016Aug10/'+optimise+'/national/Bangladesh'
    thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem)
    thisOptimisation.outputCascadeAndOutcomeToCSV(cascadeValues, optimise)


# GEOSPATIAL
optimise = 'DALYs'
regionNameList = ['Barisal', 'Chittagong', 'Dhaka', 'Khulna', 'Rajshahi', 'Rangpur', 'Sylhet']
spreadsheetFileStem = 'input_spreadsheets/Bangladesh/2016Aug02/subregionSpreadsheets/'
spreadsheetList = []
for regionName in regionNameList:
    spreadsheet = spreadsheetFileStem + regionName + '.xlsx'
    spreadsheetList.append(spreadsheet)


# GEOSPATIAL WITHOUT EXTRA MONEY
# DALYs: bar graph/region, trade off curves, cascade and outcomes for DALYs    
cascadeValues = [0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 'extreme']  
GAFile = 'GA'  
resultsFileStem = 'Results2016Aug10/'+optimise+'/geospatial/'
geospatialOptimisation = optimisation.GeospatialOptimisation(spreadsheetList, regionNameList, numModelSteps, cascadeValues, optimise, resultsFileStem)
geospatialOptimisation.outputRegionalCurrentSpendingToCSV()
geospatialOptimisation.outputRegionalPostGAOptimisedSpendingToCSV(GAFile)
geospatialOptimisation.outputTradeOffCurves()
geospatialOptimisation.outputRegionalCascadesAndOutcomeToCSV('DALYs')


# GEOSPATIAL EXTRA MONEY
extraMoney = 10000000
cascadeValuesExtra = [1.0, 1.20, 1.50, 1.80, 2.0, 3.0, 'extreme']
# DALYs extra money: bar graph/region, trade off curves, cascade and outcomes for DALYs    
GAFileExtra = 'GA_fixedProg_extra_'+str(extraMoney)   
resultsFileStem = 'Results2016Aug10fixedProgCosts/'+optimise+'/geospatial/'
geospatialOptimisation = optimisation.GeospatialOptimisation(spreadsheetList, regionNameList, numModelSteps, cascadeValuesExtra, optimise, resultsFileStem)
geospatialOptimisation.outputRegionalCurrentSpendingToCSV()
geospatialOptimisation.outputRegionalPostGAOptimisedSpendingToCSV(GAFileExtra)
geospatialOptimisation.outputTradeOffCurves()
geospatialOptimisation.outputRegionalCascadesAndOutcomeToCSV('DALYs')










