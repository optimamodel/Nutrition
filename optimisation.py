# -*- coding: utf-8 -*-
"""
Created on Wed Jun  8 13:58:29 2016

@author: ruth
"""
def getTotalInitialAllocation(data, costCoverageInfo, targetPopSize):
    import costcov
    from numpy import array
    from copy import deepcopy as dcp
    costCov = costcov.Costcov()
    allocation = []
    for intervention in data.interventionList:
        coverageFraction = array([dcp(data.interventionCoveragesCurrent[intervention])])
        coverageNumber = coverageFraction * targetPopSize[intervention]
        if coverageNumber == 0:
            spending = array([0.])
        else:
            spending = costCov.inversefunction(coverageNumber, costCoverageInfo[intervention], targetPopSize[intervention])  
        allocation.append(spending)
    return allocation

def rescaleAllocation(totalBudget, proposalAllocation):
    scaleRatio = totalBudget / sum(proposalAllocation)
    rescaledAllocation = [x * scaleRatio for x in proposalAllocation]
    return rescaledAllocation 

def objectiveFunction(proposalAllocation, totalBudget, costCoverageInfo, optimise, mothers, timestep, numModelSteps, targetPopSize, agingRateList, agePopSizes, keyList, data):
    import helper as helper
    import costcov
    from numpy import array
    helper = helper.Helper()
    costCov = costcov.Costcov()
    model, constants, params = helper.setupModelConstantsParameters('optimisation model', mothers, timestep, agingRateList, agePopSizes, keyList, data)
    if sum(proposalAllocation) == 0: 
        scaledproposalAllocation = proposalAllocation
    else:    
        scaledproposalAllocation = rescaleAllocation(totalBudget, proposalAllocation)
    # calculate coverage (%)
    newCoverages = {}    
    for i in range(0, len(data.interventionList)):
        intervention = data.interventionList[i]
        newCoverages[intervention] = costCov.function(array([scaledproposalAllocation[i]]), costCoverageInfo[intervention], targetPopSize[intervention]) / targetPopSize[intervention]
    # run the model
    timestepsPre = 12
    for t in range(timestepsPre):
        model.moveOneTimeStep()    
    # update coverages after 1 year    
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
            
            
class Optimisation:
    def __init__(self, dataSpreadsheetName, timestep, numModelSteps, ages, birthOutcomes, wastingList, stuntingList, breastfeedingList, ageGroupSpans, agingRateList):
        self.dataSpreadsheetName = dataSpreadsheetName
        self.timestep = timestep
        self.numModelSteps = numModelSteps
        self.ages = ages
        self.birthOutcomes = birthOutcomes
        self.wastingList = wastingList
        self.stuntingList = stuntingList
        self.breastfeedingList = breastfeedingList
        self.ageGroupSpans = ageGroupSpans
        self.agingRateList = agingRateList
        
    def performSingleOptimisation(self, optimise, MCSampleSize, filename):
        import data as dataCode
        import helper as helper
        from copy import deepcopy as dcp
        from numpy import array
        helper = helper.Helper()
        keyList = [self.ages, self.birthOutcomes, self.wastingList, self.stuntingList, self.breastfeedingList]
        spreadsheetData = dataCode.getDataFromSpreadsheet(self.dataSpreadsheetName, keyList)        
        mothers = helper.makePregnantWomen(spreadsheetData) 
        numAgeGroups = len(self.ages)
        agePopSizes  = helper.makeAgePopSizes(numAgeGroups, self.ageGroupSpans, spreadsheetData)  
        targetPopSize = {}
        costCoverageInfo = {}
        for intervention in spreadsheetData.interventionList:
            targetPopSize[intervention] = 0.
            costCoverageInfo[intervention] = {}
            for ageInd in range(numAgeGroups):
                age = self.ages[ageInd]
                targetPopSize[intervention] += spreadsheetData.interventionTargetPop[intervention][age] * agePopSizes[ageInd]
            targetPopSize[intervention] += spreadsheetData.interventionTargetPop[intervention]['pregnant women'] * mothers['populationSize']
            costCoverageInfo[intervention]['unitcost']   = array([dcp(spreadsheetData.interventionCostCoverage[intervention]["unit cost"])])
            costCoverageInfo[intervention]['saturation'] = array([dcp(spreadsheetData.interventionCostCoverage[intervention]["saturation coverage"])])
        
        initialAllocation = getTotalInitialAllocation(spreadsheetData, costCoverageInfo, targetPopSize)
        totalBudget = sum(initialAllocation)
        xmin = [0.] * len(initialAllocation)
        args = {'totalBudget':totalBudget, 'costCoverageInfo':costCoverageInfo, 'optimise':optimise, 'mothers':mothers, 'timestep':self.timestep, 'numModelSteps':self.numModelSteps, 'targetPopSize':targetPopSize, 'agingRateList':self.agingRateList, 'agePopSizes':agePopSizes, 'keyList':keyList, 'data':spreadsheetData}    
        self.runOnce(MCSampleSize, xmin, args, spreadsheetData.interventionList, totalBudget, filename+'.pkl')
        
        
    def performCascadeOptimisation(self, optimise, MCSampleSize, filename, cascadeValues):
        import data as dataCode
        import helper as helper
        from copy import deepcopy as dcp
        from numpy import array
        helper = helper.Helper()
        keyList = [self.ages, self.birthOutcomes, self.wastingList, self.stuntingList, self.breastfeedingList]
        spreadsheetData = dataCode.getDataFromSpreadsheet(self.dataSpreadsheetName, keyList)        
        mothers = helper.makePregnantWomen(spreadsheetData) 
        numAgeGroups = len(self.ages)
        agePopSizes  = helper.makeAgePopSizes(numAgeGroups, self.ageGroupSpans, spreadsheetData)  
        targetPopSize = {}
        costCoverageInfo = {}
        for intervention in spreadsheetData.interventionList:
            targetPopSize[intervention] = 0.
            costCoverageInfo[intervention] = {}
            for ageInd in range(numAgeGroups):
                age = self.ages[ageInd]
                targetPopSize[intervention] += spreadsheetData.interventionTargetPop[intervention][age] * agePopSizes[ageInd]
            targetPopSize[intervention] += spreadsheetData.interventionTargetPop[intervention]['pregnant women'] * mothers['populationSize']
            costCoverageInfo[intervention]['unitcost']   = array([dcp(spreadsheetData.interventionCostCoverage[intervention]["unit cost"])])
            costCoverageInfo[intervention]['saturation'] = array([dcp(spreadsheetData.interventionCostCoverage[intervention]["saturation coverage"])])
            
        initialAllocation = getTotalInitialAllocation(spreadsheetData, costCoverageInfo, targetPopSize)
        currentTotalBudget = sum(initialAllocation)
        xmin = [0.] * len(initialAllocation)
        
        for cascade in cascadeValues:
            totalBudget = currentTotalBudget * cascade
            args = {'totalBudget':totalBudget, 'costCoverageInfo':costCoverageInfo, 'optimise':optimise, 'mothers':mothers, 'timestep':self.timestep, 'numModelSteps':self.numModelSteps, 'targetPopSize':targetPopSize, 'agingRateList':self.agingRateList, 'agePopSizes':agePopSizes, 'keyList':keyList, 'data':spreadsheetData}    
            self.runOnce(MCSampleSize, xmin, args, spreadsheetData.interventionList, totalBudget, filename+str(cascade)+'.pkl')    

        
    def runOnce(self, MCSampleSize, xmin, args, interventionList, totalBudget, filename):        
        import asd as asd 
        import pickle as pickle
        import numpy as np
        numInterventions = len(interventionList)
        scenarioMonteCarloOutput = []
        for r in range(0, MCSampleSize):
            proposalAllocation = np.random.rand(numInterventions)
            budgetBest, fval, exitflag, output = asd.asd(objectiveFunction, proposalAllocation, args, xmin = xmin, verbose = 0)  
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
        