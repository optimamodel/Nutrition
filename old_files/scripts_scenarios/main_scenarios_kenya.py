# -*- coding: utf-8 -*-
"""
Created on Wed Feb 24 13:49:18 2016

@author: ruthpearson
"""
from __future__ import division
import pickle as pickle

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(moduleDir)
from nutrition import data
from old_files import helper
import output

helper = helper.Helper()

country = 'Kenya'
startYear = 2016

dataFilename = '../input_spreadsheets/%s/Input_%s_%i.xlsx'%(country,country,startYear)
inputData = data.readSpreadsheet(dataFilename, helper.keyList)
numAgeGroups = len(helper.keyList['ages'])

numsteps = 168
timespan = helper.keyList['timestep'] * float(numsteps)

for intervention in inputData.interventionList:
    print "Baseline coverage of %s = %g"%(intervention,inputData.coverage[intervention])

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
    pickle.dump(modelX, outfile)
    modelX.moveOneTimeStep()
    pickle.dump(modelX, outfile)

    # initialise
    newCoverages={}
    for intervention in inputData.interventionList:
        newCoverages[intervention] = inputData.coverage[intervention]
    # scale up intervention
    newCoverages[chosenIntervention] += percentageIncrease/100.
    newCoverages[chosenIntervention] = min(newCoverages[chosenIntervention],inputData.costSaturation[chosenIntervention]["saturation coverage"])
    newCoverages[chosenIntervention] = max(newCoverages[chosenIntervention],inputData.coverage[chosenIntervention])
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
    newCoverages[intervention] = inputData.coverage[intervention]
for intervention in inputData.interventionList:
    newCoverages[intervention] += percentageIncrease/100.
    newCoverages[intervention] = min(newCoverages[intervention],inputData.costSaturation[intervention]["saturation coverage"])
    newCoverages[intervention] = max(newCoverages[intervention],inputData.coverage[intervention])
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



