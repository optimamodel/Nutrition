# -*- coding: utf-8 -*-
"""
Created on Wed Jun 14 2016

@author: madhurakilledar
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
date = '2016Sept12'

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
Zinc = 'Prophylactic zinc supplementation'
eachBudget = totalBudget * fracScaleup / 2.
# For each intervention...
for intervention in [CompFeed, Zinc]:

    # allocation of funding
    newInvestment   = eachBudget
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



