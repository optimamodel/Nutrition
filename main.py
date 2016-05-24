# -*- coding: utf-8 -*-
"""
Created on Wed Feb 24 13:49:18 2016

@author: ruthpearson
"""
from __future__ import division

import model as modelCode
import data as dataCode
import constants as constantsCode
import parameters as parametersCode
import output as output



ages = ["<1 month", "1-5 months", "6-11 months", "12-23 months", "24-59 months"]
birthOutcomes = ["Pre-term SGA", "Pre-term AGA", "Term SGA", "Term AGA"]
wastingList = ["normal", "mild", "moderate", "high"]
stuntingList = ["normal", "mild", "moderate", "high"]
breastfeedingList = ["exclusive", "predominant", "partial", "none"]
keyList = [ages, birthOutcomes, wastingList, stuntingList, breastfeedingList]

spreadsheetData = dataCode.getDataFromSpreadsheet('InputForCode.xlsx', keyList)
mothers = modelCode.FertileWomen(0.9, 2.e6)

ageRangeList  = ages 
agingRateList = [1./1., 1./5., 1./6., 1./12., 1./36.] # fraction of people aging out per MONTH
numAgeGroups = len(ageRangeList)
agePopSizes  = [2.e5, 4.e5, 7.e5, 1.44e6, 44.e5]

timestep = 1./12. 
numsteps = 168  
timespan = timestep * float(numsteps)


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

plotData = []
run = 0


#------------------------------------------------------------------------    
# INTERVENTION
listOfAgeCompartments = makeAgeCompartements(agingRateList, agePopSizes, keyList)
modelZ = modelCode.Model("Decreased Coverage model", mothers, listOfAgeCompartments, keyList, timestep)
constants = constantsCode.Constants(spreadsheetData, modelZ, keyList)
modelZ.setConstants(constants)
params = parametersCode.Params(spreadsheetData,constants,keyList)
modelZ.setParams(params)
modelZ.updateMortalityRate()

# scale up interventions
# initialise
newCoverages={}
for intervention in spreadsheetData.interventionList:
    newCoverages[intervention] = spreadsheetData.interventionCoveragesCurrent[intervention]
    print "Current coverage of %s = %g"%(intervention,newCoverages[intervention])
# decrease coverage for all by 30 percentage points (capped at 0%)
for intervention in spreadsheetData.interventionList:
    newCoverages[intervention] = max(0.0,newCoverages[intervention]-0.3) 
    print "New coverage of %s = %g"%(intervention,newCoverages[intervention])
modelZ.updateCoverages(newCoverages)

# file to dump objects into at each time step
pickleFilename = 'test_Intervention_M30.pkl'
import pickle as pickle
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

tag = "all interventions - decrease coverage by 30\%"
plotData.append({})
plotData[run]["modelList"] = newModelList
plotData[run]["tag"] = tag
plotData[run]["color"] = 'red'
run += 1


#------------------------------------------------------------------------    
# DEFAULT RUN WITH NO CHANGES TO INTERVENTIONS
listOfAgeCompartments = makeAgeCompartements(agingRateList, agePopSizes, keyList)
model = modelCode.Model("Main model", mothers, listOfAgeCompartments, keyList, timestep)
constants = constantsCode.Constants(spreadsheetData, model, keyList)
model.setConstants(constants)
params = parametersCode.Params(spreadsheetData, constants, keyList)
model.setParams(params)
model.updateMortalityRate()

pickleFilename = 'testDefault.pkl'
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

tag = "default"
plotData.append({})
plotData[run]["modelList"] = modelList
plotData[run]["tag"] = tag
plotData[run]["color"] = 'grey'
run += 1

#------------------------------------------------------------------------    
# INTERVENTION
listOfAgeCompartments = makeAgeCompartements(agingRateList, agePopSizes, keyList)
modelZ = modelCode.Model("Increased Coverage model", mothers, listOfAgeCompartments, keyList, timestep)
constants = constantsCode.Constants(spreadsheetData, modelZ, keyList)
modelZ.setConstants(constants)
params = parametersCode.Params(spreadsheetData,constants,keyList)
modelZ.setParams(params)
modelZ.updateMortalityRate()

# scale up interventions
# initialise
newCoverages={}
for intervention in spreadsheetData.interventionList:
    newCoverages[intervention] = spreadsheetData.interventionCoveragesCurrent[intervention]
    print "Current coverage of %s = %g"%(intervention,newCoverages[intervention])
# increase coverage for all by 30 percentage points (capped at 100%)
for intervention in spreadsheetData.interventionList:
    newCoverages[intervention] = min(1.0,newCoverages[intervention]+0.3) 
    print "New coverage of %s = %g"%(intervention,newCoverages[intervention])
# increase zinc coverage
#newCoverages["Zinc supplementation"] = 1.0
modelZ.updateCoverages(newCoverages)


# file to dump objects into at each time step
pickleFilename = 'test_Intervention_P30.pkl'
import pickle as pickle
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

tag = "all interventions - increase coverage by 30\%"
plotData.append({})
plotData[run]["modelList"] = newModelList
plotData[run]["tag"] = tag
plotData[run]["color"] = 'blue'
run += 1


#------------------------------------------------------------------------    


output.getCombinedPlots(run, plotData)
output.getDeathsAverted(modelList, newModelList, 'test')



