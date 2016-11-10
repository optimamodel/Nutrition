# -*- coding: utf-8 -*-
"""
Created on Thu Oct  6 16:59:18 2016

@author: ruth
"""

import data
from copy import deepcopy as dcp
import helper
import numpy as np
import optimisation
import csv
helper = helper.Helper()
numModelSteps = 120
numYears = 10
years = range(2016, 2016 + numYears)

country = 'Bangladesh'
date = '2016Oct'
# national spreadsheet
spreadsheet = 'input_spreadsheets/'+country+'/'+date+'/InputForCode_'+country+'.xlsx'
# regional spreadsheets
regionNameList = ['Barisal', 'Chittagong', 'Dhaka', 'Khulna', 'Rajshahi', 'Rangpur', 'Sylhet']
spreadsheetFileStem = 'input_spreadsheets/' + country + '/' + date + '/subregionSpreadsheets/'
# put the national spreadsheet into a spreadsheet list, then append the regional spreadsheets
spreadsheetList = [spreadsheet]
for regionName in regionNameList:
    spreadsheet = spreadsheetFileStem + regionName + '.xlsx'
    spreadsheetList.append(spreadsheet)


# ------------------    SOME USEFUL FUNCTIONS       ---------------------------

def getYearlyObjectiveList(spreadsheet):
    spreadsheetData = data.readSpreadsheet(spreadsheet, helper.keyList)
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
    
    # get outcomes
    outcomeOfInterestList = ['deaths', 'stunting', 'DALYs']
    # get y axis
    objective = {}    
    objectiveYearly = {}
    for outcomeOfInterest in outcomeOfInterestList:
        objective[outcomeOfInterest] = []
        objective[outcomeOfInterest].append(modelList[0].getOutcome(outcomeOfInterest))
        for i in range(1, numModelSteps):
            difference = modelList[i].getOutcome(outcomeOfInterest) - modelList[i-1].getOutcome(outcomeOfInterest)
            objective[outcomeOfInterest].append(difference)
        # make it yearly
        numYears = numModelSteps/12
        objectiveYearly[outcomeOfInterest] = []
        for i in range(0, numYears):
            step = i*12
            objectiveYearly[outcomeOfInterest].append( sum(objective[outcomeOfInterest][step:12+step]) )
    #stunting prev is a bit different so do it separately
    outcomeOfInterest = 'stunting prev'
    objective[outcomeOfInterest] = []
    for i in range(0, numModelSteps):
        objective[outcomeOfInterest].append(modelList[i].getOutcome(outcomeOfInterest))
    # make it yearly
    numYears = numModelSteps/12
    objectiveYearly[outcomeOfInterest] = []
    for i in range(0, numYears):
        step = i*12
        objectiveYearly[outcomeOfInterest].append( np.mean(objective[outcomeOfInterest][step:12+step]) )        
    return objectiveYearly


def getBaseline(spreadsheet):
    optimise = 'dummy1'
    resultsFileStem = 'dummy2'
    thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, optimise, resultsFileStem)
    baselineAllocation = thisOptimisation.getInitialAllocationDictionary()
    modelList = thisOptimisation.oneModelRunWithOutput(baselineAllocation)
    # get outcomes
    outcomeOfInterestList = ['deaths', 'stunting', 'DALYs']
    # get y axis
    objective = {}    
    objectiveYearly = {}
    for outcomeOfInterest in outcomeOfInterestList:
        objective[outcomeOfInterest] = []
        objective[outcomeOfInterest].append(modelList[0].getOutcome(outcomeOfInterest))
        for i in range(1, numModelSteps):
            difference = modelList[i].getOutcome(outcomeOfInterest) - modelList[i-1].getOutcome(outcomeOfInterest)
            objective[outcomeOfInterest].append(difference)
        # make it yearly
        numYears = numModelSteps/12
        objectiveYearly[outcomeOfInterest] = []
        for i in range(0, numYears):
            step = i*12
            objectiveYearly[outcomeOfInterest].append( sum(objective[outcomeOfInterest][step:12+step]) )
    #stunting prev is a bit different so do it separately
    outcomeOfInterest = 'stunting prev'
    objective[outcomeOfInterest] = []
    for i in range(0, numModelSteps):
        objective[outcomeOfInterest].append(modelList[i].getOutcome(outcomeOfInterest))
    # make it yearly
    numYears = numModelSteps/12
    objectiveYearly[outcomeOfInterest] = []
    for i in range(0, numYears):
        step = i*12
        objectiveYearly[outcomeOfInterest].append( np.mean(objective[outcomeOfInterest][step:12+step]) )        
    return objectiveYearly

# -----------------------------------------------------------------------------

# GENERATE RESULTS AND OUTPUT TO CSV 
nameList = ['national'] + regionNameList
results = {}
results['baseline'] = {}
results['full coverage'] = {}
for i in range(len(spreadsheetList)):
    regionName = nameList[i]
    print regionName
    spreadsheet = spreadsheetList[i]
    results['full coverage'][regionName] = getYearlyObjectiveList(spreadsheet)
    results['baseline'][regionName] = getBaseline(spreadsheet)


rows = []
for analysis in ['baseline', 'full coverage']:
    rows.append('')
    rows.append([analysis] + [' ', ' ', ' ',' ', ' ', ' ',' ', ' ', ' ',' '])
    for objective in ['stunting', 'stunting prev', 'deaths', 'DALYs']:
        rows.append('')        
        rows.append([objective] + [' ', ' ', ' ',' ', ' ', ' ',' ', ' ', ' ',' '])
        rows.append([' '] + years)
        for region in nameList:
            rows.append([region] + results[analysis][region][objective])
outfilename = 'Bangladesh_full_coverage_comparison.csv'
with open(outfilename, "wb") as f:
    writer = csv.writer(f)
    writer.writerows(rows)   




