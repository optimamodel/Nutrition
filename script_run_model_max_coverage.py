# -*- coding: utf-8 -*-
"""
Created on Thu Oct  6 16:59:18 2016

@author: ruth
"""

import data
from copy import deepcopy as dcp
import helper
helper = helper.Helper()

numModelSteps = 180
dataSpreadsheetName = 'input_spreadsheets/Bangladesh/2016Sept12/InputForCode_Bangladesh.xlsx'
spreadsheetData = data.readSpreadsheet(dataSpreadsheetName, helper.keyList)
model, derived, params = helper.setupModelConstantsParameters(spreadsheetData)

# run the model
modelList = []    
timestepsPre = 12
for t in range(timestepsPre):
    model.moveOneTimeStep()  
    modelThisTimeStep = dcp(model)
    modelList.append(modelThisTimeStep)
    
# update coverages after 1 year    
newCoverages = {}    
for i in range(0, len(spreadsheetData.interventionList)):
    intervention = spreadsheetData.interventionList[i]
    newCoverages[intervention] = 1
    
model.updateCoverages(newCoverages)

for t in range(numModelSteps - timestepsPre):
    model.moveOneTimeStep()
    modelThisTimeStep = dcp(model)
    modelList.append(modelThisTimeStep)