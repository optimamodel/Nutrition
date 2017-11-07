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
numModelSteps = 180

costCurveType = 'standard'
regionNameList = ['Arusha', 'Dar_es_Salaam', 'Dodoma', 'Geita', 'Iringa', 'Kagera',
                  'Kaskazini_Pemba', 'Kaskazini_Unguja', 'Katavi', 'Kigoma', 'Kilimanjaro',
                  'Kusini_Pemba', 'Kusini_Unguja', 'Lindi', 'Manyara', 'Mara', 'Mbeya',
                  'Mjini_Magharibi', 'Morogoro', 'Mtwara', 'Mwanza', 'Njombe', 'Pwani',
                  'Rukwa', 'Ruvuma', 'Shinyanga', 'Simiyu', 'Singida', 'Tabora', 'Tanga']

spreadsheetFileStem = rootpath + '/input_spreadsheets/' + country + '/' + spreadsheetDate + '/regions/InputForCode_'
spreadsheetList = []
for regionName in regionNameList:
    spreadsheet = spreadsheetFileStem + regionName + '.xlsx'
    spreadsheetList.append(spreadsheet)

        
# make a zero dictionary        
spreadsheetData = data.readSpreadsheet(spreadsheetList[0], thisHelper.keyList)        
zeroSpending = {}    
for i in range(0, len(spreadsheetData.interventionList)):
    intervention = spreadsheetData.interventionList[i]
    zeroSpending[intervention] = 0.        
    
    
# outcomes for zero spending    
outfilename = 'zero_spending_regional.csv'  
header1 = ['region', 'thrive', 'deaths', 'stunting prev']  
with open(outfilename, "wb") as f:
    writer = csv.writer(f)
    writer.writerow(header1)
    for region in range(len(regionNameList)):
        regionName = regionNameList[region]
        spreadsheet = spreadsheetList[region]
        thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, 'dummy', 'dummy', costCurveType)    
        modelList = thisOptimisation.oneModelRunWithOutput(zeroSpending)    
        row =[regionName, modelList[numModelSteps-1].getOutcome('thrive'), modelList[numModelSteps-1].getOutcome('deaths'), modelList[numModelSteps-1].getOutcome('stunting prev')]
        writer.writerow(row)

# baseline 1 (IYCF cov is zero for all regions so no need to scale up manually)
outfilename = 'baseline1_regional.csv'  
header1 = ['region', 'thrive', 'deaths', 'stunting prev']  
with open(outfilename, "wb") as f:
    writer = csv.writer(f)
    writer.writerow(header1)
    for region in range(len(regionNameList)):
        regionName = regionNameList[region]
        spreadsheet = spreadsheetList[region]
        thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, 'dummy', 'dummy', costCurveType)    
        thisSpending = thisOptimisation.getInitialAllocationDictionary()        
        modelList = thisOptimisation.oneModelRunWithOutput(thisSpending)    
        row =[regionName, modelList[numModelSteps-1].getOutcome('thrive'), modelList[numModelSteps-1].getOutcome('deaths'), modelList[numModelSteps-1].getOutcome('stunting prev')]
        writer.writerow(row)    
    
    
    
    
    
    
 
# zero scenario   
outfilename = 'zero_spending_regional.csv'  
header1 = ['thrive', 'deaths', 'stunting prev']  
with open(outfilename, "wb") as f:
    writer = csv.writer(f)
    writer.writerow(header1)
    thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, 'dummy', resultsFileStem, costCurveType)    
    modelList = thisOptimisation.oneModelRunWithOutput(zeroSpending)    
    row =[modelList[numModelSteps-1].getOutcome('thrive'), modelList[numModelSteps-1].getOutcome('deaths'), modelList[numModelSteps-1].getOutcome('stunting prev')]
    writer.writerow(row)

# baseline 1 with IYCF manually scaled up
outfilename = 'baseline1_national.csv'  
header1 = ['thrive', 'deaths', 'stunting prev']  
with open(outfilename, "wb") as f:
    writer = csv.writer(f)
    writer.writerow(header1)
    thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, 'dummy', resultsFileStem, costCurveType)    
    thisSpending = thisOptimisation.getInitialAllocationDictionary()  
    modelList = thisOptimisation.oneModelRunWithOutputManuallyScaleIYCF(thisSpending, IYCF_cov)    
    row =[modelList[numModelSteps-1].getOutcome('thrive'), modelList[numModelSteps-1].getOutcome('deaths'), modelList[numModelSteps-1].getOutcome('stunting prev')]
    writer.writerow(row)