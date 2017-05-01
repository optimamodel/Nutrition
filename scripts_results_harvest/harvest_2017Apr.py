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
outcomeOfInterestList = ['thrive', 'deaths']
cascadeValues = [0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 4.0]  


optimise = 'thrive'
resultsFileStem = rootpath+'/Results/'+date+'/'+optimise+'/national/'+country
# both time series when optimising for thrive
thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem)
thisOptimisation.outputCurrentSpendingToCSV() 
thisOptimisation.outputTimeSeriesToCSV('thrive')
thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem) #this repitition is necessary
thisOptimisation.outputTimeSeriesToCSV('deaths')
# both outcomes for thrive cascade
thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem) # this one might not be
for outcomeOfInterest in outcomeOfInterestList:
    thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem)
    thisOptimisation.outputCascadeAndOutcomeToCSV(cascadeValues, outcomeOfInterest)
    
    
# getting coverage info
import pickle    
import data 
import costcov
costCov = costcov.Costcov()
thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem)
spreadsheetData = data.readSpreadsheet(dataSpreadsheetName, thisOptimisation.helper.keyList)

# at 50% budget
# read the optimal budget allocations from file
filename = '%s_cascade_%s_0.5.pkl'%(resultsFileStem, optimise)
infile = open(filename, 'rb')
allocation = pickle.load(infile)
infile.close()
# run the model with this allocation
modelList = thisOptimisation.oneModelRunWithOutput(allocation)
# get cost coverage and target pop to translate cost to coverage
costCoverageInfo = thisOptimisation.getCostCoverageInfo()
# target pop size when interventions are added comes after 12 timesteps 
targetPopSize = optimisation.getTargetPopSizeFromModelInstance(dataSpreadsheetName, thisOptimisation.helper.keyList, modelList[11])
# get coverages
coverages1 = {}
for i in range(0, len(spreadsheetData.interventionList)):
    intervention = spreadsheetData.interventionList[i]
    coverages1[intervention] = costCov.function(allocation[intervention], costCoverageInfo[intervention], targetPopSize[intervention]) / targetPopSize[intervention]

# at 150% budget
filename = '%s_cascade_%s_1.5.pkl'%(resultsFileStem, optimise)
infile = open(filename, 'rb')
allocation = pickle.load(infile)
infile.close()
modelList = thisOptimisation.oneModelRunWithOutput(allocation)
costCoverageInfo = thisOptimisation.getCostCoverageInfo()
targetPopSize = optimisation.getTargetPopSizeFromModelInstance(dataSpreadsheetName, thisOptimisation.helper.keyList, modelList[11])
coverages2 = {}
for i in range(0, len(spreadsheetData.interventionList)):
    intervention = spreadsheetData.interventionList[i]
    coverages2[intervention] = costCov.function(allocation[intervention], costCoverageInfo[intervention], targetPopSize[intervention]) / targetPopSize[intervention]
