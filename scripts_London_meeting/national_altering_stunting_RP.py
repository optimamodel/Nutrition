'''Increases stunting distributions across age groups by given intervals and runs model to check the outcomes'''

rootpath = '..'
import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)

import helper
import data
from copy import deepcopy as dcp

thisHelper = helper.Helper()
country = 'Bangladesh'
date = '2017Jul'
spreadsheetDate = '2016Oct'
dataSpreadsheetPath = rootpath+'/input_spreadsheets/London_spreadsheets/'+country+'/'+spreadsheetDate+'/InputForCode_'+country+'.xlsx'

# get data
spreadsheetData = data.readSpreadsheet(dataSpreadsheetPath, thisHelper.keyList)
interventionList = spreadsheetData.interventionList

# change the stunting distribution
ages = thisHelper.keyList['ages']
stuntingList = thisHelper.keyList['stuntingList']



for increase in [-0.1, 0., 0.1, 0.2]:
    print "looking at increase of:   ", increase
    stuntingDist = dcp(spreadsheetData.stuntingDistribution) 
    for age in ages:
        for stuntingCat in ['moderate', 'high']:
            previousStunting = spreadsheetData.stuntingDistribution[age][stuntingCat]
            stuntingSum = spreadsheetData.stuntingDistribution[age]['moderate'] + spreadsheetData.stuntingDistribution[age]['high']
            stuntingDist[age][stuntingCat] += increase*previousStunting/stuntingSum # percentage increase
        for stuntingCat in ['normal', 'mild']:
            totalStunted = stuntingDist[age]['moderate'] + stuntingDist[age]['high']
            stuntingDist[age][stuntingCat] = (1. - totalStunted)/2.
    # change the stunting distribution of the data object
    spreadsheetDataCopy = dcp(spreadsheetData)
    spreadsheetDataCopy.stuntingDistribution = dcp(stuntingDist)
    
    #print spreadsheetDataCopy.stuntingDistribution

    # set up model
    model, derived, params = thisHelper.setupModelDerivedParameters(spreadsheetDataCopy)

    modelList = []
    # run model
    timesteps = 180
    for t in range(timesteps):
        model.moveOneTimeStep()
        modelThisTimeStep = dcp(model)
        modelList.append(modelThisTimeStep)

    totalDeaths = modelList[-1].getOutcome('thrive')
    print "total deaths:  ",totalDeaths







