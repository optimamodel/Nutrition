# -*- coding: utf-8 -*-
"""
Created on Wed Feb 24 13:49:18 2016

@author: ruthpearson
"""
from __future__ import division

import data as dataCode
import output as output
import helper as helper
import pickle as pickle
from copy import deepcopy as dcp
import costcov
from numpy import array

country = 'Bangladesh'
startYear = 2016

helper = helper.Helper()
costCov = costcov.Costcov()

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
agingRateList = [1./1., 1./5., 1./6., 1./12., 1./36.] # fraction of people aging out per MONTH (WARNING use ageSpans to define this)
numAgeGroups = len(ages)
agePopSizes  = helper.makeAgePopSizes(numAgeGroups, ageGroupSpans, spreadsheetData)

timestep = 1./12. 
numsteps = 180  
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
model.moveOneTimeStep()
pickle.dump(model, outfile)

# Run model
for t in range(numsteps-1):
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

#output.getCumulativeDeathsByAgePlot(modelList, nametag)

#------------------------------------------------------------------------    
# INTERVENTION
nametag = "Fixed investment"
pickleFilename = '%s_Investment.pkl'%(country)
plotcolor = 'green'

print "\n"+nametag
modelZ, constants, params = helper.setupModelConstantsParameters(nametag, mothers, timestep, agingRateList, agePopSizes, keyList, spreadsheetData)


# file to dump objects into at each time step
outfile = open(pickleFilename, 'wb')
model.moveOneTimeStep()
pickle.dump(model, outfile)

# initialise
newCoverages={}
for intervention in spreadsheetData.interventionList:
    newCoverages[intervention] = spreadsheetData.interventionCoveragesCurrent[intervention]
# arbitrary allocation of funding
investmentDict = {} # dictionary of money for each intervention
for intervention in spreadsheetData.interventionList:
    investmentDict[intervention] = 1.e6 # 1 million BDT per intervention per year for the full 14 years
# calculate coverage (%)
targetPopSize = {}
for intervention in spreadsheetData.interventionList:
    print intervention
    investment = array([investmentDict[intervention]])
    targetPopSize[intervention] = 0.
    for iAge in range(numAgeGroups):
        ageName = ages[iAge]
        targetPopSize[intervention] += spreadsheetData.interventionTargetPop[intervention][ageName] * modelZ.listOfAgeCompartments[iAge].getTotalPopulation()
    targetPopSize[intervention] +=     spreadsheetData.interventionTargetPop[intervention]['pregnant women'] * modelZ.fertileWomen.populationSize
    costCovParams = {}
    costCovParams['unitcost']   = array([dcp(spreadsheetData.interventionCostCoverage[intervention]["unit cost"])])
    costCovParams['saturation'] = array([dcp(spreadsheetData.interventionCostCoverage[intervention]["saturation coverage"])])
    additionalPeopleCovered = costCov.function(investment, costCovParams, targetPopSize[intervention]) # function from HIV
    additionalCoverage = additionalPeopleCovered / targetPopSize[intervention]
    print "additional coverage: %g"%(additionalCoverage)
    newCoverages[intervention] += additionalCoverage[0] 
    print "new coverage: %g"%(newCoverages[intervention])
# update coverage
modelZ.updateCoverages(newCoverages)

for t in range(numsteps-1):
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


output.getCombinedPlots(run, plotData startYear=startYear-1)
#output.getDeathsAverted(modelList, newModelList, 'test')



