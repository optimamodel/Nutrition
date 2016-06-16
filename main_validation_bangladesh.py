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
startYear = 2000

timestep = 1./12. 
numsteps = 180
timespan = timestep * float(numsteps)
#endYear  = startYear + int(timespan)

helper = helper.Helper()
ages = ["<1 month", "1-5 months", "6-11 months", "12-23 months", "24-59 months"]
birthOutcomes = ["Pre-term SGA", "Pre-term AGA", "Term SGA", "Term AGA"]
wastingList = ["normal", "mild", "moderate", "high"]
stuntingList = ["normal", "mild", "moderate", "high"]
breastfeedingList = ["exclusive", "predominant", "partial", "none"]
keyList = [ages, birthOutcomes, wastingList, stuntingList, breastfeedingList]

dataFilename = 'Input_Optima_%s_%i.xlsx'%(country,startYear)
spreadsheetData = dataCode.getDataFromSpreadsheet(dataFilename, keyList)
mothers = helper.makePregnantWomen(spreadsheetData)
mothers['annualPercentPopGrowth'] = -0.01
ageGroupSpans = [1., 5., 6., 12., 36.] # number of months in each age group
agingRateList = [1./1., 1./5., 1./6., 1./12., 1./36.] # fraction of people aging out per MONTH
numAgeGroups = len(ages)
agePopSizes  = helper.makeAgePopSizes(numAgeGroups, ageGroupSpans, spreadsheetData)
year1 = 3871841
year2 = 3731124
year3 = 3645815
year4 = 3567786
year5 = 3491964
agePopSizes  = [year1/12., year1*5./12., year1*6./12., year2, year3+year4+year5]

# initialise
newCoverages={}
for intervention in spreadsheetData.interventionList:
    newCoverages[intervention] = spreadsheetData.interventionCoveragesCurrent[intervention]
    print "Baseline coverage of %s = %g"%(intervention,spreadsheetData.interventionCoveragesCurrent[intervention])

plotData = []
run = 0

#------------------------------------------------------------------------    
# DEFAULT RUN WITH NO CHANGES TO INTERVENTIONS
nametag = "Optima model"
filenamePrefix = '%s_Historical'%(country)
pickleFilename = '%s.pkl'%(filenamePrefix)
plotcolor = 'grey'

print "\n"+nametag
model, constants, params = helper.setupModelConstantsParameters(nametag, mothers, timestep, agingRateList, agePopSizes, keyList, spreadsheetData)

totalStepsTaken = 0
# file to dump objects into at each time step
outfile = open(pickleFilename, 'wb')
for t in range(100):
    model.moveOneTimeStep()
    pickle.dump(model, outfile)
totalStepsTaken += t+1

# update coverages
#newCoverages[chosenIntervention] = ??
#newCoverages[chosenIntervention] = min(newCoverages[chosenIntervention],spreadsheetData.interventionCostCoverage[chosenIntervention]["saturation coverage"])
#newCoverages[chosenIntervention] = max(newCoverages[chosenIntervention],0.0)
#model.updateCoverages(newCoverages)

# Run model
for t in range(numsteps-totalStepsTaken):
    model.moveOneTimeStep()
    pickle.dump(model, outfile)
totalStepsTaken += t+1

# done
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


output.getCombinedPlots(run, plotData, startYear=startYear, filenamePrefix=filenamePrefix, save=True)
#output.getDeathsAverted(modelList, newModelList, 'test')
#output.getStuntedPercent(modelList, '2000-2015', startYear=2000)


