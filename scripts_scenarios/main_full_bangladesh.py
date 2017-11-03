# -*- coding: utf-8 -*-
"""
Created in Nov 2016

@author: madhurakilledar

AIM: compare cases of stunting in three scenarios
1. baseline
2. full package (all intervention scaled up to 80%)
3. CFE scaled up to 80% (others remain at current coverage)

INPUT:
REQUIRED FILES
input spreadsheet - see dataFilename

VARIABLES
country
startYear
date
dataFilename
numsteps
delay
fracScaleup

OUTPUT:
verbose output only
stating number of cases of stunting (cumulative after age 5)
and cases of stunting averted relative to baseline (scenario #1)

"""
from __future__ import division
from copy import deepcopy as dcp
from numpy import array

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(moduleDir)
import data
import helper
import output
import costcov

helper = helper.Helper()
costCov = costcov.Costcov()

country = 'Bangladesh'
startYear = 2016
date = '2016Oct'

dataFilename = '../input_spreadsheets/%s/%s/InputForCode_%s.xlsx'%(country, date, country)
#division = 'Sylhet'
#dataFilename = '../input_spreadsheets/%s/%s/subregionSpreadsheets/%s.xlsx'%(country, date, division)
print "\n Input: %s"%dataFilename
inputData = data.readSpreadsheet(dataFilename, helper.keyList)
numAgeGroups = len(helper.keyList['ages'])
print "U5 Population  = %i"%(inputData.demographics['population U5'])
print "Fraction in lower WQ = %g"%(inputData.demographics['fraction poor'])
print "Frac food insecure (lower WQ) = %g"%(inputData.demographics['fraction food insecure (poor)'])
print "Frac food insecure (upper WQ) = %g"%(inputData.demographics['fraction food insecure (not poor)'])

numsteps = 180
delay = 12

oldCoverages={}
costCovParams = {}
#print "\n Baseline coverage of: "
for intervention in inputData.interventionList:
    #print "%s = %g"%(intervention,inputData.coverage[intervention])
    oldCoverages[intervention]  = inputData.coverage[intervention]
    # calculate coverage (%)
    costCovParams[intervention] = {}
    costCovParams[intervention]['unitcost']   = dcp(inputData.costSaturation[intervention]["unit cost"])
    costCovParams[intervention]['saturation'] = dcp(inputData.costSaturation[intervention]["saturation coverage"])


#------------------------------------------------------------------------    
# DEFAULT RUN WITH NO CHANGES TO INTERVENTIONS
nametag = "Baseline"
plotcolor = 'grey'

print "\n"+nametag
model, derived, params = helper.setupModelConstantsParameters(inputData)

for iAge in range(numAgeGroups):
    ageName = helper.keyList['ages'][iAge]
    print "Number of children in %s = %i"%(ageName,model.listOfAgeCompartments[iAge].getTotalPopulation())
print "Number of pregnant women = %i"%(model.pregnantWomen.populationSize)

# calculate target population size and current spending
targetPopSize = {}
baselineSpending = {}
baselineBudget = 0.
for intervention in inputData.interventionList:
    targetPopSize[intervention] = 0.
    for iAge in range(numAgeGroups):
        ageName = helper.keyList['ages'][iAge]
        targetPopSize[intervention] += inputData.targetPopulation[intervention][ageName] * model.listOfAgeCompartments[iAge].getTotalPopulation()
    targetPopSize[intervention] +=     inputData.targetPopulation[intervention]['pregnant women'] * model.pregnantWomen.populationSize
    coverageNumber  = oldCoverages[intervention] * targetPopSize[intervention]
    baselineSpending[intervention] = costCov.inversefunction(coverageNumber, costCovParams[intervention], targetPopSize[intervention])
    baselineBudget += baselineSpending[intervention]
    #print "%s = %i USD"%(intervention, baselineSpending[intervention])
#print "Baseline Annual Budget = %i USD"%(baselineBudget)

# Run model
for t in range(delay):
    model.moveOneTimeStep()

for t in range(numsteps-delay):
    model.moveOneTimeStep()

baselineStunted = model.getOutcome('stunting')
print "Number of children stunted = %i"%baselineStunted
baselineDeaths = model.getOutcome('deaths')
print "Number of deaths = %i"%baselineDeaths

#------------------------------------------------------------------------    
# FULL PACKAGE
fullCoverage = 0.8

title = '\n Scale up all interventions to %i%%'%(fullCoverage*100)
print title

modelB, derived, params = helper.setupModelConstantsParameters(inputData)

# New coverage scenario
newCoverages = dcp(oldCoverages)
for ichoose in range(len(inputData.interventionList)):
    intervention = inputData.interventionList[ichoose]
    newCoverages[intervention] = fullCoverage

# calculate target population size and new spending
targetPopSize = {}
newSpending = {}
newBudget = 0.
for intervention in inputData.interventionList:
    print "\n %s"%intervention
    targetPopSize[intervention] = 0.
    for iAge in range(numAgeGroups):
        ageName = helper.keyList['ages'][iAge]
        targetPopSize[intervention] += inputData.targetPopulation[intervention][ageName] * modelB.listOfAgeCompartments[iAge].getTotalPopulation()
    targetPopSize[intervention] +=     inputData.targetPopulation[intervention]['pregnant women'] * modelB.pregnantWomen.populationSize
    print "Target Population Size = %i"%(targetPopSize[intervention])
    coverageNumber  = newCoverages[intervention] * targetPopSize[intervention]
    newSpending[intervention] = costCov.inversefunction(coverageNumber, costCovParams[intervention], targetPopSize[intervention])
    print "Spending = %i USD"%(newSpending[intervention])
    newBudget += newSpending[intervention]
print "New Annual Budget = %i USD"%(newBudget)

for t in range(delay):
    modelB.moveOneTimeStep()

modelFP = dcp(modelB)

# scale up intervention
modelFP.updateCoverages(newCoverages)

# Run model
for t in range(numsteps-delay):
    modelFP.moveOneTimeStep()

newFPstunted = modelFP.getOutcome('stunting')
print "number of children stunted = %i"%newFPstunted
print "number of cases averted = %i"%(baselineStunted - newFPstunted)
newFPdeaths = modelFP.getOutcome('deaths')
print "number of deaths= %i"%newFPdeaths
print "number of deaths averted = %i"%(baselineDeaths - newFPdeaths)


#------------------------------------------------------------------------    
# FULL CFE ONLY 
fullCoverage = 0.8
CompFeed = 'Complementary feeding education'
title = '\n Scale up %s to %i%%'%(CompFeed, fullCoverage*100)
print title

modelB, derived, params = helper.setupModelConstantsParameters(inputData)

# New coverage scenario
newCoverages = dcp(oldCoverages)
newCoverages[CompFeed] = fullCoverage

# calculate target population size and new spending
targetPopSize = {}
newSpending = {}
newBudget = 0.
for intervention in inputData.interventionList:
    targetPopSize[intervention] = 0.
    for iAge in range(numAgeGroups):
        ageName = helper.keyList['ages'][iAge]
        targetPopSize[intervention] += inputData.targetPopulation[intervention][ageName] * modelB.listOfAgeCompartments[iAge].getTotalPopulation()
    targetPopSize[intervention] +=     inputData.targetPopulation[intervention]['pregnant women'] * modelB.pregnantWomen.populationSize
    coverageNumber  = newCoverages[intervention] * targetPopSize[intervention]
    newSpending[intervention] = costCov.inversefunction(coverageNumber, costCovParams[intervention], targetPopSize[intervention])
    newBudget += newSpending[intervention]
print "New Annual Budget = %i USD"%(newBudget)

for t in range(delay):
    modelB.moveOneTimeStep()

modelCFE = dcp(modelB)

# scale up intervention
modelCFE.updateCoverages(newCoverages)

# Run model
for t in range(numsteps-delay):
    modelCFE.moveOneTimeStep()

newCFEstunted = modelCFE.getOutcome('stunting')
print "number of children stunted = %i"%newCFEstunted
print "number of cases averted = %i"%(baselineStunted - newCFEstunted)
newCFEdeaths = modelCFE.getOutcome('deaths')
print "number of deaths= %i"%newCFEdeaths
print "number of deaths averted = %i"%(baselineDeaths - newCFEdeaths)


#------------------------------------------------------------------------    



