# -*- coding: utf-8 -*-
"""
Created on Wed June 01 2016

@author: madhurakilledar
"""
from __future__ import division

import data as dataCode
import helper as helper
import output as output
from copy import deepcopy as dcp
import pickle as pickle

country = 'Bangladesh'
startYear = 2016

helper = helper.Helper()
ages = ["<1 month", "1-5 months", "6-11 months", "12-23 months", "24-59 months"]
birthOutcomes = ["Pre-term SGA", "Pre-term AGA", "Term SGA", "Term AGA"]
wastingList = ["normal", "mild", "moderate", "high"]
stuntingList = ["normal", "mild", "moderate", "high"]
breastfeedingList = ["exclusive", "predominant", "partial", "none"]
keyList = [ages, birthOutcomes, wastingList, stuntingList, breastfeedingList]

dataFilename = 'InputForCode_%s.xlsx'%(country)
spreadsheetData = dataCode.getDataFromSpreadsheet(dataFilename, keyList)
mothers = helper.makePregnantWomen(spreadsheetData)
mothers['annualPercentPopGrowth'] = -0.01
ageGroupSpans = [1., 5., 6., 12., 36.] # number of months in each age group
agingRateList = [1./1., 1./5., 1./6., 1./12., 1./36.] # fraction of people aging out per MONTH
numAgeGroups = len(ages)
agePopSizes  = helper.makeAgePopSizes(numAgeGroups, ageGroupSpans, spreadsheetData)

timestep = 1./12. 
numsteps = 180
timespan = timestep * float(numsteps)

newCoverages={}
print "Baseline coverages:"
for intervention in spreadsheetData.interventionList:
    print "%s : %g"%(intervention,spreadsheetData.interventionCoveragesCurrent[intervention])

plotData = []
run = 0

#------------------------------------------------------------------------    
# DEFAULT RUN WITH NO CHANGES TO INTERVENTIONS
nametag = "Baseline"
pickleFilename = '%s_Default.pkl'%(country)
plotcolor = 'grey'

print "\n"+nametag
model, constants, params = helper.setupModelConstantsParameters(nametag, mothers, timestep, agingRateList, agePopSizes, keyList, spreadsheetData)

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

numInterventions = len(spreadsheetData.interventionList)
colorStep = 1./float(numInterventions)-1.e-2
for ichoose in range(numInterventions):
    chosenIntervention = spreadsheetData.interventionList[ichoose]
    nametag = chosenIntervention
    pickleFilename = '%s_Intervention%i_P%i.pkl'%(country,ichoose,percentageIncrease)
    plotcolor = (1.0-colorStep*run, 1.0-0.23*abs(run-4), 0.0+colorStep*run)

    print "\n"+nametag
    modelX, constants, params = helper.setupModelConstantsParameters(nametag, mothers, timestep, agingRateList, agePopSizes, keyList, spreadsheetData)

    # file to dump objects into at each time step
    outfile = open(pickleFilename, 'wb')
    modelX.moveOneTimeStep()
    pickle.dump(modelX, outfile)

    modelX.getDiagnostics(verbose=True)

    # initialise
    for intervention in spreadsheetData.interventionList:
        newCoverages[intervention] = spreadsheetData.interventionCoveragesCurrent[intervention]
    # scale up intervention
    newCoverages[chosenIntervention] += percentageIncrease/100.
    newCoverages[chosenIntervention] = min(newCoverages[chosenIntervention],spreadsheetData.interventionCostCoverage[chosenIntervention]["saturation coverage"])
    newCoverages[chosenIntervention] = max(newCoverages[chosenIntervention],spreadsheetData.interventionCoveragesCurrent[chosenIntervention])
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
"""
# INTERVENTION
percentageIncrease = 30
nametag = "All interventions: increase coverage by %g%% points"%(percentageIncrease)
pickleFilename = '%s_Intervention_P%i.pkl'%(country,percentageIncrease)
plotcolor = 'black'

print "\n"+nametag
modelZ, constants, params = helper.setupModelConstantsParameters(nametag, mothers, timestep, agingRateList, agePopSizes, keyList, spreadsheetData)


# file to dump objects into at each time step
outfile = open(pickleFilename, 'wb')
pickle.dump(modelZ, outfile)
modelZ.moveOneTimeStep()
pickle.dump(modelZ, outfile)

# scale up all interventions
# initialise
newCoverages={}
for intervention in spreadsheetData.interventionList:
    newCoverages[intervention] = spreadsheetData.interventionCoveragesCurrent[intervention]
for intervention in spreadsheetData.interventionList:
    newCoverages[intervention] += percentageIncrease/100.
    newCoverages[intervention] = min(newCoverages[intervention],spreadsheetData.interventionCostCoverage[intervention]["saturation coverage"])
    newCoverages[intervention] = max(newCoverages[intervention],spreadsheetData.interventionCoveragesCurrent[intervention])
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
"""

#------------------------------------------------------------------------    

filenamePrefix = '%s_fixedScaleup'%(country)

output.getCombinedPlots(run, plotData, startYear=startYear-1, filenamePrefix=filenamePrefix, save=True)
output.getCompareDeathsAverted(run, plotData, scalePercent=0.5, filenamePrefix=filenamePrefix, title=title, save=True)
output.getStuntingCasesAverted(run, plotData, scalePercent=0.5, filenamePrefix=filenamePrefix, title=title, save=True)



