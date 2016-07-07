# -*- coding: utf-8 -*-
"""
Created on Wed June 01 2016

@author: madhurakilledar
"""
from __future__ import division
from copy import deepcopy as dcp
import pickle as pickle

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(moduleDir)
import data
import helper
import output

helper = helper.Helper()

country = 'Bangladesh'
startYear = 2016

dataFilename = '../input_spreadsheets/%s/InputForCode_%s.xlsx'%(country,country)
inputData = data.getDataFromSpreadsheet(dataFilename, helper.keyList)
numAgeGroups = len(helper.keyList['ages'])

numsteps = 180

newCoverages={}
print "Baseline coverages:"
for intervention in inputData.interventionList:
    print "%s : %g"%(intervention,inputData.interventionCoveragesCurrent[intervention])

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
percentageIncrease = 20
title = '%s: 2015-2030 \n Scale up intervention by %i%%'%(country,percentageIncrease)
print title

numInterventions = len(inputData.interventionList)
colorStep = 1./float(numInterventions)-1.e-2
for ichoose in range(numInterventions):
    chosenIntervention = inputData.interventionList[ichoose]
    nametag = chosenIntervention
    pickleFilename = '%s_Intervention%i_P%i.pkl'%(country,ichoose,percentageIncrease)
    plotcolor = (1.0-colorStep*run, 1.0-0.23*abs(run-4), 0.0+colorStep*run)

    print "\n"+nametag
    modelX, derived, params = helper.setupModelConstantsParameters(inputData)

    # file to dump objects into at each time step
    outfile = open(pickleFilename, 'wb')
    modelX.moveOneTimeStep()
    pickle.dump(modelX, outfile)

    modelX.getDiagnostics(verbose=True)

    # initialise
    for intervention in inputData.interventionList:
        newCoverages[intervention] = inputData.interventionCoveragesCurrent[intervention]
    # scale up intervention
    newCoverages[chosenIntervention] += percentageIncrease/100.
    newCoverages[chosenIntervention] = min(newCoverages[chosenIntervention],inputData.interventionCostCoverage[chosenIntervention]["saturation coverage"])
    newCoverages[chosenIntervention] = max(newCoverages[chosenIntervention],inputData.interventionCoveragesCurrent[chosenIntervention])
    newCoverages[chosenIntervention] = max(newCoverages[chosenIntervention],0.0)
    print "new coverage: %g"%(newCoverages[chosenIntervention])
    modelX.updateCoverages(newCoverages)

    modelX.getDiagnostics(verbose=True)

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
# INTERVENTION
percentageIncrease = 30
nametag = "All interventions: increase coverage by %g%% points"%(percentageIncrease)
pickleFilename = '%s_Intervention_P%i.pkl'%(country,percentageIncrease)
plotcolor = 'black'

print "\n"+nametag
modelZ, derived, params = helper.setupModelConstantsParameters(inputData)


# file to dump objects into at each time step
outfile = open(pickleFilename, 'wb')
pickle.dump(modelZ, outfile)
modelZ.moveOneTimeStep()
pickle.dump(modelZ, outfile)

# scale up all interventions
# initialise
newCoverages={}
for intervention in inputData.interventionList:
    newCoverages[intervention] = inputData.interventionCoveragesCurrent[intervention]
for intervention in inputData.interventionList:
    newCoverages[intervention] += percentageIncrease/100.
    newCoverages[intervention] = min(newCoverages[intervention],inputData.interventionCostCoverage[intervention]["saturation coverage"])
    newCoverages[intervention] = max(newCoverages[intervention],inputData.interventionCoveragesCurrent[intervention])
    newCoverages[intervention] = max(newCoverages[intervention],0.0)
modelZ.updateCoverages(newCoverages)

# Run model
for t in range(numsteps-2):
    modelZ.moveOneTimeStep()
    pickle.dump(modelZ, outfile)
outfile.close()    

# collect output, make graphs etc.
infile = open(pickleFilename, 'rb')
newModelList = []
while 1:
    try:
        newModelList.append(pickle.load(infile))
    except (EOFError):
        break
infile.close()

plotData.append({})
plotData[run]["modelList"] = newModelList
plotData[run]["tag"] = nametag
plotData[run]["color"] = plotcolor
run += 1

#------------------------------------------------------------------------    

filenamePrefix = '%s_fixedScaleup'%(country)

output.getCombinedPlots(run, plotData, startYear=startYear-1, filenamePrefix=filenamePrefix, save=True)
output.getCompareDeathsAverted(run, plotData, scalePercent=0.5, filenamePrefix=filenamePrefix, title=title, save=True)
output.getU5StuntingCasesAverted(run, plotData, scalePercent=0.5, filenamePrefix=filenamePrefix, title=title, save=True)
output.getA5StuntingCasesAverted(run, plotData, scalePercent=0.5, filenamePrefix=filenamePrefix, title=title, save=True)



