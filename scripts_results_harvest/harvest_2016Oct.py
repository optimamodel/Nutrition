# -*- coding: utf-8 -*-
"""
Created on Mon Oct 31 14:18:57 2016

@author: ruth
"""
import os, sys
rootpath = '..'
moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)
import optimisation

country = 'Bangladesh'
date = '2016Oct'
 
numModelSteps = 180

# NATIONAL
dataSpreadsheetName = rootpath+'/input_spreadsheets/'+country+'/'+date+'/InputForCode_'+country+'.xlsx'
outcomeOfInterestList = ['deaths', 'stunting', 'DALYs']
cascadeValues = [0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 4.0]  
analysis = 'noConstraints'
optimise = 'stunting'
resultsFileStem = rootpath+'/Results/'+date+'/'+optimise+'/national/'+analysis+'/'+country
# stunting: bar graph, all 3 time series when optimising for stunting
thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem)
thisOptimisation.outputCurrentSpendingToCSV() 
thisOptimisation.outputTimeSeriesToCSV('DALYs')
thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem) #this repitition is necessary
thisOptimisation.outputTimeSeriesToCSV('deaths')
thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem) #this repitition is necessary
thisOptimisation.outputTimeSeriesToCSV('stunting')
# all 3 outcomes for stunting cascade
thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem) # this one might not be
for outcomeOfInterest in outcomeOfInterestList:
    thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem)
    thisOptimisation.outputCascadeAndOutcomeToCSV(cascadeValues, outcomeOfInterest)
    
# cascades for deaths and DALYs
optimise = 'deaths'
resultsFileStem = rootpath+'/Results/'+date+'/'+optimise+'/national/'+analysis+'/'+country
thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem)
thisOptimisation.outputCascadeAndOutcomeToCSV(cascadeValues, 'deaths') 
thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem)
thisOptimisation.outputCascadeAndOutcomeToCSV(cascadeValues, 'stunting') 
optimise = 'DALYs'
resultsFileStem = rootpath+'/Results/'+date+'/'+optimise+'/national/'+analysis+'/'+country
thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem)
thisOptimisation.outputCascadeAndOutcomeToCSV(cascadeValues, 'DALYs')    
    

# GEOSPATIAL
optimise = 'stunting'
regionNameList = ['Barisal', 'Chittagong', 'Dhaka', 'Khulna', 'Rajshahi', 'Rangpur', 'Sylhet']
spreadsheetFileStem = rootpath+'/input_spreadsheets/'+country+'/'+date+'/subregionSpreadsheets/'
spreadsheetList = []
for regionName in regionNameList:
    spreadsheet = spreadsheetFileStem + regionName + '.xlsx'
    spreadsheetList.append(spreadsheet)


# GEOSPATIAL EXTRA MONEY
extraMoney = 10000000
cascadeValuesExtra = [1.0, 1.1, 1.25, 1.5, 1.7, 2.0, 'extreme']
analysis = 'fixedCosts'
# stunting extra money: bar graph/region, trade off curves, cascade and outcomes    
GAFileExtra = 'GA_fixedProg_extra_'+str(extraMoney)   
resultsFileStem = rootpath+'/Results/'+date+'/'+optimise+'/geospatial/'+analysis+'/'
geospatialOptimisation = optimisation.GeospatialOptimisation(spreadsheetList, regionNameList, numModelSteps, cascadeValuesExtra, optimise, resultsFileStem)
geospatialOptimisation.outputRegionalCurrentSpendingToCSV()
geospatialOptimisation.outputRegionalPostGAOptimisedSpendingToCSV(GAFileExtra)
geospatialOptimisation.outputTradeOffCurves()
geospatialOptimisation.outputRegionalCascadesAndOutcomeToCSV('stunting')
geospatialOptimisation.outputRegionalTimeSeriesToCSV('stunting')
geospatialOptimisation.plotTimeSeriesPostGAReallocationByRegion(GAFileExtra)
geospatialOptimisation.outputToCSVTimeSeriesPostGAReallocationByRegion(GAFileExtra)