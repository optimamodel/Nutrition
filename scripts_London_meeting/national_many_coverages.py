'''Produces outcomes of running the model for a given set of coverages'''

rootpath = '..'
import os, sys
import helper
import data
from copy import deepcopy as dcp
import pandas as pd
import costcov
import csv
from optimisation import getTargetPopSizeFromModelInstance


def getCostCoverageInfo(dataSpreadsheetName, keyList):
    import data
    from copy import deepcopy as dcp
    spreadsheetData = data.readSpreadsheet(dataSpreadsheetName, keyList)
    costCoverageInfo = {}
    for intervention in spreadsheetData.interventionList:
        costCoverageInfo[intervention] = {}
        costCoverageInfo[intervention]['unitcost'] = dcp(spreadsheetData.costSaturation[intervention]["unit cost"])
        costCoverageInfo[intervention]['saturation'] = dcp(
            spreadsheetData.costSaturation[intervention]["saturation coverage"])
    return costCoverageInfo

def getCoverageFromCostCurve(modelList, spreadsheetPath, helper, newCoverages, outcomeList):
    # ABSOLUTE NUMBER CHILDREN COVERED
    # This assumes that it is the target population size at the time of scaling interventions (i.e. after 12 months)
    modelInstance = modelList[11]
    targetPopSizes = getTargetPopSizeFromModelInstance(spreadsheetPath, helper.keyList, modelInstance)
    interventionList = newCoverages.keys()
    coverageThisIntervention = {}
    for intervention in interventionList:
        coverageThisIntervention[intervention] = targetPopSizes[intervention] * newCoverages[intervention]
    # get coverage accross all interventions
    totalCoverageAllInterventions = sum(coverageThisIntervention.values())
    outcomeList += [totalCoverageAllInterventions]
    return outcomeList, coverageThisIntervention

def getCostOfCoverage(modelList, spreadsheetPath, interventionList, helper, coverageThisIntervention, outcomeList):
    # This is the cost of covering the people calculated above (using inverse cost-coverage curve)
    import costcov
    costCov = costcov.Costcov()
    modelInstance = modelList[11]
    targetPopSizes = getTargetPopSizeFromModelInstance(spreadsheetPath, helper.keyList, modelInstance)
    costThisIntervention = {}
    costCoverageInfo = getCostCoverageInfo(spreadsheetPath, helper.keyList)
    for intervention in interventionList:
        costThisIntervention[intervention] = costCov.inversefunction(coverageThisIntervention[intervention],
                                                                     costCoverageInfo[intervention],
                                                                     targetPopSizes[intervention])
    # get cost across all interventions
    totalCostAllInterventions = sum(costThisIntervention.values())
    outcomeList += [totalCostAllInterventions]

    return outcomeList


def getOutcomesAllSameCoverage(spreadsheetData, newCoverages, spreadsheetPath):
    import helper
    helper = helper.Helper()
    outcomeList = []
    outcomeList += ['All']
    outcomeList += [newCoverages['Vitamin A supplementation']]

    # set up model
    model, derived, params = helper.setupModelDerivedParameters(spreadsheetData)

    modelList = []
    # prep model with current coverages
    timestepsPre = 12
    for t in range(timestepsPre):
        model.moveOneTimeStep()
        modelThisTimeStep = dcp(model)
        modelList.append(modelThisTimeStep)

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

    # get target pop size and cost of coverage
    outcomeList, coverageThisIntervention = getCoverageFromCostCurve(modelList, spreadsheetPath, helper, newCoverages, outcomeList)
    interventionList = ['Balanced energy-protein supplementation', 'Vitamin A supplementation',
                        'Public provision of complementary foods', 'Breastfeeding promotion',
                        'Antenatal micronutrient supplementation', 'Complementary feeding education']
    outcomeList = getCostOfCoverage(modelList, spreadsheetPath, interventionList, helper, coverageThisIntervention, outcomeList)

    return outcomeList

def getOutcomesAllCurrentCoverage(spreadsheetData, spreadsheetPath):
    import helper
    helper = helper.Helper()
    outcomeList = []
    outcomeList += ['All']
    outcomeList += ['current']
    # set up model
    model, derived, params = helper.setupModelDerivedParameters(spreadsheetData)

    modelList = []
    # prep model with current coverages
    timestepsPre = 12
    for t in range(timestepsPre):
        model.moveOneTimeStep()
        modelThisTimeStep = dcp(model)
        modelList.append(modelThisTimeStep)

    newCoverages = dcp(model.params.coverage)

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

    # get target pop size and cost of coverage
    outcomeList, coverageThisIntervention = getCoverageFromCostCurve(modelList, spreadsheetPath, helper, newCoverages, outcomeList)
    interventionList = ['Balanced energy-protein supplementation', 'Vitamin A supplementation',
                        'Public provision of complementary foods', 'Breastfeeding promotion',
                        'Antenatal micronutrient supplementation', 'Complementary feeding education']
    outcomeList = getCostOfCoverage(modelList, spreadsheetPath, interventionList, helper, coverageThisIntervention, outcomeList)


    return outcomeList

def getOutcomesScaledFromCurrent(spreadsheetData, scaledCoverages, spreadsheetPath):
    import helper
    helper = helper.Helper()
    rows = []
    interventionList = ['Balanced energy-protein supplementation', 'Vitamin A supplementation',
                        'Public provision of complementary foods', 'Breastfeeding promotion',
                        'Antenatal micronutrient supplementation', 'Complementary feeding education']
    for intervention in interventionList:
        outcomeList = []
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

        newCoverages = dcp(model.params.coverage)
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


        # get target pop size and cost of coverage
        outcomeList, coverageThisIntervention = getCoverageFromCostCurve(modelList, spreadsheetPath, helper,
                                                                         newCoverages, outcomeList)

        outcomeList = getCostOfCoverage(modelList, spreadsheetPath, interventionList, helper, coverageThisIntervention,
                                        outcomeList)
        rows.append(outcomeList)

    return rows

def getOutcomesScaledFromZero(spreadsheetData, scaledCoverages, spreadsheetPath):
    import helper
    helper = helper.Helper()
    rows = []
    interventionList = ['Balanced energy-protein supplementation', 'Vitamin A supplementation',
                        'Public provision of complementary foods', 'Breastfeeding promotion',
                        'Antenatal micronutrient supplementation', 'Complementary feeding education']
    for intervention in interventionList:
        outcomeList = []
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

        newCoverages = {interv: 0. for interv in interventionList}
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



        # get target pop size and cost of coverage
        outcomeList, coverageThisIntervention = getCoverageFromCostCurve(modelList, spreadsheetPath, helper,
                                                                         newCoverages, outcomeList)

        outcomeList = getCostOfCoverage(modelList, spreadsheetPath, interventionList, helper, coverageThisIntervention,
                                        outcomeList)
        rows.append(outcomeList)

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
            w.writerow(outcomeList)
    return
