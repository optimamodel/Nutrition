# -*- coding: utf-8 -*-
"""
Created on Tue May 16 16:28:10 2017

@author: ruth
"""

import costcov
import optimisation
import helper
import data
costCov = costcov.Costcov()
helper = helper.Helper()

#get spreadsheet list
regionNameList = ['Barisal', 'Chittagong', 'Dhaka', 'Khulna', 'Rajshahi', 'Rangpur', 'Sylhet']
spreadsheetFileStem = 'input_spreadsheets/Bangladesh/2016Oct/subregionSpreadsheets/'
spreadsheetList = []
for regionName in regionNameList:
    spreadsheet = spreadsheetFileStem + regionName + '.xlsx'
    spreadsheetList.append(spreadsheet)

# get the plots
for region in range(0, len(regionNameList)):
    regionName = regionNameList[region]
    spreadsheet = spreadsheetList[region]
    thisData = data.readSpreadsheet(spreadsheet, helper.keyList)
    thisOptimisation = optimisation.Optimisation(spreadsheet, 180, 'thrive', 'dummy')
    costCovInfo = thisOptimisation.getCostCoverageInfo()
    # get target popsize
    model, derived, params = helper.setupModelConstantsParameters(thisData)
    # run the model
    for t in range(12):
        model.moveOneTimeStep()    
    # want target popsize after 1 year (this is when we add interventions)
    targetPopSize = optimisation.getTargetPopSizeFromModelInstance(spreadsheet, helper.keyList, model) 
    costCov.plotCurves(targetPopSize, costCovInfo, regionName)
