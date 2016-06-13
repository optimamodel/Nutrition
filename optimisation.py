# -*- coding: utf-8 -*-
"""
Created on Wed Jun  8 13:58:29 2016

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
            spending = 0
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
    model, constants, params = helper.setupModelConstantsParameters('optimisation model', mothers, timestep, agingRateList, agePopSizes, keyList, spreadsheetData)
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
helper = helper.Helper()
costCov = costcov.Costcov()
dataSpreadsheetName = 'InputForCode_Bangladesh.xlsx'
timestep = 1./12. 
numsteps = 168  
ages = ["<1 month", "1-5 months", "6-11 months", "12-23 months", "24-59 months"]
birthOutcomes = ["Pre-term SGA", "Pre-term AGA", "Term SGA", "Term AGA"]
wastingList = ["normal", "mild", "moderate", "high"]
stuntingList = ["normal", "mild", "moderate", "high"]
breastfeedingList = ["exclusive", "predominant", "partial", "none"]
keyList = [ages, birthOutcomes, wastingList, stuntingList, breastfeedingList]
spreadsheetData = dataCode.getDataFromSpreadsheet(dataSpreadsheetName, keyList)
mothers = helper.makePregnantWomen(spreadsheetData)
mothers['annualPercentPopGrowth'] = 0.03
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
xmin = [0.] * len(initialAllocation)
optimise = 'deaths' # choose between 'deaths' and 'stunting'
args = {'totalBudget':totalBudget, 'costCoverageInfo':costCoverageInfo, 'optimise':optimise, 'mothers':mothers, 'timestep':timestep, 'agingRateList':agingRateList, 'agePopSizes':agePopSizes, 'keyList':keyList, 'data':spreadsheetData}    
budgetBest, fval, exitflag, output = asd.asd(objectiveFunction, initialAllocation, args, xmin = xmin)  #MaxFunEvals = 10            

scaledInitialAllocation = rescaleAllocation(totalBudget, initialAllocation)
scaledBudgetBest = rescaleAllocation(totalBudget, budgetBest)
budgetDictBefore = {}
budgetDictAfter = {}  
finalCoverage = {}
i = 0        
for intervention in spreadsheetData.interventionList:
    budgetDictBefore[intervention] = scaledInitialAllocation[i]
    budgetDictAfter[intervention] = scaledBudgetBest[i]  
    finalCoverage[intervention] = costCov.function(array([scaledBudgetBest[i]]), costCoverageInfo[intervention], targetPopSize[intervention]) / targetPopSize[intervention]
    i += 1        
    
outputPlot.getBudgetPieChartComparison(budgetDictBefore, budgetDictAfter, optimise, output.fval[0], output.fval[len(output.fval)-1])    




       