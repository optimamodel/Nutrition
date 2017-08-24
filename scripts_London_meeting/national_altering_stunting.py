'''Increases stunting distributions across age groups by given intervals and runs model to check the outcomes'''

rootpath = '..'
import os, sys
import helper
import data
from national_many_coverages import getOutcomesScaledFromCurrent, getOutcomesAllCurrentCoverage, getOutcomesScaledFromZero, getOutcomesAllSameCoverage, writeToCSV
from copy import deepcopy as dcp

moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)
helper = helper.Helper()

country = 'Bangladesh'
date = '2017Jul'
spreadsheetDate = '2016Oct'

dataSpreadsheetPath = rootpath+'/input_spreadsheets/London_spreadsheets/'+country+'/'+spreadsheetDate+'/InputForCode_'+country+'.xlsx'
resultsPath = rootpath+'/Results/'+date+'/modeloutcomes_alteredStuntingAndCoverages/'
if not os.path.exists(resultsPath):
    os.makedirs(resultsPath)

# get all the data & coverages
spreadsheetData = data.readSpreadsheet(dataSpreadsheetPath, helper.keyList)
coveragesSpreadsheetPath = rootpath+'/input_spreadsheets/London_spreadsheets/coverages/many_coverages.xlsx'

interventionList = spreadsheetData.interventionList

# change the stunting distribution
ages = helper.keyList['ages']
stuntingList = helper.keyList['stuntingList']

newCoveragesDict = {'0%':{intervention: 0. for intervention in interventionList},
                    '80%':{intervention: 0.8 for intervention in interventionList}}
for increase in [-0.1, 0., 0.1, 0.2, 0.3, 0.4, 0.5]:
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
    print spreadsheetDataCopy.stuntingDistribution
    current = getOutcomesAllCurrentCoverage(spreadsheetDataCopy, dataSpreadsheetPath) # current coverages
    currentToEighty = getOutcomesScaledFromCurrent(spreadsheetDataCopy, newCoveragesDict['80%'], dataSpreadsheetPath) # scaling to 80% from current
    zeroToEighty = getOutcomesScaledFromZero(spreadsheetDataCopy, newCoveragesDict['80%'], dataSpreadsheetPath) # scaling to 80% from 0
    allEighty = getOutcomesAllSameCoverage(spreadsheetDataCopy, newCoveragesDict['80%'], dataSpreadsheetPath) # all at 80%
    allZero = getOutcomesAllSameCoverage(spreadsheetDataCopy, newCoveragesDict['0%'], dataSpreadsheetPath) # all at 0%

    outputFileName = resultsPath+'outcomes_Bangladesh_current_stuntingChange_' + str(increase) + '.csv'
    writeToCSV(outputFileName, current, False)
    outputFileName = resultsPath+'outcomes_Bangladesh_currentToEighty_stuntingChange_' + str(increase) + '.csv'
    writeToCSV(outputFileName, currentToEighty, True)
    outputFileName = resultsPath+'outcomes_Bangladesh_zeroToEighty_stuntingChange_' + str(increase) + '.csv'
    writeToCSV(outputFileName, zeroToEighty, True)
    outputFileName = resultsPath+'outcomes_Bangladesh_allEighty_stuntingChange_' + str(increase) + '.csv'
    writeToCSV(outputFileName, allEighty, False)
    outputFileName = resultsPath+'outcomes_Bangladesh_allzero_stuntingChange_' + str(increase) + '.csv'
    writeToCSV(outputFileName, allZero, False)








