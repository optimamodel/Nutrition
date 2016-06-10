# -*- coding: utf-8 -*-
"""
Created on Wed Jun  8 13:58:29 2016

@author: ruth
"""
def getTotalInitialBudget(data):
    totalBudget = 0
    for intervention in data.interventionList:
        unitCost = data.interventionCostCoverage[intervention]['unit cost']
        coverage = data.interventionCoveragesCurrent[intervention]
        totalPopulationU5 = data.demographics['population U5']
        totalBudget += unitCost * coverage * totalPopulationU5
    return totalBudget   

def rescaleBudget(totalBudget, proposalBudget):
        scaleRatio = totalBudget / sum(proposalBudget)
        rescaledBudget = [x * scaleRatio for x in proposalBudget]
        return rescaledBudget 

def inputFunctionForAsd(proposalBudget, totalBudget, costCoverageInfo, optimise, mothers, timestep, agingRateList, agePopSizes, keyList, data):
    import helper as helper
    from numpy import array
    helper = helper.Helper()
    
    def rescaleProposalBudget(totalBudget, proposalBudget):
        scaleRatio = totalBudget / sum(proposalBudget)
        rescaledProposalBudget = [x * scaleRatio for x in proposalBudget]
        return rescaledProposalBudget    
    
    model, constants, params = helper.setupModelConstantsParameters('optimisation model', mothers, timestep, agingRateList, agePopSizes, keyList, spreadsheetData)
    scaledProposalBudget = rescaleProposalBudget(totalBudget, proposalBudget)
    # calculate coverage (%)
    newCoverages = {}    
    i = 0
    for intervention in data.interventionList:
        newCoverages[intervention] = costCov.function(array([scaledProposalBudget[i]]), costCoverageInfo[intervention], targetPopSize[intervention]) / targetPopSize[intervention]
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
# this model created to calculate targetPopSizes
model, constants, params = helper.setupModelConstantsParameters('optimisation model', mothers, timestep, agingRateList, agePopSizes, keyList, spreadsheetData)
targetPopSize = {}
costCoverageInfo = {}
startingVector = []
for intervention in spreadsheetData.interventionList:
    targetPopSize[intervention] = 0.
    costCoverageInfo[intervention] = {}
    for ageInd in range(numAgeGroups):
        age = ages[ageInd]
        targetPopSize[intervention] += spreadsheetData.interventionTargetPop[intervention][age] * model.listOfAgeCompartments[ageInd].getTotalPopulation()
    targetPopSize[intervention] += spreadsheetData.interventionTargetPop[intervention]['pregnant women'] * model.fertileWomen.populationSize
    costCoverageInfo[intervention]['unitcost']   = array([dcp(spreadsheetData.interventionCostCoverage[intervention]["unit cost"])])
    costCoverageInfo[intervention]['saturation'] = array([dcp(spreadsheetData.interventionCostCoverage[intervention]["saturation coverage"])])
    # this is starting budget as vector   
    startingVector.append(costCoverageInfo[intervention]['unitcost'] * spreadsheetData.interventionCoveragesCurrent[intervention] * targetPopSize[intervention])
totalBudget = getTotalInitialBudget(spreadsheetData)
xmin = [0.] * len(startingVector)
optimise = 'deaths' # choose between 'deaths' and 'stunting'
args = {'totalBudget':totalBudget, 'costCoverageInfo':costCoverageInfo, 'optimise':optimise, 'mothers':mothers, 'timestep':timestep, 'agingRateList':agingRateList, 'agePopSizes':agePopSizes, 'keyList':keyList, 'data':spreadsheetData}    
budgetBest, fval, exitflag, output = asd.asd(inputFunctionForAsd, startingVector, args, xmin = xmin)  #MaxFunEvals = 10            

scaledStartingVector = rescaleBudget(totalBudget, startingVector)
scaledBudgetBest = rescaleBudget(totalBudget, budgetBest)
budgetDictBefore = {}
budgetDictAfter = {}  
i = 0        
for intervention in spreadsheetData.interventionList:
    budgetDictBefore[intervention] = scaledStartingVector[i]
    budgetDictAfter[intervention] = scaledBudgetBest[i]  
    i += 1        
    
outputPlot.getBudgetPieChartComparison(budgetDictBefore, budgetDictAfter)    