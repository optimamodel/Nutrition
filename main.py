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



ages = ["<1 month","1-5 months","6-11 months","12-23 months","24-59 months"]
birthOutcomes = ["Pre-term SGA","Pre-term AGA","Term SGA","Term AGA"]
wastingList = ["normal", "mild", "moderate", "high"]
stuntingList = ["normal", "mild", "moderate", "high"]
breastfeedingList = ["exclusive", "predominant", "partial", "none"]
keyList = [ages,birthOutcomes,wastingList,stuntingList,breastfeedingList]

# read the data from the spreadsheet
spreadsheetData = dataCode.getDataFromSpreadsheet('InputForCode.xlsx',keyList)

# make the fertile women
mothers = modelCode.FertileWomen(0.9, 2.e6)

ageRangeList  = ages #spreadsheetData.ages
agingRateList = [1./1., 1./5., 1./6., 1./12., 1./36.] # fraction of people aging out per MONTH
numAgeGroups = len(ageRangeList)
agePopSizes  = [2.e5, 4.e5, 7.e5, 1.44e6, 44.e5]

timestep = 1./12. # 1 month #timespan / float(numsteps)
numsteps = 168  # number of timesteps; determined to produce a sensible timestep
timespan = timestep * float(numsteps)


#-------------------------------------------------------------------------
def makeBoxes(thisAgePopSize, ageRange):
    allBoxes = {}
    for stuntingCat in stuntingList:
        allBoxes[stuntingCat] = {} 
        for wastingCat in wastingList:
            allBoxes[stuntingCat][wastingCat] = {}
            for breastfeedingCat in breastfeedingList:
                thisPopSize = thisAgePopSize * spreadsheetData.stuntingDistribution[ageRange][stuntingCat] * spreadsheetData.wastingDistribution[ageRange][wastingCat] * spreadsheetData.breastfeedingDistribution[ageRange][breastfeedingCat]   # Assuming independent
                thisMortalityRate = spreadsheetData.totalMortality[ageRange] # WARNING need to distribute appropriately
                allBoxes[stuntingCat][wastingCat][breastfeedingCat] =  modelCode.Box(stuntingCat, wastingCat, breastfeedingCat, thisPopSize, thisMortalityRate)
    return allBoxes

def makeAgeCompartements(ageRangeList, agingRateList, agePopSizes, keyList):
    numAgeGroups = len(ageRangeList)
    listOfAgeCompartments = []
    for age in range(numAgeGroups): # Loop over all age-groups
        ageRange  = ageRangeList[age]
        agingRate = agingRateList[age]
        agePopSize = agePopSizes[age]
        thisAgeBoxes = makeBoxes(agePopSize, ageRange)
        compartment = modelCode.AgeCompartment(ageRange, thisAgeBoxes, agingRate, keyList)
        listOfAgeCompartments.append(compartment)
    return listOfAgeCompartments         
#------------------------------------------------------------------------    


plotData = []

#------------------------------------------------------------------------    
# DEFAULT RUN WITH NO CHANGES TO INTERVENTIONS

# DEFAULT RUN WITH NO CHANGES TO INTERVENTIONS
listOfAgeCompartments = makeAgeCompartements(ageRangeList, agingRateList, agePopSizes, keyList)
model = modelCode.Model("Main model", mothers, listOfAgeCompartments, keyList, timestep)
constants = constantsCode.Constants(spreadsheetData, model, keyList)
model.setConstants(constants)
params = parametersCode.Params(spreadsheetData,constants,keyList)
model.setParams(params)


pickleFilename = 'testDefault.pkl'
#open file to dump objects into at each time step
import pickle as pickle
outfile = open(pickleFilename, 'wb')

for t in range(numsteps):
    #print t
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
"""
#plotting scripts assume numsteps is a multiple of 12 (integer years)
output.getPopSizeByAgePlot(modelList, tag)
output.getPopAndStuntedSizePlot(modelList, tag)
output.getCumulativeDeathsByAgePlot(modelList, tag)
output.getNumStuntedByAgePlot(modelList, tag)
output.getStuntedPercent(modelList, tag)
"""
plotData.append({})
plotData[0]["modelList"] = modelList
plotData[0]["tag"] = tag
plotData[0]["color"] = 'grey'

#------------------------------------------------------------------------    
# INTERVENTION
listOfAgeCompartments = makeAgeCompartements(ageRangeList, agingRateList, agePopSizes, keyList)
modelZ = modelCode.Model("Zinc model", mothers, listOfAgeCompartments, keyList, timestep)
constants = constantsCode.Constants(spreadsheetData, modelZ, keyList)
modelZ.setConstants(constants)
params = parametersCode.Params(spreadsheetData,constants,keyList)
modelZ.setParams(params)

# increase zinc coverage
newCoverages={}
newCoverages["Zinc supplementation"] = 0.3
print "Update Zinc supplementation coverage to %g percent"%(newCoverages["Zinc supplementation"]*100.)
modelZ.updateCoverages(newCoverages)




# file to dump objects into at each time step
pickleFilename = 'testZinc.pkl'
import pickle as pickle
outfile = open(pickleFilename, 'wb')

for t in range(numsteps):
    #print t
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

tag = "increased Zinc"
"""
#plotting scripts assume numsteps is a multiple of 12 (integer years)
output.getPopSizeByAgePlot(newModelList, tag)
output.getPopAndStuntedSizePlot(newModelList, tag)
output.getCumulativeDeathsByAgePlot(newModelList, tag)
output.getNumStuntedByAgePlot(newModelList, tag)
output.getStuntedPercent(newModelList, tag)
"""

plotData.append({})
plotData[1]["modelList"] = newModelList
plotData[1]["tag"] = tag
plotData[1]["color"] = 'blue'


output.getCombinedPlots(2,plotData)



