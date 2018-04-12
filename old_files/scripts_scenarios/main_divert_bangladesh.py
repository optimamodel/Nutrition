# -*- coding: utf-8 -*-
"""
Created on Wed Jun 14 2016

@author: madhurakilledar

AIM: compare outcomes for interventions
when intervention receives extra funds
(which have been diverted away from current allocation, so that total budget remains unchanged)

INPUT:
REQUIRED FILES
input spreadsheet - see dataFilename

VARIABLES
country
startYear
date
dataFilename
numsteps
diverted_fraction

OUTPUT:
code will create a bunch of png files using function in output.py
- horizontal bar graphs comparing outcomes for each intervention (relative to baseline)
- time trends of health outcomes

"""
from __future__ import division
from copy import deepcopy as dcp

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(moduleDir)
import data
import output
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

plotData = []
run = 0

#------------------------------------------------------------------------    
# DEFAULT RUN WITH NO CHANGES TO INTERVENTIONS
nametag = "Baseline"
plotcolor = 'grey'

print "\n"+nametag
model, derived, params = helper.setupModelConstantsParameters(inputData)
modelList = []

# Run model
for t in range(numsteps):
    model.moveOneTimeStep()
    modelList.append(dcp(model))

plotData.append({})
plotData[run]["modelList"] = modelList
plotData[run]["tag"] = nametag
plotData[run]["color"] = plotcolor
run += 1

#------------------------------------------------------------------------    
# INTERVENTION
diverted_fraction = 0.33
title = '%s: 2015-2030 \n Divert %g%% of current budget into one intervention'%(country,diverted_fraction*100)
print title

modelB, derived, params = helper.setupModelConstantsParameters(inputData)
modelB.moveOneTimeStep()

# calculate target population size and current spending
currentBudget = 0.
targetPopSize = {}
currentSpending = {}
newCoverages = {}
for intervention in inputData.interventionList:
    print intervention
    targetPopSize[intervention] = 0.
    for iAge in range(numAgeGroups):
        ageName = helper.keyList['ages'][iAge]
        targetPopSize[intervention] += inputData.targetPopulation[intervention][ageName] * modelB.listOfAgeCompartments[iAge].getTotalPopulation()
    targetPopSize[intervention] +=     inputData.targetPopulation[intervention]['pregnant women'] * modelB.pregnantWomen.populationSize
    coverageNumber  = oldCoverages[intervention] * targetPopSize[intervention]
    currentSpending[intervention] = costCov.inversefunction(coverageNumber, costCovParams[intervention], targetPopSize[intervention])
    print currentSpending[intervention]
    currentBudget += currentSpending[intervention]
print 'Current Budget = %g USD'%currentBudget


# calculate reduced coverage (implied by funding reduced by some fraction)
reducedCoverages = {}
for intervention in inputData.interventionList:
    # reduced coverage for all interventions
    investment = (1.-diverted_fraction)*currentSpending[intervention]
    peopleCovered   = costCov.function(investment, costCovParams[intervention], targetPopSize[intervention])
    fractionCovered = peopleCovered / targetPopSize[intervention]
    reducedCoverages[intervention] = fractionCovered

for ichoose in range(len(inputData.interventionList)):
    chosenIntervention = inputData.interventionList[ichoose]
    nametag = chosenIntervention
    plotcolor = (1.0-0.13*run, 1.0-0.24*abs(run-4), 0.0+0.13*run)
    print "\n %s"%nametag

    modelX = dcp(modelB)
    modelXList = []
    modelXList.append(dcp(modelX))

    newCoverages = dcp(reducedCoverages)

    # coverage for chosen intervention (fractionally reduced funding, then additional funds from whole budget)
    investment = currentBudget*diverted_fraction + (1.-diverted_fraction)*currentSpending[chosenIntervention]
    peopleCovered   = costCov.function(investment, costCovParams[chosenIntervention], targetPopSize[chosenIntervention])
    fractionCovered = peopleCovered / targetPopSize[chosenIntervention]
    newCoverages[chosenIntervention] = fractionCovered
    print "new coverage: %g"%(newCoverages[chosenIntervention])
    # scale up intervention
    modelX.updateCoverages(newCoverages)

    # Run model
    for t in range(numsteps-1):
        modelX.moveOneTimeStep()
        modelXList.append(dcp(modelX))

    plotData.append({})
    plotData[run]["modelList"] = modelXList
    plotData[run]["tag"] = nametag
    plotData[run]["color"] = plotcolor
    run += 1


#------------------------------------------------------------------------    

filenamePrefix = '%s_%s_divert'%(country, date)

output.getCombinedPlots(         run, plotData, startYear=startYear-1, filenamePrefix=filenamePrefix, save=True)
output.getCompareDeathsAverted(  run, plotData, scalePercent=0.2, filenamePrefix=filenamePrefix, title=title, save=True)
output.getDALYsAverted(          run, plotData, scalePercent=0.2, filenamePrefix=filenamePrefix, title=title, save=True)
output.getU5StuntingCasesAverted(run, plotData, scalePercent=0.5, filenamePrefix=filenamePrefix, title=title, save=True)
output.getA5StuntingCasesAverted(run, plotData, scalePercent=0.5, filenamePrefix=filenamePrefix, title=title, save=True)



