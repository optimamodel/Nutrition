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


def inputFunctionForAsd(proposalBudget, totalBudget, costCoverageInfo, mothers, timestep, agingRateList, agePopSizes, keyList, data):
    import helper as helper
    from numpy import array
    helper = helper.Helper()
    
    print "calling function"
    
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
    performanceMeasure = model.listOfAgeCompartments[0].getCumulativeDeaths() # PLACE HOLDER 
    return performanceMeasure    
            
            
            
            
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
    targetPopSize[intervention] +=     spreadsheetData.interventionTargetPop[intervention]['pregnant women'] * model.fertileWomen.populationSize
    costCoverageInfo[intervention]['unitcost']   = array([dcp(spreadsheetData.interventionCostCoverage[intervention]["unit cost"])])
    costCoverageInfo[intervention]['saturation'] = array([dcp(spreadsheetData.interventionCostCoverage[intervention]["saturation coverage"])])
    # this is starting budget as vector   
    startingVector.append(costCoverageInfo[intervention]['unitcost'] * costCoverageInfo[intervention]['saturation'] * targetPopSize[intervention])
totalBudget = getTotalInitialBudget(spreadsheetData)
args = {'totalBudget':totalBudget, 'costCoverageInfo':costCoverageInfo, 'mothers':mothers, 'timestep':timestep, 'agingRateList':agingRateList, 'agePopSizes':agePopSizes, 'keyList':keyList, 'data':spreadsheetData}    
budgetBest, fval, exitflag, output = asd.asd(inputFunctionForAsd, startingVector, args)            
          