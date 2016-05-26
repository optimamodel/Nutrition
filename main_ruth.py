# -*- coding: utf-8 -*-
"""
Created on Tue May  3 09:54:36 2016

@author: ruth
"""

import model as modelCode
import data as dataCode
import constants as constantsCode
import parameters as parametersCode
import output as output
import pickle as pickle

#-------------------------------------------------------------------------    
def makeBoxes(thisAgePopSize, ageGroup, keyList):
    allBoxes = {}
    ages, birthOutcomes, wastingList, stuntingList, breastfeedingList = keyList
    for stuntingCat in stuntingList:
        allBoxes[stuntingCat] = {} 
        for wastingCat in wastingList:
            allBoxes[stuntingCat][wastingCat] = {}
            for breastfeedingCat in breastfeedingList:
                thisPopSize = thisAgePopSize * spreadsheetData.stuntingDistribution[ageGroup][stuntingCat] * spreadsheetData.wastingDistribution[ageGroup][wastingCat] * spreadsheetData.breastfeedingDistribution[ageGroup][breastfeedingCat]   # Assuming independent
                thisMortalityRate = 0
                allBoxes[stuntingCat][wastingCat][breastfeedingCat] =  modelCode.Box(stuntingCat, wastingCat, breastfeedingCat, thisPopSize, thisMortalityRate)
    return allBoxes

def makeAgeCompartements(agingRateList, agePopSizes, keyList):
    ages, birthOutcomes, wastingList, stuntingList, breastfeedingList = keyList
    numAgeGroups = len(ages)
    listOfAgeCompartments = []
    for age in range(numAgeGroups): # Loop over all age-groups
        ageGroup  = ages[age]
        agingRate = agingRateList[age]
        agePopSize = agePopSizes[age]
        thisAgeBoxes = makeBoxes(agePopSize, ageGroup, keyList)
        compartment = modelCode.AgeCompartment(ageGroup, thisAgeBoxes, agingRate, keyList)
        listOfAgeCompartments.append(compartment)
    return listOfAgeCompartments         
#-------------------------------------------------------------------------    


ages = ["<1 month","1-5 months","6-11 months","12-23 months","24-59 months"]
birthOutcomes = ["Pre-term SGA","Pre-term AGA","Term SGA","Term AGA"]
wastingList = ["normal", "mild", "moderate", "high"]
stuntingList = ["normal", "mild", "moderate", "high"]
breastfeedingList = ["exclusive", "predominant", "partial", "none"]
keyList = [ages,birthOutcomes,wastingList,stuntingList,breastfeedingList]

# read the data from the spreadsheet
spreadsheetData = dataCode.getDataFromSpreadsheet('InputForCode.xlsx', keyList)
# make the fertile women
mothers = modelCode.FertileWomen(0.9, 2.e6)

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
listOfAgeCompartments = makeAgeCompartements(agingRateList, agePopSizes, keyList)
model = modelCode.Model("Main model", mothers, listOfAgeCompartments, keyList, timestep)
constants = constantsCode.Constants(spreadsheetData, model, keyList)
model.setConstants(constants)
params = parametersCode.Params(spreadsheetData, constants, keyList)
model.setParams(params)
model.updateMortalityRate() #now update mortlaity rate of all the boxes


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
listOfAgeCompartments = makeAgeCompartements(agingRateList, agePopSizes, keyList)
modelZ = modelCode.Model("Interventions added model", mothers, listOfAgeCompartments, keyList, timestep)
constants = constantsCode.Constants(spreadsheetData, modelZ, keyList)
modelZ.setConstants(constants)
params = parametersCode.Params(spreadsheetData, constants, keyList)
modelZ.setParams(params)
modelZ.updateMortalityRate() #now update mortlaity rate of all the boxes


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




