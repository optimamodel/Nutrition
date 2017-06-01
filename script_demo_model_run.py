# -*- coding: utf-8 -*-
"""
Created on Wed May 31 15:32:25 2017

This demo is for version 1.0 Optima Nutrition.  It demonstrates:  
how to run the baseline model
how to run the model with different coverages 
how to access outcomes
how to translate a cost into a coverage

@author: ruth
"""
import data
from copy import deepcopy as dcp
import helper
helper = helper.Helper()

numModelSteps = 180 # this is 12 months times 15 years
spreadsheet = 'input_spreadsheets/Bangladesh/2016Oct/InputForCode_Bangladesh.xlsx'
spreadsheetData = data.readSpreadsheet(spreadsheet, helper.keyList)

# make a model
model, derived, params = helper.setupModelConstantsParameters(spreadsheetData)

# make a list to save a version of the model at each time step
modelList = []  
# run the model for one year before updating coverages  
timestepsPre = 12
for t in range(timestepsPre):
    model.moveOneTimeStep()  
    modelThisTimeStep = dcp(model)
    modelList.append(modelThisTimeStep)
    
# change the coverages of some interventions   
newCoverages = {}    
newCoverages['Vitamin A supplementation'] = 0.5
newCoverages['Breastfeeding promotion'] = 0.85

# update coverages after 1 year     
model.updateCoverages(newCoverages)

# run the model for the remaining timesteps
for t in range(numModelSteps - timestepsPre):
    model.moveOneTimeStep()
    modelThisTimeStep = dcp(model)
    modelList.append(modelThisTimeStep)
    
# index to final version of the model (final time step in the list)
stepFinal = numModelSteps-1    
    
# get outcomes
cumulativeAgingOutStunted = modelList[stepFinal].getOutcome('stunting')
finalStuntingPrevalence = modelList[stepFinal].getOutcome('stunting prev')
cumulativeDeaths = modelList[stepFinal].getOutcome('deaths')
cumulativeThriving = modelList[stepFinal].getOutcome('thrive')

print 'cumulative number of people thriving with updated coverages is:'
print cumulativeThriving

# compare this to the baseline
model, derived, params = helper.setupModelConstantsParameters(spreadsheetData)
modelList = []  
for t in range(numModelSteps):
    model.moveOneTimeStep()  
    modelThisTimeStep = dcp(model)
    modelList.append(modelThisTimeStep)
cumulativeThriving = modelList[stepFinal].getOutcome('thrive')
print 'cumulative number of people thriving baseline is:'    
print cumulativeThriving


"""
DIFFERENT OPTIONS FOR NEW COVERAGES:

1.  SET ALL COVERAGES TO BE MAXIMIUM

newCoverages = {}    
for i in range(0, len(spreadsheetData.interventionList)):
    intervention = spreadsheetData.interventionList[i]
    newCoverages[intervention] = 1
    
    
2. SPECIFY A COST AND TRANSLATE IT INTO COVERAGE

# import some things we need
import optimisation
import costcov

# make a costcov object to help us later
costCov = costcov.Costcov()

# make an optimisation object to help us later (it contains some useful functions)
thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, 'dummy', 'dummy')

# get the cost coverage information relevant to this spreadsheet
costCoverageInfo = thisOptimisation.getCostCoverageInfo()

# make some objects to help us get target popsize for new coverage of interventions
model, derived, params = helper.setupModelConstantsParameters(spreadsheetData)

# run the model for 1 year
for t in range(timestepsPre):
    model.moveOneTimeStep()    

# want target popsize after 1 year (this is when we add interventions)
targetPopSize = optimisation.getTargetPopSizeFromModelInstance(spreadsheet, helper.keyList, model) 

# intervention name that we want to know the new coverage for
intervention = 'Breastfeeding promotion'

# how much we want to spend on intervention
spending = 2000000

# use a function in the costcov object to translate this spending into a coverage
newCoverages[intervention] = costCov.function(spending, costCoverageInfo[intervention], targetPopSize[intervention]) / targetPopSize[intervention]

# print out the coverage that this spending translates to
print newCoverages[intervention]
    
"""



