# -*- coding: utf-8 -*-
"""
Created on Wed Jun 01 2016

@author: madhurakilledar
"""
from __future__ import division
from copy import deepcopy as dcp
import pickle as pickle
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

country = 'Kenya'
startYear = 2016

dataFilename = '../input_spreadsheets/%s/Input_%s_%i.xlsx'%(country, country, startYear)
inputData = data.getDataFromSpreadsheet(dataFilename, keyList)
numAgeGroups = len(helper.keyList['ages'])

numsteps = 180
timespan = helper.keyList['timestep'] * float(numsteps)

for intervention in inputData.interventionList:
    print "Baseline coverage of %s = %g"%(intervention, inputData.coverage[intervention])

plotData = []
run = 0
#------------------------------------------------------------------------    
# DEFAULT RUN WITH NO CHANGES TO INTERVENTIONS
nametag = "Baseline"
pickleFilename = '%s_Default.pkl'%(country)
plotcolor = 'grey'

print "\n"+nametag
model, derived, params = helper.setupModelConstantsParameters(inputData)

# file to dump objects into at each time step
outfile = open(pickleFilename, 'wb')

# Run model
for t in range(numsteps):
    model.moveOneTimeStep()
    pickle.dump(model, outfile)
outfile.close()    

# collect output, make graphs etc.
infile = open(pickleFilename, 'rb')
modelList = []
while 1:
    try:
        modelList.append(pickle.load(infile))
    except (EOFError):
        break
infile.close()

plotData.append({})
plotData[run]["modelList"] = modelList
plotData[run]["tag"] = nametag
plotData[run]["color"] = plotcolor
run += 1

#------------------------------------------------------------------------    
# INTERVENTION
investmentIncrease = 1.e6  # 1 million BDT per intervention per year for the full 14 years
title = '%s: 2015-2030 \n Scale up intervention by %i million BDT per year'%(country,investmentIncrease/1e6)
print title

for ichoose in range(len(inputData.interventionList)):
    chosenIntervention = inputData.interventionList[ichoose]
    nametag = chosenIntervention
    pickleFilename = '%s_Intervention%i_Invest.pkl'%(country,ichoose)
    plotcolor = (1.0-0.13*run, 1.0-0.3*abs(run-4), 0.0+0.13*run)
    print "\n %s: increase investment by BDT %g"%(nametag,investmentIncrease)

    modelX, derived, params = helper.setupModelConstantsParameters(inputData)

    # file to dump objects into at each time step
    outfile = open(pickleFilename, 'wb')
    modelX.moveOneTimeStep()
    pickle.dump(modelX, outfile)

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
    targetPopSize[chosenIntervention] +=     inputData.targetPopulation[chosenIntervention]['pregnant women'] * modelX.fertileWomen.populationSize
    costCovParams = {}
    costCovParams['unitcost']   = array([dcp(inputData.interventionCostCoverage[chosenIntervention]["unit cost"])])
    costCovParams['saturation'] = array([dcp(inputData.interventionCostCoverage[chosenIntervention]["saturation coverage"])])
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
        pickle.dump(modelX, outfile)
    outfile.close()    

    # collect output, make graphs etc.
    infile = open(pickleFilename, 'rb')
    modelXList = []
    while 1:
        try:
            modelXList.append(pickle.load(infile))
        except (EOFError):
            break
    infile.close()

    plotData.append({})
    plotData[run]["modelList"] = modelXList
    plotData[run]["tag"] = nametag
    plotData[run]["color"] = plotcolor
    run += 1


#------------------------------------------------------------------------    

filenamePrefix = '%s_fixedInvest'%(country)

output.getCombinedPlots(run, plotData, startYear=startYear-1, filenamePrefix=filenamePrefix, save=True)
output.getCompareDeathsAverted(run, plotData, scalePercent=0.1, filenamePrefix=filenamePrefix, title=title, save=True)
output.getU5StuntingCasesAverted(run, plotData, scalePercent=0.5, filenamePrefix=filenamePrefix, title=title, save=True)
output.getA5StuntingCasesAverted(run, plotData, scalePercent=0.5, filenamePrefix=filenamePrefix, title=title, save=True)



