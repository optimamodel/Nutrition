# -*- coding: utf-8 -*-
"""
Created on Mon Nov  6 16:17:17 2017

@author: ruth
"""
import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '../../..')
sys.path.append(moduleDir)
import optimisation
import data
import helper
thisHelper = helper.Helper()
import csv

rootpath = '../../..'
country = 'Tanzania'
date = '2017Sep'
spreadsheetDate = '2017Sep'
spreadsheet = rootpath+'/input_spreadsheets/'+country+'/'+spreadsheetDate+'/InputForCode_'+country+'.xlsx'
numModelSteps = 180
optimise = 'dummy'
costCurveType = 'standard'
resultsFileStem = rootpath+'/Results/'+date+'/'+optimise+'/national/'+country
IYCF_cov = 0.15

        
# make a zero dictionary        
spreadsheetData = data.readSpreadsheet(spreadsheet, thisHelper.keyList)        
zeroSpending = {}    
for i in range(0, len(spreadsheetData.interventionList)):
    intervention = spreadsheetData.interventionList[i]
    zeroSpending[intervention] = 0.        
 
# zero scenario   
spreadsheetData = data.readSpreadsheet(spreadsheet, thisHelper.keyList)
outfilename = 'zero_spending_national.csv'  
header1 = ['thrive', 'deaths', 'stunting prev']  
with open(outfilename, "wb") as f:
    writer = csv.writer(f)
    writer.writerow(header1)
    thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, 'dummy', resultsFileStem, costCurveType)    
    customCoverages = spreadsheetData.coverage
    customCoverages['IYCF'] = IYCF_cov
    modelList = thisOptimisation.oneModelRunWithOutputCustomOptimised(zeroSpending, customCoverages)
    row =[modelList[numModelSteps-1].getOutcome('thrive'), modelList[numModelSteps-1].getOutcome('deaths'), modelList[numModelSteps-1].getOutcome('stunting prev')]
    writer.writerow(row)

# baseline 1 with IYCF manually scaled up
outfilename = 'baseline1_national.csv'  
header1 = ['thrive', 'deaths', 'stunting prev']  
with open(outfilename, "wb") as f:
    writer = csv.writer(f)
    writer.writerow(header1)
    thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, 'dummy', resultsFileStem, costCurveType)    
    modelList = thisOptimisation.oneModelRunWithOutputManuallyScaleIYCF(IYCF_cov)    
    row =[modelList[numModelSteps-1].getOutcome('thrive'), modelList[numModelSteps-1].getOutcome('deaths'), modelList[numModelSteps-1].getOutcome('stunting prev')]
    writer.writerow(row)
    
# baseline 2 with custom coverages
customCoverages = {'Vitamin A supplementation':0.9, 'Antenatal micronutrient supplementation':0.58, 'IYCF':0.65}
outfilename = 'baseline2_national.csv'  
header1 = ['thrive', 'deaths', 'stunting prev']  
with open(outfilename, "wb") as f:
    writer = csv.writer(f)
    writer.writerow(header1)
    thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, 'dummy', resultsFileStem, costCurveType)    
    modelList = thisOptimisation.oneModelRunWithOutputCustomCoverages(customCoverages)    
    row =[modelList[numModelSteps-1].getOutcome('thrive'), modelList[numModelSteps-1].getOutcome('deaths'), modelList[numModelSteps-1].getOutcome('stunting prev')]
    writer.writerow(row)    
    
    
# get spending for baseline 2 custom coverages in a csv
myHelper = helper.Helper()
thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, 'dummy', resultsFileStem, costCurveType)    
spreadsheetData = data.readSpreadsheet(spreadsheet, myHelper.keyList)  
# manually modify coverages in data object
spreadsheetData.coverage['Vitamin A supplementation'] = 0.9 
spreadsheetData.coverage['Antenatal micronutrient supplementation'] = 0.58 
spreadsheetData.coverage['IYCF'] = 0.65 
# carry on     
costCoverageInfo = thisOptimisation.getCostCoverageInfo()
targetPopSize = thisOptimisation.getInitialTargetPopSize()        
initialAllocation = optimisation.getTotalInitialAllocation(spreadsheetData, costCoverageInfo, targetPopSize)        
initialAllocationDictionary = {}
for i in range(0, len(spreadsheetData.interventionList)):
    intervention = spreadsheetData.interventionList[i]
    initialAllocationDictionary[intervention] = initialAllocation[i]
outfilename = 'baseline2_spending.csv'  
with open(outfilename, "wb") as f:
    writer = csv.writer(f)
    writer.writerow(initialAllocationDictionary.keys()) 
    writer.writerow(initialAllocationDictionary.values()) 
    
    
# get spending for baseline 1 custom coverages in a csv
myHelper = helper.Helper()
thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, 'dummy', resultsFileStem, costCurveType)    
spreadsheetData = data.readSpreadsheet(spreadsheet, myHelper.keyList)  
# manually modify coverages in data object
spreadsheetData.coverage['IYCF'] = IYCF_cov
# carry on     
costCoverageInfo = thisOptimisation.getCostCoverageInfo()
targetPopSize = thisOptimisation.getInitialTargetPopSize()        
initialAllocation = optimisation.getTotalInitialAllocation(spreadsheetData, costCoverageInfo, targetPopSize)        
initialAllocationDictionary = {}
for i in range(0, len(spreadsheetData.interventionList)):
    intervention = spreadsheetData.interventionList[i]
    initialAllocationDictionary[intervention] = initialAllocation[i]
outfilename = 'baseline1_spending.csv'  
with open(outfilename, "wb") as f:
    writer = csv.writer(f)
    writer.writerow(initialAllocationDictionary.keys()) 
    writer.writerow(initialAllocationDictionary.values()) 
        