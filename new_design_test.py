# -*- coding: utf-8 -*-
"""
Created on Wed Feb 24 13:49:18 2016

@author: ruthpearson
"""

import new_design as code
import fake_data as fakeDataCode
import solvingEquations as equations

#make the fertile women
mothers = code.FertileWomen(0.2, 500)

#key of combinations of stunting and wasting
# normal - up to 1 SD less than mean
# mild - between 1 and 2 SD less than mean
# moderate - between 2 and 3 SD less than mean
# high - more than 3 SD less than mean


# <insert code to read from spreadsheet> ;)

listOfAgeCompartments = []
ageRangeList  = ["0-1 month","1-6 months","6-12 months","12-24 months","24-59 months"]
agingRateList = [1./1., 1./5., 1./6., 1./12., 1./36.]
numAgeGroups = len(ageRangeList)

# Loop over all age-groups
for age in range(numAgeGroups): #made the 'G' capital 
    ageRange  = ageRangeList[age]
    agingRate = agingRateList[age]

# allBoxes is a dictionary rather than a list to provide to AgeCompartment
    allBoxes = {}
    for stuntingStatus in ["normal", "mild", "moderate", "high"]:
        allBoxes[stuntingStatus] = {} 
        for wastingStatus in ["normal", "mild", "moderate", "high"]:
            allBoxes[stuntingStatus][wastingStatus] = {}
            for breastFeedingStatus in ["exclusive", "predominant", "partial", "none"]:
                thisPopSize = 100 #place holder
                thisMortalityRate = 0.1 #place holder
                allBoxes[stuntingStatus][wastingStatus][breastFeedingStatus] =  code.Box(stuntingStatus, wastingStatus, breastFeedingStatus, thisPopSize, thisMortalityRate)

    compartment = code.AgeCompartment(ageRange, allBoxes, agingRate)
    listOfAgeCompartments.append(compartment)



#make the model object
model = code.Model("Main model", mothers, listOfAgeCompartments)
fakeData = fakeDataCode.getFakeData()
model.calcConstants(fakeData)

model.applyMortality()
model.applyAging()

underlyingMortality = equations.getUnderlyingMortalityByAge(fakeData)

model.updateMortalityRate(fakeData, underlyingMortality)


