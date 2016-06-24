# -*- coding: utf-8 -*-
"""
Created on Thu Jun 23 13:34:12 2016

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
            
            
            
import output as outputPlot            
import data as dataCode
import helper as helper
import costcov
from copy import deepcopy as dcp
from numpy import array
import asd as asd
import numpy as np
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
totalBudget = sum(initialAllocation)
proposalAllocation = dcp(initialAllocation)

#proposalAllocation = [1., 1., 1., 1., 1., 1., 1.]
#proposalAllocation = [totalBudget/2., 0., totalBudget/2., 0., 0., 0.,0.]
#proposalAllocation = [invest-1000. if invest>2000. else 1000. for invest in initialAllocation]
#proposalAllocation = [totalBudget/len(initialAllocation)] * len(initialAllocation)

xmin = [0.] * len(initialAllocation)
#xmin = [100.] * len(initialAllocation)
#xmin  = [0.01*invest if invest>100. else 1. for invest in initialAllocation]

optimise = 'stunting' # choose between 'deaths' and 'stunting'
args = {'totalBudget':totalBudget, 'costCoverageInfo':costCoverageInfo, 'optimise':optimise, 'mothers':mothers, 'timestep':timestep, 'agingRateList':agingRateList, 'agePopSizes':agePopSizes, 'keyList':keyList, 'data':spreadsheetData}    

for r in range(0, 10):
    
    proposalAllocation = np.random.rand(7)

    budgetBest, fval, exitflag, output = asd.asd(objectiveFunction, proposalAllocation, args, xmin = xmin)  #MaxFunEvals = 10            
    
    scaledBudgetBest = rescaleAllocation(totalBudget, budgetBest)
    scaledproposalAllocation = rescaleAllocation(totalBudget, proposalAllocation)
    budgetDictBefore = {}
    budgetDictAfter = {}  
    initialCoverage = {}
    finalCoverage = {}
    i = 0        
    for intervention in spreadsheetData.interventionList:
        budgetDictBefore[intervention] = scaledproposalAllocation[i]#[0]
        budgetDictAfter[intervention] = scaledBudgetBest[i][0]  
        initialCoverage[intervention] = costCov.function(array([scaledproposalAllocation[i]]), costCoverageInfo[intervention], targetPopSize[intervention]) / targetPopSize[intervention]
        finalCoverage[intervention] = costCov.function(array([scaledBudgetBest[i]]), costCoverageInfo[intervention], targetPopSize[intervention]) / targetPopSize[intervention]
        i += 1        
        
        
    string = optimise+'_random_'+str(r)    
    outputPlot.getBudgetPieChartComparison(budgetDictBefore, budgetDictAfter, optimise, output.fval[0], fval[0][0], string+'_pie')    
    outputPlot.compareOptimisationOutput(budgetDictBefore, budgetDictAfter, initialCoverage, finalCoverage, optimise, string)



       
