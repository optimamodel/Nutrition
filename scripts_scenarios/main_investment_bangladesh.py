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
version = '1604'

dataFilename = '../input_spreadsheets/%s/InputForCode_%s.xlsx'%(country, country)
#dataFilename = '../input_spreadsheets/%s/Input_%s_%i_%s.xlsx'%(country, country, startYear, version)
inputData = data.readSpreadsheet(dataFilename, helper.keyList)
numAgeGroups = len(helper.keyList['ages'])

numsteps = 180

print "Baseline coverage of: "
for intervention in inputData.interventionList:
    print "%s = %g"%(intervention,inputData.coverage[intervention])

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
investmentIncrease = 1.e6  # 1 million USD per intervention per year for the full 15 years
title = '%s: 2015-2030 \n Scale up intervention by %i million USD per year'%(country,investmentIncrease/1e6)
print title

for ichoose in range(len(inputData.interventionList)):
    chosenIntervention = inputData.interventionList[ichoose]
    nametag = chosenIntervention
    plotcolor = (1.0-0.13*run, 1.0-0.24*abs(run-4), 0.0+0.13*run)
    print "\n %s: increase in annual investment by USD %g"%(nametag,investmentIncrease)

    modelX, derived, params = helper.setupModelConstantsParameters(inputData)
    modelXList = []

    modelX.moveOneTimeStep()
    modelXList.append(dcp(modelX))

    # initialise
    newCoverages={}
    for intervention in inputData.interventionList:
        newCoverages[intervention] = inputData.coverage[intervention]
    # allocation of funding
    investment = array([investmentIncrease])
    # calculate coverage (%)
    targetPopSize = {}
    targetPopSize[chosenIntervention] = 0.
    for iAge in range(numAgeGroups):
        ageName = helper.keyList['ages'][iAge]
        targetPopSize[chosenIntervention] += inputData.targetPopulation[chosenIntervention][ageName] * modelX.listOfAgeCompartments[iAge].getTotalPopulation()
    targetPopSize[chosenIntervention] +=     inputData.targetPopulation[chosenIntervention]['pregnant women'] * modelX.pregnantWomen.populationSize
    costCovParams = {}
    costCovParams['unitcost']   = array([dcp(inputData.costSaturation[chosenIntervention]["unit cost"])])
    costCovParams['saturation'] = array([dcp(inputData.costSaturation[chosenIntervention]["saturation coverage"])])
    additionalPeopleCovered   = costCov.function(investment, costCovParams, targetPopSize[chosenIntervention]) # function from HIV
    additionalFractionCovered = additionalPeopleCovered / targetPopSize[chosenIntervention]
    print "additional coverage: %g"%(additionalFractionCovered)
    newCoverages[chosenIntervention] += additionalFractionCovered
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

filenamePrefix = '%s_%s_fixedInvest'%(country, version)

output.getCombinedPlots(run, plotData, startYear=startYear-1, filenamePrefix=filenamePrefix, save=True)
output.getCompareDeathsAverted(run, plotData, scalePercent=0.1, filenamePrefix=filenamePrefix, title=title, save=True)
output.getU5StuntingCasesAverted(run, plotData, scalePercent=0.5, filenamePrefix=filenamePrefix, title=title, save=True)
output.getA5StuntingCasesAverted(run, plotData, scalePercent=0.5, filenamePrefix=filenamePrefix, title=title, save=True)



