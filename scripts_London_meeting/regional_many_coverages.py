'''Produces outcomes of running the model for a given set of coverages in regions'''

rootpath = '..'
import os, sys
import helper
import data
from copy import deepcopy as dcp
import pandas as pd
import costcov
import csv
from optimisation import getTargetPopSizeFromModelInstance

def getOutcomesGivenCoverage(spreadsheetData, interventionList, baselineCoverages, scaledCoverages, helper, allIdentical):
    rows = []
    for intervention in interventionList:
        outcomeList = []
        if allIdentical:
            outcomeList += ['All']
            outcomeList += [baselineCoverages[intervention]]
            rows = []
        else:
            outcomeList += [intervention]
            outcomeList += [scaledCoverages[intervention]]

        # set up model
        model, derived, params = helper.setupModelDerivedParameters(spreadsheetData)

        modelList = []
        # prep model with current coverages
        timestepsPre = 12
        for t in range(timestepsPre):
            model.moveOneTimeStep()
            modelThisTimeStep = dcp(model)
            modelList.append(modelThisTimeStep)

        # scale up intervention one at a time from baseline coverage. If scale=baseline then interventions not scaled
        newCoverages = dcp(baselineCoverages)
        newCoverages[intervention] = scaledCoverages[intervention]
        model.updateCoverages(newCoverages)

        timesteps = 180
        for t in range(timesteps - timestepsPre):
            model.moveOneTimeStep()
            modelThisTimeStep = dcp(model)
            modelList.append(modelThisTimeStep)

        # GET OUTCOMES #TODO: subtract first year?
        totalDeaths = modelList[-1].getOutcome('deaths')
        totalStunted = modelList[-1].getOutcome('stunting')
        totalThrive = modelList[-1].getOutcome('thrive')
        totalStuntedPrev = modelList[-1].getOutcome('stunting prev')
        outcomeList += [totalDeaths, totalStunted, totalThrive, totalStuntedPrev]

        rows.append(outcomeList)
        # TODO: pop size? total costs?

    return rows

def writeToCSV(outfileName, outcomeList, rows):
    headings = ['intervention', 'coverage', 'total deaths', 'total stunting', 'total thriving', 'stunting prevalence',
                'number people covered', 'total cost']
    with open(outfileName, 'wb') as f:
        w = csv.writer(f)
        w.writerow(headings)
        if rows:
            w.writerows(outcomeList)
        else: # only 1 row
            w.writerows(outcomeList)
    return


moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)
helper = helper.Helper()

country = 'Bangladesh'
regionNames = ['Barisal', 'Chittagong', 'Dhaka', 'Khulna', 'Rajshahi', 'Rangpur', 'Sylhet']
date = '2017Jul'
spreadsheetDate = '2016Oct'

resultsPath = rootpath+'/Results/'+date+'/modeloutcomes_manycoverages/subregional/'
if not os.path.exists(resultsPath):
    os.makedirs(resultsPath)

for region in regionNames:
    dataSpreadsheetPath = rootpath+'/input_spreadsheets/London_spreadsheets/'+country+'/'+spreadsheetDate+'/subregionSpreadsheets/'+region+'.xlsx'
    coveragesSpreadsheetPath = rootpath+'/input_spreadsheets/London_spreadsheets/coverages/many_coverages.xlsx'

    # get all the data & coverages
    spreadsheetData = data.readSpreadsheet(dataSpreadsheetPath, helper.keyList)
    interventionList = spreadsheetData.interventionList

    baselineSheet = pd.read_excel(coveragesSpreadsheetPath, sheetname='baseline coverages', index_col=[0])
    baselineCoverages = {}
    for intervention in interventionList:
        baselineCoverages[intervention] = baselineSheet.loc[intervention, 'Coverage']

    scaledSheet = pd.read_excel(coveragesSpreadsheetPath, sheetname='scaled coverages', index_col=[0])
    scaledCoverages = {}
    for intervention in interventionList:
        scaledCoverages[intervention] = scaledSheet.loc[intervention, 'Coverage']

    rowsForBaseline = getOutcomesGivenCoverage(spreadsheetData, interventionList, baselineCoverages, baselineCoverages, helper, allIdentical =True)
    rowsForScaled = getOutcomesGivenCoverage(spreadsheetData, interventionList, baselineCoverages, scaledCoverages, helper, allIdentical=False)

    outfilename = resultsPath+'model_outcomes_'+region+'_baseline.csv'
    writeToCSV(outfilename, rowsForBaseline, rows=False)
    outfilename = resultsPath+'model_outcomes_'+region+'_scaled.csv'
    writeToCSV(outfilename, rowsForScaled, rows=True)



