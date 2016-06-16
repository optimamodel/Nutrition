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

dataFilename = 'Input_LiST_%s_%i.xlsx'%(country,startYear)
spreadsheetData = dataCode.getDataFromSpreadsheet(dataFilename, keyList)
mothers = helper.makePregnantWomen(spreadsheetData)
mothers['annualPercentPopGrowth'] = -0.01
ageGroupSpans = [1., 5., 6., 12., 36.] # number of months in each age group
agingRateList = [1./1., 1./5., 1./6., 1./12., 1./36.] # fraction of people aging out per MONTH
numAgeGroups = len(ages)
agePopSizes  = helper.makeAgePopSizes(numAgeGroups, ageGroupSpans, spreadsheetData)
agePopSizes = [246307.75 , 1231538.75 , 1477846.50 , 2950860.00 , 8895211.00 ]


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


#------------------------------------------------------------------------    
# INCREASE COVERAGE OF COMPLEMENTARY FEEDING BY 50%
percentageIncrease = 50
nametag = "Complementary feeding: increase coverage by %g%% points"%(percentageIncrease)
pickleFilename = '%s_CompFeed_P%i.pkl'%(country,percentageIncrease)
plotcolor = 'green'

print "\n"+nametag
modelZ, constants, params = helper.setupModelConstantsParameters(nametag, mothers, timestep, agingRateList, agePopSizes, keyList, spreadsheetData)

# file to dump objects into at each time step
outfile = open(pickleFilename, 'wb')
modelZ.moveOneTimeStep()
pickle.dump(modelZ, outfile)

# initialise
newCoverages={}
for intervention in spreadsheetData.interventionList:
    newCoverages[intervention] = spreadsheetData.interventionCoveragesCurrent[intervention]
# scale up
for intervention in ['Complementary feeding (supplementation)','Complementary feeding (education)']:
    newCoverages[intervention] += percentageIncrease/100.
    newCoverages[intervention] = min(newCoverages[intervention],spreadsheetData.interventionCostCoverage[intervention]["saturation coverage"])
    newCoverages[intervention] = max(newCoverages[intervention],spreadsheetData.interventionCoveragesCurrent[intervention])
    newCoverages[intervention] = max(newCoverages[intervention],0.0)
modelZ.updateCoverages(newCoverages)

# Run model
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
# INCREASE COVERAGE OF BREASTFEEDING FROM 61% to 90%
percentageIncrease = 29
nametag = "Breastfeeding: increase coverage by %g%% points"%(percentageIncrease)
pickleFilename = '%s_BreastFeed_P%i.pkl'%(country,percentageIncrease)
plotcolor = 'blue'

print "\n"+nametag
modelZ, constants, params = helper.setupModelConstantsParameters(nametag, mothers, timestep, agingRateList, agePopSizes, keyList, spreadsheetData)

# file to dump objects into at each time step
outfile = open(pickleFilename, 'wb')
modelZ.moveOneTimeStep()
pickle.dump(modelZ, outfile)

# initialise
newCoverages={}
for intervention in spreadsheetData.interventionList:
    newCoverages[intervention] = spreadsheetData.interventionCoveragesCurrent[intervention]
# scale up
for intervention in ['Breastfeeding promotion (dual delivery)']:
    newCoverages[intervention] += percentageIncrease/100.
    newCoverages[intervention] = min(newCoverages[intervention],spreadsheetData.interventionCostCoverage[intervention]["saturation coverage"])
    newCoverages[intervention] = max(newCoverages[intervention],spreadsheetData.interventionCoveragesCurrent[intervention])
    newCoverages[intervention] = max(newCoverages[intervention],0.0)
modelZ.updateCoverages(newCoverages)

# Run model
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


output.getCombinedPlots(run, plotData, startYear=startYear-1)
output.getDeathsAverted(modelList, newModelList, 'test')
output.getCompareDeathsAverted(run, plotData, filenamePrefix=country, title='comparison with LiST', save=True)



