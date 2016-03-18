# -*- coding: utf-8 -*-
"""
Created on Wed Feb 24 13:49:18 2016

@author: ruthpearson
"""

import model as modelCode
import data as dataCode
import constants as constantsCode
import output as output



#key of combinations of stunting and wasting
# normal - up to 1 SD less than mean
# mild - between 1 and 2 SD less than mean
# moderate - between 2 and 3 SD less than mean
# high - more than 3 SD less than mean


# make the fertile women
mothers = modelCode.FertileWomen(0.2, 2.e6)

# read the data from the spreadsheet
spreadsheetData = dataCode.getDataFromSpreadsheet('InputForCode.xlsx')
# get fake data
#fakeData = dataCode.getFakeData()

#----------------------   MAKE ALL THE BOXES     ---------------------
listOfAgeCompartments = []
ageRangeList  = spreadsheetData.ages
agingRateList = [1./1., 1./5., 1./6., 1./12., 1./36.] # fraction of people aging out per year
numAgeGroups = len(ageRangeList)
agePopSizes  = [2.e5, 3.e5, 7.e5, 14.e5, 43.e5]

timespan = 5.0 # [years] running the model for this long
numsteps = 10  # number of timesteps; determined to produce a sensible timestep
timestep = timespan / float(numsteps)

# Loop over all age-groups
for age in range(numAgeGroups): 
    ageRange  = ageRangeList[age]
    agingRate = agingRateList[age]
    agePopSize = agePopSizes[age]

# allBoxes is a dictionary rather than a list to provide to AgeCompartment
    allBoxes = {}
    for stuntingCat in ["normal", "mild", "moderate", "high"]:
        allBoxes[stuntingCat] = {} 
        for wastingCat in ["normal", "mild", "moderate", "high"]:
            allBoxes[stuntingCat][wastingCat] = {}
            for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
                thisPopSize = int( agePopSize * spreadsheetData.stuntingDistribution[stuntingCat][ageRange] * spreadsheetData.wastingDistribution[wastingCat][ageRange] * spreadsheetData.breastfeedingDistribution[breastfeedingCat][ageRange]  ) # Assuming independent
                thisMortalityRate = spreadsheetData.totalMortalityByAge[age] # WARNING need to distribute appropriately
                allBoxes[stuntingCat][wastingCat][breastfeedingCat] =  modelCode.Box(stuntingCat, wastingCat, breastfeedingCat, thisPopSize, thisMortalityRate)

    compartment = modelCode.AgeCompartment(ageRange, allBoxes, agingRate)
    listOfAgeCompartments.append(compartment)
    
#------------------------------------------------------------------------    

# make a model object
model = modelCode.Model("Main model", mothers, listOfAgeCompartments, spreadsheetData.ages, timestep)

# make a constants object
# (initialisation sets all constant values based on inputdata and inputmodel) 
constants = constantsCode.Constants(spreadsheetData, model)

#set the constants in the model
model.setConstants(constants)

# TODO create dataframe to hold numsteps datapoints for any important output

# These will go into a time-loop

#open file to dump objects into at each time step
import pickle as pickle
outfile = open('testOutput.pkl', 'wb')

for t in range(numsteps):
    print t
    model.moveOneTimeStep(spreadsheetData)
    pickle.dump(model, outfile)
    
outfile.close()    

# collect output, make graphs etc.
infile = open('testOutput.pkl', 'rb')
modelList = []
while 1:
    try:
        modelList.append(pickle.load(infile))
    except (EOFError):
        break
infile.close()

output.getPopSizeByAgePlot(modelList)
output.getCumulativeDeathsByAgePlot(modelList)
output.getNumStuntedByAgePlot(modelList)
output.getStuntedPercent(modelList)





