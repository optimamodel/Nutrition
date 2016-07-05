# -*- coding: utf-8 -*-
"""
Created on Wed Feb 24 13:49:18 2016

@author: ruthpearson
"""
from __future__ import division
from copy import deepcopy as dcp
import pickle as pickle

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(moduleDir)
import data as dataCode
import helper as helper
import output as output

country = 'Kenya'
startYear = 2016
#agePopSizes  = [1.7e5, 4.e5, 7.e5, 1.44e6, 44.e5]

helper = helper.Helper()
ages = ["<1 month", "1-5 months", "6-11 months", "12-23 months", "24-59 months"]
birthOutcomes = ["Pre-term SGA", "Pre-term AGA", "Term SGA", "Term AGA"]
wastingList = ["normal", "mild", "moderate", "high"]
stuntingList = ["normal", "mild", "moderate", "high"]
breastfeedingList = ["exclusive", "predominant", "partial", "none"]
keyList = [ages, birthOutcomes, wastingList, stuntingList, breastfeedingList]
ageGroupSpans = [1., 5., 6., 12., 36.] # number of months in each age group
agingRateList = [1./1., 1./5., 1./6., 1./12., 1./36.] # fraction of people aging out per MONTH
timestep = 1./12. 

dataFilename = '../input_spreadsheets/%s/Input_%s_%i.xlsx'%(country,country,startYear)
spreadsheetData = dataCode.getDataFromSpreadsheet(dataFilename, keyList)
mothers = helper.makePregnantWomen(spreadsheetData)
#mothers['annualPercentPopGrowth'] = 0.03
numAgeGroups = len(ages)
agePopSizes  = helper.makeAgePopSizes(numAgeGroups, ageGroupSpans, spreadsheetData)

numsteps = 168
timespan = timestep * float(numsteps)

for intervention in spreadsheetData.interventionList:
    print "Baseline coverage of %s = %g"%(intervention,spreadsheetData.interventionCoveragesCurrent[intervention])

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
pickle.dump(model, outfile)
model.moveOneTimeStep()
pickle.dump(model, outfile)

# Run model
for t in range(numsteps-2):
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
percentageIncrease = 50

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
    pickle.dump(modelX, outfile)
    modelX.moveOneTimeStep()
    pickle.dump(modelX, outfile)

    # initialise
    newCoverages={}
    for intervention in spreadsheetData.interventionList:
        newCoverages[intervention] = spreadsheetData.interventionCoveragesCurrent[intervention]
    # scale up intervention
    newCoverages[chosenIntervention] += percentageIncrease/100.
    newCoverages[chosenIntervention] = min(newCoverages[chosenIntervention],spreadsheetData.interventionCostCoverage[chosenIntervention]["saturation coverage"])
    newCoverages[chosenIntervention] = max(newCoverages[chosenIntervention],spreadsheetData.interventionCoveragesCurrent[chosenIntervention])
    newCoverages[chosenIntervention] = max(newCoverages[chosenIntervention],0.0)
    modelX.updateCoverages(newCoverages)

    # Run model
    for t in range(numsteps-2):
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
percentageIncrease = 50
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


#------------------------------------------------------------------------    


output.getCombinedPlots(run, plotData)
output.getDeathsAverted(modelList, newModelList, 'test')



