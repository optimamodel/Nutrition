# -*- coding: utf-8 -*-
"""
Created on Tue May  3 09:54:36 2016

@author: ruth
"""

import data as dataCode
import output as output
import pickle as pickle
import helper as helper

helper = helper.Helper()
ages = ["<1 month","1-5 months","6-11 months","12-23 months","24-59 months"]
birthOutcomes = ["Pre-term SGA","Pre-term AGA","Term SGA","Term AGA"]
wastingList = ["normal", "mild", "moderate", "high"]
stuntingList = ["normal", "mild", "moderate", "high"]
breastfeedingList = ["exclusive", "predominant", "partial", "none"]
keyList = [ages,birthOutcomes,wastingList,stuntingList,breastfeedingList]
spreadsheetData = dataCode.getDataFromSpreadsheet('InputForCode_Bangladesh.xlsx', keyList)
mothers = {'birthRate':0.9, 'populationSize':2.e6}
mothers['annualPercentPopGrowth'] = - 0.01
agingRateList = [1./1., 1./5., 1./6., 1./12., 1./36.] # fraction of people aging out per MONTH
numAgeGroups = len(ages)
agePopSizes  = [2.e5, 4.e5, 7.e5, 1.44e6, 44.e5]
timestep = 1./12. # 1 month 
numsteps = 168  
timespan = timestep * float(numsteps)

for intervention in spreadsheetData.interventionList:
    print "Baseline coverage of %s = %g"%(intervention,spreadsheetData.interventionCoveragesCurrent[intervention])



#------------------------------------------------------------------------    
# DEFAULT RUN WITH NO CHANGES TO INTERVENTIONS
nametag = 'without interventions'
model, constants, params = helper.setupModelConstantsParameters(nametag, mothers, timestep, agingRateList, agePopSizes, keyList, spreadsheetData)


pickleFilename = 'testDefault.pkl'
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



#------------------------------------------------------------------------    
# INTERVENTION
nametag = 'with interventions'
modelZ, constants, params = helper.setupModelConstantsParameters(nametag, mothers, timestep, agingRateList, agePopSizes, keyList, spreadsheetData)


newCoverages={}
for intervention in spreadsheetData.interventionList:
    newCoverages[intervention] = spreadsheetData.interventionCoveragesCurrent[intervention]
for intervention in spreadsheetData.interventionList:
    newCoverages[intervention] = min(1.0,newCoverages[intervention]+0.3) 
modelZ.updateCoverages(newCoverages)



# file to dump objects into at each time step
pickleFilename = 'testInterventions.pkl'
outfile = open(pickleFilename, 'wb')

for t in range(numsteps):
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


#output.getPopAndStuntedSizePlot(modelList, 'before')
#output.getPopAndStuntedSizePlot(newModelList, 'after')

output.getNumStuntedByAgePlot(modelList, 'before')
output.getNumStuntedByAgePlot(newModelList, 'after')

output.getStuntedPercent(modelList, 'before')
output.getStuntedPercent(newModelList, 'after')

#output.getCumulativeDeathsByAgePlot(modelList, 'before')
#output.getCumulativeDeathsByAgePlot(newModelList, 'after')


output.getDeathsAverted(modelList, newModelList, '')

plotData = []
plotData.append({})
plotData[0]["modelList"] = modelList
plotData[0]["tag"] = 'no intervention'
plotData[0]["color"] = 'grey'
plotData.append({})
plotData[1]["modelList"] = newModelList
plotData[1]["tag"] = 'with intervention'
plotData[1]["color"] = 'blue'
output.getCombinedPlots(2, plotData)




