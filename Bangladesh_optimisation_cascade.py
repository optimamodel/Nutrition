# -*- coding: utf-8 -*-
"""
Created on Fri Jun 17 13:56:23 2016

@author: ruth
"""

def getTotalInitialAllocation(data, costCoverageInfo, targetPopSize):
    import costcov
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
    import helper as helper
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
            
            
            
import data as dataCode
import helper as helper
import costcov
from copy import deepcopy as dcp
from numpy import array
import asd as asd
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


#  -------------     STUNTING    ----------------
print 'STUNTING'
optimise = 'stunting' # choose between 'deaths' and 'stunting'
cascadeOutputBudgetDictStunting = {}
for cascade in range(0.6, 3.0, 0.2):
    print 'CASCADE:  ' + str(cascade)

    filename = 'Bangladesh_stunting__cascade_'+str(cascade)+'.pkl'
    outfile = open(filename, 'wb')
    totalOutput = []
    for r in range(0, 50):
        print 'SAMPLE:  ' + str(r)
        totalBudget = currentTotalBudget * cascade
        args = {'verbose':0, 'totalBudget':totalBudget, 'costCoverageInfo':costCoverageInfo, 'optimise':optimise, 'mothers':mothers, 'timestep':timestep, 'agingRateList':agingRateList, 'agePopSizes':agePopSizes, 'keyList':keyList, 'data':spreadsheetData} 
        proposalAllocation = np.random.rand(numInterventions)
        budgetBest, fval, exitflag, output = asd.asd(objectiveFunction, proposalAllocation, args, xmin = xmin)
        outputDict = {'budgetBest':budgetBest, 'fval':fval, 'exitflag':exitflag, 'output':output}    
        totalOutput.append(outputDict)
        pickle.dump(outputDict, outfile)
    outfile.close() 
    
    # find the best
    bestOutput = totalOutput[0]
    for sample in range(0, len(totalOutput)):
        if totalOutput[sample]['fval'] < bestOutput['fval']:
            bestOutput = totalOutput[sample]
        
    
    bestOutputBudget = bestOutput['budgetBest']
    bestOutputBudgetScaled = rescaleAllocation(totalBudget, bestOutputBudget)
    cascadeOutputBudgetDictStunting[cascade] = bestOutputBudgetScaled

    filename = 'Bangladesh_cascadeOutputBudgetDictStunting.pkl'
    outfile = open(filename, 'wb')
    pickle.dump(cascadeOutputBudgetDictStunting, outfile)
    outfile.close() 
    
#  -------------     DEATHS    ----------------
print 'DEATHS'
optimise = 'deaths' # choose between 'deaths' and 'stunting'
cascadeOutputBudgetDictDeaths = {}
for cascade in range(0.6, 3.0, 0.2):
    print 'CASCADE:  ' + str(cascade)

    filename = 'Bangladesh_deaths__cascade_'+str(cascade)+'.pkl'
    outfile = open(filename, 'wb')
    totalOutputD = []
    for r in range(0, 50):
        print 'SAMPLE:  ' + str(r)
        totalBudget = currentTotalBudget * cascade
        args = {'verbose':0, 'totalBudget':totalBudget, 'costCoverageInfo':costCoverageInfo, 'optimise':optimise, 'mothers':mothers, 'timestep':timestep, 'agingRateList':agingRateList, 'agePopSizes':agePopSizes, 'keyList':keyList, 'data':spreadsheetData} 
        proposalAllocation = np.random.rand(numInterventions)
        budgetBest, fval, exitflag, output = asd.asd(objectiveFunction, proposalAllocation, args, xmin = xmin)
        outputDict = {'budgetBest':budgetBest, 'fval':fval, 'exitflag':exitflag, 'output':output}    
        totalOutputD.append(outputDict)
        pickle.dump(outputDict, outfile)
    outfile.close() 
    
    # find the best
    bestOutput = totalOutputD[0]
    for sample in range(0, len(totalOutputD)):
        if totalOutputD[sample]['fval'] < bestOutput['fval']:
            bestOutput = totalOutputD[sample]
        
    
    bestOutputBudget = bestOutput['budgetBest']
    bestOutputBudgetScaled = rescaleAllocation(totalBudget, bestOutputBudget)
    cascadeOutputBudgetDictDeaths[cascade] = bestOutputBudgetScaled

    filename = 'Bangladesh_cascadeOutputBudgetDictDeaths.pkl'
    outfile = open(filename, 'wb')
    pickle.dump(cascadeOutputBudgetDictDeaths, outfile)
    outfile.close()









#scaledBudgetBest = rescaleAllocation(totalBudget, budgetBest)
#rescaledProposalAllocation = rescaleAllocation(totalBudget, proposalAllocation)
#budgetDictBefore = {}
#budgetDictAfter = {}  
#finalCoverage = {}
#initialCoverage = {}
#i = 0        
#for intervention in spreadsheetData.interventionList:
#    budgetDictBefore[intervention] = rescaledProposalAllocation[i][0]
#    budgetDictAfter[intervention] = scaledBudgetBest[i][0]  
#    finalCoverage[intervention] = costCov.function(array([scaledBudgetBest[i]]), costCoverageInfo[intervention], targetPopSize[intervention]) / targetPopSize[intervention]
#    initialCoverage[intervention] = costCov.function(array([rescaledProposalAllocation[i]]), costCoverageInfo[intervention], targetPopSize[intervention]) / targetPopSize[intervention]
#    i += 1        
    

