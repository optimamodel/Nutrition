# -*- coding: utf-8 -*-
"""
Created in Oct 2016

@author: madhurakilledar

AIM: compare cases of stunting in three scenarios
1. baseline
2. total budget increased and all interventions scaled up but with the same relative allocation
3. total budget increased (by the same multiple) and optimal allocation used (must have been determined beforehand)

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

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(moduleDir)
from nutrition import data
from old_files import costcov, helper

helper = helper.Helper()
costCov = costcov.Costcov()

country = 'Bangladesh'
startYear = 2016
date = '2016Oct'

dataFilename = '../input_spreadsheets/%s/%s/InputForCode_%s.xlsx'%(country, date, country)
inputData = data.readSpreadsheet(dataFilename, helper.keyList)
numAgeGroups = len(helper.keyList['ages'])

numsteps = 180
delay = 12

oldCoverages={}
costCovParams = {}
print "\n Baseline coverage of: "
for intervention in inputData.interventionList:
    print "%s = %g"%(intervention,inputData.coverage[intervention])
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

# Run model
for t in range(numsteps):
    model.moveOneTimeStep()

#model.getDiagnostics(verbose=True)
numStunted = model.getOutcome('stunting')
print "Number of children stunted = %i"%numStunted
baselineStunted = numStunted

#------------------------------------------------------------------------    
# ADD FUNDING & EXPAND EACH INTERVENTION ACCORDINGLY
fracScaleup = 2.
title = '\n%s: 2015-2030 \nScale up each intervention by %i%%'%(country,fracScaleup*100)
print title

modelB, derived, params = helper.setupModelConstantsParameters(inputData)
for t in range(delay):
    modelB.moveOneTimeStep()

# calculate target population size and current spending
targetPopSize = {}
currentSpending = {}
totalBudget = 0.
for intervention in inputData.interventionList:
    targetPopSize[intervention] = 0.
    for iAge in range(numAgeGroups):
        ageName = helper.keyList['ages'][iAge]
        targetPopSize[intervention] += inputData.targetPopulation[intervention][ageName] * modelB.listOfAgeCompartments[iAge].getTotalPopulation()
    targetPopSize[intervention] +=     inputData.targetPopulation[intervention]['pregnant women'] * modelB.pregnantWomen.populationSize
    coverageNumber  = oldCoverages[intervention] * targetPopSize[intervention]
    currentSpending[intervention] = costCov.inversefunction(coverageNumber, costCovParams[intervention], targetPopSize[intervention])
    totalBudget += currentSpending[intervention]

modelX = dcp(modelB)

newCoverages = dcp(oldCoverages)
# For each intervention...
print "\n NEW coverage"
for ichoose in range(len(inputData.interventionList)):
    intervention = inputData.interventionList[ichoose]

    # allocation of funding
    newInvestment   = currentSpending[intervention] * fracScaleup
    peopleCovered   = costCov.function(newInvestment, costCovParams[intervention], targetPopSize[intervention])
    fractionCovered = peopleCovered / targetPopSize[intervention]
    newCoverages[intervention] = fractionCovered
    print "%s: new investment USD %i, new coverage: %g"%(intervention,newInvestment,newCoverages[intervention])
    # scale up intervention
    modelX.updateCoverages(newCoverages)

# Run model
for t in range(numsteps-delay):
    modelX.moveOneTimeStep()

#modelX.getDiagnostics(verbose=True)
numStunted = modelX.getOutcome('stunting')
print "\n number of children stunted = %i"%numStunted
print " number of cases averted = %i"%(baselineStunted - numStunted)


#------------------------------------------------------------------------    
# ADD FUNDING & APPROXIMATE OPTIMAL ALLOCATION
fracScaleup = 2.
title = '\n%s: 2015-2030 \n Optimal allocation'%(country)
print title

modelB, derived, params = helper.setupModelConstantsParameters(inputData)
for t in range(delay):
    modelB.moveOneTimeStep()

# calculate target population size and current spending
targetPopSize = {}
currentSpending = {}
totalBudget = 0.
for intervention in inputData.interventionList:
    targetPopSize[intervention] = 0.
    for iAge in range(numAgeGroups):
        ageName = helper.keyList['ages'][iAge]
        targetPopSize[intervention] += inputData.targetPopulation[intervention][ageName] * modelB.listOfAgeCompartments[iAge].getTotalPopulation()
    targetPopSize[intervention] +=     inputData.targetPopulation[intervention]['pregnant women'] * modelB.pregnantWomen.populationSize
    coverageNumber  = oldCoverages[intervention] * targetPopSize[intervention]
    currentSpending[intervention] = costCov.inversefunction(coverageNumber, costCovParams[intervention], targetPopSize[intervention])
    totalBudget += currentSpending[intervention]

modelO = dcp(modelB)

newCoverages = dcp(oldCoverages)
print "\n NEW coverage"
CompFeed = 'Complementary feeding education'
VitA = 'Vitamin A supplementation'
#Zinc = 'Prophylactic zinc supplementation'
#eachBudget = totalBudget * fracScaleup / 2.
newBudget = {}
newBudget[CompFeed] = totalBudget * fracScaleup * 2. / 3.
newBudget[VitA]     = totalBudget * fracScaleup * 1. / 3.

# Allocate funds and calculate new coverage
for intervention in [CompFeed, VitA]:
    #newInvestment   = eachBudget
    newInvestment   = newBudget[intervention]
    peopleCovered   = costCov.function(newInvestment, costCovParams[intervention], targetPopSize[intervention])
    fractionCovered = peopleCovered / targetPopSize[intervention]
    newCoverages[intervention] = fractionCovered
    print "%s: new investment USD %i, new coverage: %g"%(intervention,newInvestment,newCoverages[intervention])

# scale up intervention
modelO.updateCoverages(newCoverages)

# Run model
for t in range(numsteps-delay):
    modelO.moveOneTimeStep()

#modelO.getDiagnostics(verbose=True)
numStunted = modelO.getOutcome('stunting')
print "\n number of children stunted = %i"%numStunted
print "number of cases averted = %i"%(baselineStunted - numStunted)

#------------------------------------------------------------------------    



