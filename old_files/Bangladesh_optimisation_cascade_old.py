# -*- coding: utf-8 -*-
"""
Created on Fri Jun 24 12:21:51 2016

@author: ruth
"""

class OutputClass:
    def __init__(self, budgetBest, fval, exitflag, cleanOutputIterations, cleanOutputFuncCount, cleanOutputFvalVector, cleanOutputXVector):
        self.budgetBest = budgetBest
        self.fval = fval
        self.exitflag = exitflag
        self.cleanOutputIterations = cleanOutputIterations
        self.cleanOutputFuncCount = cleanOutputFuncCount
        self.cleanOutputFvalVector = cleanOutputFvalVector
        self.cleanOutputXVector = cleanOutputXVector

def getTotalInitialAllocation(data, costCoverageInfo, targetPopSize):
    from old_files import costcov
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

def objectiveFunction(proposalAllocation, totalBudget, costCoverageInfo, optimise, mothers, timestep, agingRateList, agePopSizes, keyList, data):
    from numpy import array
    helper = helper.Helper()
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
    model.updateCoverages(newCoverages)
    for t in range(numsteps):
        model.moveOneTimeStep()
    if optimise == 'deaths':    
        performanceMeasure = model.getTotalCumulativeDeaths()
    if optimise == 'stunting':        
        performanceMeasure = model.getCumulativeAgingOutStunted()
    return performanceMeasure


from nutrition import data as dataCode, asd as asd
from old_files import costcov, helper as helper
from copy import deepcopy as dcp
from numpy import array
import numpy as np
import pickle as pickle
helper = helper.Helper()
costCov = costcov.Costcov()
dataSpreadsheetName = 'InputForCode_Bangladesh.xlsx'
timestep = 1./12. 
numsteps = 180
ages = ["<1 month", "1-5 months", "6-11 months", "12-23 months", "24-59 months"]
birthOutcomes = ["Pre-term SGA", "Pre-term AGA", "Term SGA", "Term AGA"]
wastingList = ["normal", "mild", "moderate", "high"]
stuntingList = ["normal", "mild", "moderate", "high"]
breastfeedingList = ["exclusive", "predominant", "partial", "none"]
keyList = [ages, birthOutcomes, wastingList, stuntingList, breastfeedingList]
spreadsheetData = dataCode.getDataFromSpreadsheet(dataSpreadsheetName, keyList)
mothers = helper.makePregnantWomen(spreadsheetData)
mothers['annualPercentPopGrowth'] = - 0.01
ageGroupSpans = [1., 5., 6., 12., 36.] # number of months in each age group
agingRateList = [1./1., 1./5., 1./6., 1./12., 1./36.] # fraction of people aging out per MONTH (WARNING use ageSpans to define this)
numAgeGroups = len(ages)
agePopSizes  = helper.makeAgePopSizes(numAgeGroups, ageGroupSpans, spreadsheetData)
targetPopSize = {}
costCoverageInfo = {}
for intervention in spreadsheetData.interventionList:
    targetPopSize[intervention] = 0.
    costCoverageInfo[intervention] = {}
    for ageInd in range(numAgeGroups):
        age = ages[ageInd]
        targetPopSize[intervention] += spreadsheetData.interventionTargetPop[intervention][age] * agePopSizes[ageInd]
    targetPopSize[intervention] += spreadsheetData.interventionTargetPop[intervention]['pregnant women'] * mothers['populationSize']
    costCoverageInfo[intervention]['unitcost']   = array([dcp(spreadsheetData.interventionCostCoverage[intervention]["unit cost"])])
    costCoverageInfo[intervention]['saturation'] = array([dcp(spreadsheetData.interventionCostCoverage[intervention]["saturation coverage"])])
    
initialAllocation = getTotalInitialAllocation(spreadsheetData, costCoverageInfo, targetPopSize)
currentTotalBudget = sum(initialAllocation)
xmin = [0.] * len(initialAllocation)
numInterventions = len(initialAllocation)
MCSampleSize = 25
cascadeValues = [0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 4.0]  


for optimise in ['stunting', 'deaths']:

    print optimise
    cascadeBudget = {}
    for cascade in cascadeValues:
        print 'CASCADE:  ' + str(cascade)
    
        #filename = 'Bangladesh_cascade_output_'+str(cascade)+'_'+optimise+'.pkl'
        #outfile = open(filename, 'wb')
        scenarioMonteCarloOutput = []
        for r in range(0, MCSampleSize):
            print 'SAMPLE:  ' + str(r)
            totalBudget = currentTotalBudget * cascade
            args = {'totalBudget':totalBudget, 'costCoverageInfo':costCoverageInfo, 'optimise':optimise, 'mothers':mothers, 'timestep':timestep, 'agingRateList':agingRateList, 'agePopSizes':agePopSizes, 'keyList':keyList, 'data':spreadsheetData} 
            proposalAllocation = np.random.rand(numInterventions)
            budgetBest, fval, exitflag, output = asd.asd(objectiveFunction, proposalAllocation, args, xmin = xmin, verbose = 0)
            outputOneRun = OutputClass(budgetBest, fval, exitflag, output.iterations, output.funcCount, output.fval, output.x)        
            scenarioMonteCarloOutput.append(outputOneRun)
            #pickle.dump(outputOneRun, outfile)
        #outfile.close() 
        
        # find the best
        bestSample = scenarioMonteCarloOutput[0]
        for sample in range(0, len(scenarioMonteCarloOutput)):
            if scenarioMonteCarloOutput[sample].fval < bestSample.fval:
                bestSample = scenarioMonteCarloOutput[sample]
            
        # scale it and make a dictionary
        bestSampleBudget = bestSample.budgetBest
        bestSampleBudgetScaled = rescaleAllocation(totalBudget, bestSampleBudget)
        bestSampleBudgetScaledDict = {}
        for i in range(0, len(spreadsheetData.interventionList)):
            intervention = spreadsheetData.interventionList[i]
            bestSampleBudgetScaledDict[intervention] = bestSampleBudgetScaled[i]  
        # put it in the cascade output
        cascadeBudget[cascade] = bestSampleBudgetScaledDict
        # save this cascade scenario dictionary of allocation to file
        filename = 'Bangladesh_cascade_dictionary'+str(cascade)+'_'+optimise+'.pkl'
        outfile = open(filename, 'wb')
        pickle.dump(bestSampleBudgetScaledDict, outfile)
        outfile.close() 
    # save full cascade to file
    filename = 'Bangladesh_full_cascade_dictionary_'+optimise+'.pkl'
    outfile = open(filename, 'wb')
    pickle.dump(cascadeBudget, outfile)
    outfile.close()     