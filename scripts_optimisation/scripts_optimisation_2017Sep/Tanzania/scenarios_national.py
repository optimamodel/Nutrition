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
optimise = ['thrive']
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
outfilename = 'zero_spending.csv'  
header1 = ['thrive', 'deaths', 'stunting prev']  
with open(outfilename, "wb") as f:
    writer = csv.writer(f)
    writer.writerow(header1)
    thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, 'dummy', resultsFileStem, costCurveType)    
    modelList = thisOptimisation.oneModelRunWithOutput(zeroSpending)    
    row =[modelList[numModelSteps-1].getOutcome('thrive'), modelList[numModelSteps-1].getOutcome('deaths'), modelList[numModelSteps-1].getOutcome('stunting prev')]
    writer.writerow(row)

# baseline 1 with IYCF manually scaled up
outfilename = 'current_spending.csv'  
header1 = ['region', 'thrive', 'deaths', 'stunting prev']  
with open(outfilename, "wb") as f:
    writer = csv.writer(f)
    writer.writerow(header1)
    thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, 'dummy', resultsFileStem, costCurveType)    
    thisSpending = thisOptimisation.getInitialAllocationDictionary()  
    modelList = thisOptimisation.oneModelRunWithOutputManuallyScaleIYCF(thisSpending, IYCF_cov)    
    row =[modelList[numModelSteps-1].getOutcome('thrive'), modelList[numModelSteps-1].getOutcome('deaths'), modelList[numModelSteps-1].getOutcome('stunting prev')]
    writer.writerow(row)
    
# baseline 2 with custom coverages
customCoverages = {'Vitamin A supplementation':0.9, 'Antenatal micronutrient supplementation':0.58, 'IYCF':0.65}
outfilename = 'current_spending.csv'  
header1 = ['region', 'thrive', 'deaths', 'stunting prev']  
with open(outfilename, "wb") as f:
    writer = csv.writer(f)
    writer.writerow(header1)
    thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, 'dummy', resultsFileStem, costCurveType)    
    modelList = thisOptimisation.oneModelRunWithOutputCustomCoverages(customCoverages)    
    row =[modelList[numModelSteps-1].getOutcome('thrive'), modelList[numModelSteps-1].getOutcome('deaths'), modelList[numModelSteps-1].getOutcome('stunting prev')]
    writer.writerow(row)    
    
    
    
