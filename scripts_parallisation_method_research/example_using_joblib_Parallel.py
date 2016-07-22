# -*- coding: utf-8 -*-
"""
Created on Thu Jul 21 14:03:42 2016

@author: ruth
"""
def runOnce(MCSampleSize, xmin, args, interventionList, totalBudget, filename):        
    import asd as asd 
    import pickle 
    import numpy as np
    print ' ###############  RUNNING WITH TOTAL BUDGET: ',totalBudget,'  ###################'
    numInterventions = len(interventionList)
    scenarioMonteCarloOutput = []
    for r in range(0, MCSampleSize):
        proposalAllocation = np.random.rand(numInterventions)
        budgetBest, fval, exitflag, output = asd.asd(objectiveFunction, proposalAllocation, args, xmin = xmin, verbose = 2)  
        outputOneRun = OutputClass(budgetBest, fval, exitflag, output.iterations, output.funcCount, output.fval, output.x)        
        scenarioMonteCarloOutput.append(outputOneRun)   
    # find the best
    bestSample = scenarioMonteCarloOutput[0]
    for sample in range(0, len(scenarioMonteCarloOutput)):
        if scenarioMonteCarloOutput[sample].fval < bestSample.fval:
            bestSample = scenarioMonteCarloOutput[sample]
    # scale it and make a dictionary
    bestSampleBudget = bestSample.budgetBest
    bestSampleBudgetScaled = rescaleAllocation(totalBudget, bestSampleBudget)
    bestSampleBudgetScaledDict = {}
    for i in range(0, len(interventionList)):
        intervention = interventionList[i]
        bestSampleBudgetScaledDict[intervention] = bestSampleBudgetScaled[i]      
    # put it in a file    
    outfile = open(filename, 'wb')
    pickle.dump(bestSampleBudgetScaledDict, outfile)
    outfile.close()  
    
    
def getCostCoverageInfo(dataSpreadsheetName, keyList):
    import data 
    from copy import deepcopy as dcp
    spreadsheetData = data.readSpreadsheet(dataSpreadsheetName, keyList)        
    costCoverageInfo = {}
    for intervention in spreadsheetData.interventionList:
        costCoverageInfo[intervention] = {}
        costCoverageInfo[intervention]['unitcost']   = dcp(spreadsheetData.costSaturation[intervention]["unit cost"])
        costCoverageInfo[intervention]['saturation'] = dcp(spreadsheetData.costSaturation[intervention]["saturation coverage"])
    return costCoverageInfo
    
def getInitialTargetPopSize(dataSpreadsheetName, helper):
    import data 
    spreadsheetData = data.readSpreadsheet(dataSpreadsheetName, helper.keyList)        
    mothers = helper.makePregnantWomen(spreadsheetData) 
    numAgeGroups = len(helper.keyList['ages'])
    agePopSizes  = helper.makeAgePopSizes(spreadsheetData)  
    targetPopSize = {}
    for intervention in spreadsheetData.interventionList:
        targetPopSize[intervention] = 0.
        for iAge in range(numAgeGroups):
            ageName = helper.keyList['ages'][iAge]
            targetPopSize[intervention] += spreadsheetData.targetPopulation[intervention][ageName] * agePopSizes[iAge]
        targetPopSize[intervention] += spreadsheetData.targetPopulation[intervention]['pregnant women'] * mothers.populationSize
    return targetPopSize    

def getTotalInitialAllocation(data, costCoverageInfo, targetPopSize):
    import costcov
    from copy import deepcopy as dcp
    costCov = costcov.Costcov()
    allocation = []
    for intervention in data.interventionList:
        coverageFraction = dcp(data.coverage[intervention])
        coverageNumber = coverageFraction * targetPopSize[intervention]
        if coverageNumber == 0:
            spending = 0.
        else:
            spending = costCov.inversefunction(coverageNumber, costCoverageInfo[intervention], targetPopSize[intervention])  
        allocation.append(spending)
    return allocation

def rescaleAllocation(totalBudget, proposalAllocation):
    scaleRatio = totalBudget / sum(proposalAllocation)
    rescaledAllocation = [x * scaleRatio for x in proposalAllocation]
    return rescaledAllocation 
    
def getTargetPopSizeFromModelInstance(dataSpreadsheetName, keyList, model):    
    import data 
    spreadsheetData = data.readSpreadsheet(dataSpreadsheetName, keyList)        
    numAgeGroups = len(keyList['ages'])
    targetPopSize = {}
    for intervention in spreadsheetData.interventionList:
        targetPopSize[intervention] = 0.
        for iAge in range(numAgeGroups):
            ageName = keyList['ages'][iAge]
            targetPopSize[intervention] += spreadsheetData.targetPopulation[intervention][ageName] * model.listOfAgeCompartments[iAge].getTotalPopulation()
        targetPopSize[intervention] += spreadsheetData.targetPopulation[intervention]['pregnant women'] * model.pregnantWomen.populationSize
    return targetPopSize    

def objectiveFunction(proposalAllocation, totalBudget, costCoverageInfo, optimise, numModelSteps, dataSpreadsheetName, data):
    import helper 
    import costcov
    helper = helper.Helper()
    costCov = costcov.Costcov()
    model, derived, params = helper.setupModelConstantsParameters(data)
    if sum(proposalAllocation) == 0: 
        scaledproposalAllocation = proposalAllocation
    else:    
        scaledproposalAllocation = rescaleAllocation(totalBudget, proposalAllocation)
    # run the model
    timestepsPre = 12
    for t in range(timestepsPre):
        model.moveOneTimeStep()    
    # update coverages after 1 year   
    targetPopSize = getTargetPopSizeFromModelInstance(dataSpreadsheetName, helper.keyList, model)   
    newCoverages = {}    
    for i in range(0, len(data.interventionList)):
        intervention = data.interventionList[i]
        newCoverages[intervention] = costCov.function(scaledproposalAllocation[i], costCoverageInfo[intervention], targetPopSize[intervention]) / targetPopSize[intervention]
    model.updateCoverages(newCoverages)
    for t in range(numModelSteps - timestepsPre):
        model.moveOneTimeStep()
    if optimise == 'deaths':    
        performanceMeasure = model.getTotalCumulativeDeaths()
    if optimise == 'stunting':        
        performanceMeasure = model.getCumulativeAgingOutStunted()
    return performanceMeasure    
    
class OutputClass:
    def __init__(self, budgetBest, fval, exitflag, cleanOutputIterations, cleanOutputFuncCount, cleanOutputFvalVector, cleanOutputXVector):
        self.budgetBest = budgetBest
        self.fval = fval
        self.exitflag = exitflag
        self.cleanOutputIterations = cleanOutputIterations
        self.cleanOutputFuncCount = cleanOutputFuncCount
        self.cleanOutputFvalVector = cleanOutputFvalVector
        self.cleanOutputXVector = cleanOutputXVector      
        
def cascadeFunc(cascadeValue):
    print '############ CASCADE VALUE:  ', cascadeValue,'  #################'
    totalBudget = currentTotalBudget * cascadeValue
    args = {'totalBudget':totalBudget, 'costCoverageInfo':costCoverageInfo, 'optimise':optimise, 'numModelSteps':numModelSteps, 'dataSpreadsheetName':dataSpreadsheetName, 'data':spreadsheetData}    
    runOnce(MCSampleSize, xmin, args, spreadsheetData.interventionList, totalBudget, filename+str(cascadeValue)+'.pkl')                   

import helper       
dataSpreadsheetName = 'input_spreadsheets/Bangladesh/subregionSpreadsheets/Barisal.xlsx'
numModelSteps = 24
helper = helper.Helper()
cascadeValues = [0.25, 0.5]
MCSampleSize = 1
filename = 'parallel_test'
optimise = 'deaths'

from joblib import Parallel, delayed
import data 
spreadsheetData = data.readSpreadsheet(dataSpreadsheetName, helper.keyList)        
costCoverageInfo = getCostCoverageInfo(dataSpreadsheetName, helper.keyList)  
initialTargetPopSize = getInitialTargetPopSize(dataSpreadsheetName, helper)          
initialAllocation = getTotalInitialAllocation(spreadsheetData, costCoverageInfo, initialTargetPopSize)
currentTotalBudget = sum(initialAllocation)
xmin = [0.] * len(initialAllocation)

Parallel(n_jobs=2)(delayed(cascadeFunc)(cascadeValue) for cascadeValue in cascadeValues)

#for cascade in cascadeValues:
#    print '############ CASCADE VALUE:  ', cascade,'  #################'
#    totalBudget = currentTotalBudget * cascade
#    args = {'totalBudget':totalBudget, 'costCoverageInfo':costCoverageInfo, 'optimise':optimise, 'numModelSteps':numModelSteps, 'dataSpreadsheetName':dataSpreadsheetName, 'data':spreadsheetData}    
#    runOnce(MCSampleSize, xmin, args, spreadsheetData.interventionList, totalBudget, filename+str(cascade)+'.pkl')    

    
    