# -*- coding: utf-8 -*-
"""
Created on Wed Feb 24 13:49:18 2016

@author: ruthpearson
"""

import model as modelCode
import data as dataCode
import constants as constantsCode



#key of combinations of stunting and wasting
# normal - up to 1 SD less than mean
# mild - between 1 and 2 SD less than mean
# moderate - between 2 and 3 SD less than mean
# high - more than 3 SD less than mean


# make the fertile women
mothers = modelCode.FertileWomen(0.2, 500)

# read the data from the spreadsheet
#spreadsheetData = dataCode.getDataFromSpreadsheet('InputForCode.xlsx')
spreadsheetData = dataCode.getFakeData()

#----------------------   MAKE ALL THE BOXES     ---------------------
listOfAgeCompartments = []
ageRangeList  = spreadsheetData.ages
agingRateList = [1./1., 1./5., 1./6., 1./12., 1./36.]
numAgeGroups = len(ageRangeList)

# Loop over all age-groups
for age in range(numAgeGroups): 
    ageRange  = ageRangeList[age]
    agingRate = agingRateList[age]

# allBoxes is a dictionary rather than a list to provide to AgeCompartment
    allBoxes = {}
    for stuntingStatus in ["normal", "mild", "moderate", "high"]:
        allBoxes[stuntingStatus] = {} 
        for wastingStatus in ["normal", "mild", "moderate", "high"]:
            allBoxes[stuntingStatus][wastingStatus] = {}
            for breastfeedingStatus in ["exclusive", "predominant", "partial", "none"]:
                thisPopSize = 100 #place holder
                thisMortalityRate = 0.1 #place holder
                allBoxes[stuntingStatus][wastingStatus][breastfeedingStatus] =  modelCode.Box(stuntingStatus, wastingStatus, breastfeedingStatus, thisPopSize, thisMortalityRate)

    compartment = modelCode.AgeCompartment(ageRange, allBoxes, agingRate)
    listOfAgeCompartments.append(compartment)
    
#------------------------------------------------------------------------    

# make a model object
model = modelCode.Model("Main model", mothers, listOfAgeCompartments, spreadsheetData.ages)

# make a constants object
# (initialisation sets all constant values based on inputdata and inputmodel) 
constants = constantsCode.Constants(spreadsheetData, model)

#set the constants in the model
model.setConstants(constants)

model.updateMortalityRate(spreadsheetData)
model.applyMortality()
model.applyAging()









