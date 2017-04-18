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
date = '2017Apr'
spreadsheetDate = '2016Oct'
 
numModelSteps = 180

# NATIONAL
dataSpreadsheetName = rootpath+'/input_spreadsheets/'+country+'/'+spreadsheetDate+'/InputForCode_'+country+'.xlsx'
outcomeOfInterestList = ['stunting','stunting prev', 'thrive']
cascadeValues = [0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 4.0]  


optimise = 'thrive'
resultsFileStem = rootpath+'/Results/'+date+'/'+optimise+'/national/'+country
# all 3 time series when optimising for thrive
thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem)
thisOptimisation.outputCurrentSpendingToCSV() 
thisOptimisation.outputTimeSeriesToCSV('thrive')
thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem) #this repitition is necessary
thisOptimisation.outputTimeSeriesToCSV('stunting prev')
thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem) #this repitition is necessary
thisOptimisation.outputTimeSeriesToCSV('stunting')
# all 3 outcomes for thrive cascade
thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem) # this one might not be
for outcomeOfInterest in outcomeOfInterestList:
    thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem)
    thisOptimisation.outputCascadeAndOutcomeToCSV(cascadeValues, outcomeOfInterest)
    
## cascades for deaths and DALYs
#optimise = 'deaths'
#resultsFileStem = rootpath+'/Results/'+date+'/'+optimise+'/national/'+country
#thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem)
#thisOptimisation.outputCascadeAndOutcomeToCSV(cascadeValues, 'deaths') 
#thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem)
#thisOptimisation.outputCascadeAndOutcomeToCSV(cascadeValues, 'stunting') 
#optimise = 'DALYs'
#resultsFileStem = rootpath+'/Results/'+date+'/'+optimise+'/national/'+country
#thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem)
#thisOptimisation.outputCascadeAndOutcomeToCSV(cascadeValues, 'DALYs')    
    

