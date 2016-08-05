# -*- coding: utf-8 -*-
"""
Created on Fri Aug  5 15:15:58 2016

@author: ruth
"""
import optimisation
optimise = 'DALYs'
numModelSteps = 180
MCSampleSize = 25
stem = 'resultsHarvest2016Aug05'

# NATIONAL
dataSpreadsheetName = '../input_spreadsheets/Bangladesh/2016Aug02/InputForCode_Bangladesh.xlsx'
resultsFileStem = '../Results2016Aug02/'+optimise+'/national/Bangladesh'
cascadeValues = [0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 4.0]  

thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem)
thisOptimisation.plotReallocation()
thisOptimisation.plotTimeSeries()


# GEOSPATIAL 
cascadeValues = [0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 'extreme'] 
regionNameList = ['Barisal', 'Chittagong', 'Dhaka', 'Khulna', 'Rajshahi', 'Rangpur', 'Sylhet']
spreadsheetFileStem = '../input_spreadsheets/Bangladesh/2016Aug02/subregionSpreadsheets/'
spreadsheetList = []
for regionName in regionNameList:
    spreadsheet = spreadsheetFileStem + regionName + '.xlsx'
    spreadsheetList.append(spreadsheet)
    
resultsFileStem = '../Results2016Aug02/'+optimise+'/geospatial/'

geospatialOptimisation = optimisation.GeospatialOptimisation(spreadsheetList, regionNameList, numModelSteps, cascadeValues, optimise, resultsFileStem)
geospatialOptimisation.outputRegionalBOCsFile(stem+'_regionalBOCS_'+optimise+'.pkl')
geospatialOptimisation.outputTradeOffCurves(stem+'_tradeOffCurves_'+optimise+'.pkl')
geospatialOptimisation.plotRegionalBOCs()
geospatialOptimisation.plotTradeOffCurves()
#geospatialOptimisation.plotReallocationByRegion()
geospatialOptimisation.plotPostGAReallocationByRegion()
geospatialOptimisation.plotTimeSeriesPostGAReallocationByRegion()