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


#key of combinations of stunting and wasting
# normal - up to 1 SD less than mean
# mild - between 1 and 2 SD less than mean
# moderate - between 2 and 3 SD less than mean
# high - more than 3 SD less than mean


ages = ["<1 month","1-5 months","6-11 months","12-23 months","24-59 months"]
birthOutcomes = ["Pre-term SGA","Pre-term AGA","Term SGA","Term AGA"]
wastingList = ["normal", "mild", "moderate", "high"]
stuntingList = ["normal", "mild", "moderate", "high"]
breastfeedingList = ["exclusive", "predominant", "partial", "none"]
keyList = [ages,birthOutcomes,wastingList,stuntingList,breastfeedingList]

# read the data from the spreadsheet
spreadsheetData = dataCode.getDataFromSpreadsheet('InputForCode.xlsx',keyList)

#----------------------   MAKE ALL THE BOXES     ---------------------

# make the fertile women
mothers = modelCode.FertileWomen(0.9, 2.e6)

ageRangeList  = ages #spreadsheetData.ages
agingRateList = [1./1., 1./5., 1./6., 1./12., 1./36.] # fraction of people aging out per MONTH
numAgeGroups = len(ageRangeList)
agePopSizes  = [2.e5, 4.e5, 7.e5, 1.44e6, 44.e5]

#timespan = 5.0 # [years] running the model for this long
timestep = 1./12. # 1 month #timespan / float(numsteps)
numsteps = 168  # number of timesteps; determined to produce a sensible timestep
timespan = timestep * float(numsteps)


# allBoxes is a dictionary rather than a list to provide to AgeCompartment
def makeBoxes(thisAgePopSize):
    allBoxes = {}
    for stuntingCat in ["normal", "mild", "moderate", "high"]:
        allBoxes[stuntingCat] = {} 
        for wastingCat in ["normal", "mild", "moderate", "high"]:
            allBoxes[stuntingCat][wastingCat] = {}
            for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
                thisPopSize = thisAgePopSize * spreadsheetData.stuntingDistribution[ageRange][stuntingCat] * spreadsheetData.wastingDistribution[ageRange][wastingCat] * spreadsheetData.breastfeedingDistribution[ageRange][breastfeedingCat]   # Assuming independent
                thisMortalityRate = spreadsheetData.totalMortality[ageRange] # WARNING need to distribute appropriately
                allBoxes[stuntingCat][wastingCat][breastfeedingCat] =  modelCode.Box(stuntingCat, wastingCat, breastfeedingCat, thisPopSize, thisMortalityRate)
    return allBoxes



#------------------------------------------------------------------------    
# DEFAULT RUN WITH NO CHANGES TO INTERVENTIONS

# Loop over all age-groups
listOfAgeCompartments = []
for age in range(numAgeGroups): 
    ageRange  = ageRangeList[age]
    agingRate = agingRateList[age]
    agePopSize = agePopSizes[age]
    thisAgeBoxes = makeBoxes(agePopSize)
    compartment = modelCode.AgeCompartment(ageRange, thisAgeBoxes, agingRate, keyList)
    listOfAgeCompartments.append(compartment)

# make a model object
model = modelCode.Model("Main model", mothers, listOfAgeCompartments, keyList, timestep)

# make a constants object
# (initialisation sets all constant values based on inputdata and inputmodel) 
constants = constantsCode.Constants(spreadsheetData, model, keyList)
#set the constants in the model
model.setConstants(constants)

#set the parameters in the model
params = parametersCode.Params(spreadsheetData,constants,keyList)
model.setParams(params)


pickleFilename = 'testDefault.pkl'
#open file to dump objects into at each time step
import pickle as pickle
outfile = open(pickleFilename, 'wb')

for t in range(numsteps):
    print t
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

#plotting scripts assume numsteps is a multiple of 12 (integer years)
output.getPopSizeByAgePlot(modelList, "test")
output.getPopAndStuntedSizePlot(modelList, "test")
output.getCumulativeDeathsByAgePlot(modelList, "test")
output.getNumStuntedByAgePlot(modelList, "test")
output.getStuntedPercent(modelList, "test")


#------------------------------------------------------------------------    
# UPDATE PARAMS (NOT DATA) WITH INTERVENTIONS

# Loop over all age-groups
listOfAgeCompartments = []
for age in range(numAgeGroups): 
    ageRange  = ageRangeList[age]
    agingRate = agingRateList[age]
    agePopSize = agePopSizes[age]
    thisAgeBoxes = makeBoxes(agePopSize)
    compartment = modelCode.AgeCompartment(ageRange, thisAgeBoxes, agingRate, keyList)
    listOfAgeCompartments.append(compartment)

# make a model object
model = modelCode.Model("Zinc model", mothers, listOfAgeCompartments, keyList, timestep)

# make a constants object
# (initialisation sets all constant values based on inputdata and inputmodel) 
constants = constantsCode.Constants(spreadsheetData, model, keyList)
#set the constants in the model
model.setConstants(constants)

#set the parameters in the model
params = parametersCode.Params(spreadsheetData,constants,keyList)
# --------------------------------------------------
# Change parameters here
## intervention:  make first 2 age groups exclusively breastfed 
#for age in ['<1 month', '1-5 months']:
#    for status in ["predominant", "partial", "none"]:
#        params.breastfeedingDistribution[age][status] = 0
#        params.breastfeedingDistribution[age]['exclusive'] = 1         
model.setParams(params)
# --------------------------------------------------
#print "Updated interventions"
newCoverages={}
newCoverages["Zinc supplementation"] = 0.5
print "Update Zinc supplementation coverage to %g percent"%(newCoverages["Zinc supplementation"]*100.)
model.updateCoverages(newCoverages)
# -------------------------------------------------------------------------    

pickleFilename = 'testZinc.pkl'
#open file to dump objects into at each time step
import pickle as pickle
outfile = open(pickleFilename, 'wb')

for t in range(numsteps):
    print t
    model.moveOneTimeStep()
    pickle.dump(model, outfile)
    
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

#plotting scripts assume numsteps is a multiple of 12 (integer years)
output.getPopSizeByAgePlot(newModelList, "increased Zinc")
output.getPopAndStuntedSizePlot(newModelList, "increased Zinc")
output.getCumulativeDeathsByAgePlot(newModelList, "increased Zinc")
output.getNumStuntedByAgePlot(newModelList, "increased Zinc")
output.getStuntedPercent(newModelList, "increased Zinc")




