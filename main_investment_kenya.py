# -*- coding: utf-8 -*-
"""
Created on Wed Feb 24 13:49:18 2016

@author: ruthpearson
"""
from __future__ import division

import data as dataCode
import helper as helper
import output as output
from copy import deepcopy as dcp
import pickle as pickle
import costcov
from numpy import array

helper = helper.Helper()
costCov = costcov.Costcov()

ages = ["<1 month", "1-5 months", "6-11 months", "12-23 months", "24-59 months"]
birthOutcomes = ["Pre-term SGA", "Pre-term AGA", "Term SGA", "Term AGA"]
wastingList = ["normal", "mild", "moderate", "high"]
stuntingList = ["normal", "mild", "moderate", "high"]
breastfeedingList = ["exclusive", "predominant", "partial", "none"]
keyList = [ages, birthOutcomes, wastingList, stuntingList, breastfeedingList]
spreadsheetData = dataCode.getDataFromSpreadsheet('InputForCode.xlsx', keyList)
mothers = {'birthRate':0.9, 'populationSize':2.e6}
ageRangeList  = ages 
agingRateList = [1./1., 1./5., 1./6., 1./12., 1./36.] # fraction of people aging out per MONTH
numAgeGroups = len(ageRangeList)
agePopSizes  = [1.7e5, 4.e5, 7.e5, 1.44e6, 44.e5]
timestep = 1./12. 
numsteps = 168
timespan = timestep * float(numsteps)
nstep_eq = 24

for intervention in spreadsheetData.interventionList:
    print "Baseline coverage of %s = %g"%(intervention,spreadsheetData.interventionCoveragesCurrent[intervention])

plotData = []
run = 0

#------------------------------------------------------------------------    
# DEFAULT RUN WITH NO CHANGES TO INTERVENTIONS
nametag = "Baseline"
pickleFilename = 'testDefault.pkl'
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
investmentIncrease = 1.e6

for ichoose in range(len(spreadsheetData.interventionList)):
    chosenIntervention = spreadsheetData.interventionList[ichoose]
    nametag = chosenIntervention
    pickleFilename = 'test_Intervention%i_Invest.pkl'%(ichoose)
    plotcolor = (1.0-0.13*run, 1.0-0.3*abs(run-4), 0.0+0.13*run)
    print "\n %s: increase investment by BDT %g"%(nametag,investmentIncrease)

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
    # allocation of funding
    investmentDict = {} # dictionary of money for each intervention
    for intervention in spreadsheetData.interventionList:
        investmentDict[intervention] = investmentIncrease # 1 million BDT per intervention per year for the full 14 years
    # calculate coverage (%)
    targetPopSize = {}
    investment = array([investmentDict[chosenIntervention]])
    targetPopSize[chosenIntervention] = 0.
    for ageInd in range(numAgeGroups):
        age = ages[ageInd]
        targetPopSize[chosenIntervention] += spreadsheetData.interventionTargetPop[chosenIntervention][age] * modelX.listOfAgeCompartments[ageInd].getTotalPopulation()
    targetPopSize[chosenIntervention] +=     spreadsheetData.interventionTargetPop[chosenIntervention]['pregnant women'] * modelX.fertileWomen.populationSize
    ccopar = {}
    ccopar['unitcost']   = array([dcp(spreadsheetData.interventionCostCoverage[chosenIntervention]["unit cost"])])
    ccopar['saturation'] = array([dcp(spreadsheetData.interventionCostCoverage[chosenIntervention]["saturation coverage"])])
    additionalPeopleCovered = costCov.function(investment, ccopar, targetPopSize[chosenIntervention]) # function from HIV
    additionalCoverage = additionalPeopleCovered / targetPopSize[chosenIntervention]
    print "additional coverage: %g"%(additionalCoverage)
    newCoverages[chosenIntervention] += additionalCoverage[0] 
    print "new coverage: %g"%(newCoverages[chosenIntervention])
    # scale up intervention
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


"""
#------------------------------------------------------------------------    
# INTERVENTION
percentageIncrease = 90
nametag = "All interventions: increase coverage by %g%% points"%(percentageIncrease)
pickleFilename = 'test_Intervention_P%i.pkl'%(percentageIncrease)
plotcolor = 'black'

print "\n"+nametag
modelZ, constants, params = helper.setupModelConstantsParameters(nametag, mothers, timestep, agingRateList, agePopSizes, keyList, spreadsheetData)


# Find equilibrium
for t in range(nstep_eq):
    modelZ.moveOneTimeStep()

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
    newCoverages[intervention] = min(1.0,newCoverages[intervention]+percentageIncrease/100.) 
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


output.getCombinedPlots(run, plotData)



