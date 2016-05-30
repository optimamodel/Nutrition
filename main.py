# -*- coding: utf-8 -*-
"""
Created on Wed Feb 24 13:49:18 2016

@author: ruthpearson
"""
from __future__ import division

import data as dataCode
import output as output
import helper as helper
from copy import deepcopy as dcp


helper = helper.Helper()
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
agePopSizes  = [2.e5, 4.e5, 7.e5, 1.44e6, 44.e5]
timestep = 1./12. 
numsteps = 168  
timespan = timestep * float(numsteps)

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

import pickle as pickle
outfile = open(pickleFilename, 'wb')
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
nametag = "Fixed investment"
pickleFilename = 'test_Investment.pkl'
plotcolor = 'green'

print "\n"+nametag
modelZ, constants, params = helper.setupModelConstantsParameters(nametag, mothers, timestep, agingRateList, agePopSizes, keyList, spreadsheetData)


# file to dump objects into at each time step
import pickle as pickle
outfile = open(pickleFilename, 'wb')
modelZ.moveOneTimeStep()
pickle.dump(modelZ, outfile)

# initialise
newCoverages={}
for intervention in spreadsheetData.interventionList:
    newCoverages[intervention] = spreadsheetData.interventionCoveragesCurrent[intervention]
"""
investmentDict = {} # dictionary of money for each intervention
for intervention in spreadsheetData.interventionList:
    unitcost   = dcp(spreadsheetData.interventionCostCoverage[intervention]["unit cost"])
    saturation = dcp(spreadsheetData.interventionCostCoverage[intervention]["saturation coverage"])
    newCoverages[intervention] = costcoverage(investment, unitcost, saturation, targetpop) # function from HIV
"""
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


output.getCombinedPlots(run, plotData)
output.getDeathsAverted(modelList, newModelList, 'test')



