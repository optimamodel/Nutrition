# -*- coding: utf-8 -*-
"""
Created on Wed Feb 24 13:49:18 2016

@author: ruthpearson
"""

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


# make the fertile women
mothers = modelCode.FertileWomen(0.9, 2.e6)

# read the data from the spreadsheet
spreadsheetData = dataCode.getDataFromSpreadsheet('InputForCode.xlsx')

#----------------------   MAKE ALL THE BOXES     ---------------------
listOfAgeCompartments = []
ageRangeList  = spreadsheetData.ages
agingRateList = [1./1., 1./5., 1./6., 1./12., 1./36.] # fraction of people aging out per MONTH
numAgeGroups = len(ageRangeList)
agePopSizes  = [2.e5, 3.e5, 7.e5, 14.e5, 43.e5]

#timespan = 5.0 # [years] running the model for this long
timestep = 1./12. # 1 month #timespan / float(numsteps)
numsteps = 110  # number of timesteps; determined to produce a sensible timestep
timespan = timestep * float(numsteps)

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
                thisPopSize = agePopSize * spreadsheetData.stuntingDistribution[ageRange][stuntingCat] * spreadsheetData.wastingDistribution[ageRange][wastingCat] * spreadsheetData.breastfeedingDistribution[ageRange][breastfeedingCat]   # Assuming independent
                thisMortalityRate = spreadsheetData.totalMortality[ageRange] # WARNING need to distribute appropriately
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

#set the parameters in the model
params = parametersCode.Params(spreadsheetData)
# UPDATE WITH INTERVENTIONS
# -------------------------------------------------------------------------
## intervention:  make first 2 age groups exclusively breastfed 
#for age in ['<1 month', '1-5 months']:
#    for status in ["predominant", "partial", "none"]:
#        params.breastfeedingDistribution[age][status] = 0
#        params.breastfeedingDistribution[age]['exclusive'] = 1         

## intervention:  improve breastfeeding in first 2 age groups 
"""
for age in ['<1 month', '1-5 months']:
    params.breastfeedingDistribution[age]['exclusive'] = 0.6
    params.breastfeedingDistribution[age]['predominant'] = 0.3
    params.breastfeedingDistribution[age]['partial'] = 0.1
    params.breastfeedingDistribution[age]['none'] = 0
"""
# -------------------------------------------------------------------------    
model.setParams(params)





#open file to dump objects into at each time step
import pickle as pickle
outfile = open('testOutput.pkl', 'wb')

for t in range(numsteps):
    print t
    model.moveOneTimeStep()
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

#ploting scripts assume numsteps is a multiple of 12 (integer years)
output.getPopSizeByAgePlot(modelList, "test")
output.getCumulativeDeathsByAgePlot(modelList, "test")
output.getNumStuntedByAgePlot(modelList, "test")
output.getStuntedPercent(modelList, "test")





