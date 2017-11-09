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
import pandas
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
spreadsheetListIYCF = []
for regionName in regionNameList:
    spreadsheet = spreadsheetFileStem + regionName + '.xlsx'
    spreadsheet2 = spreadsheetFileStem + regionName + '_IYCF.xlsx'
    spreadsheetList.append(spreadsheet)
    spreadsheetListIYCF.append(spreadsheet2)

Location = 'IYCF_coverage.xlsx'
df = pandas.read_excel(Location, sheetname = 'Sheet1')
IYCF_cov_regional = list(df['Coverage'])
        
## make a zero dictionary        
spreadsheetData = data.readSpreadsheet(spreadsheetList[0], thisHelper.keyList)        
zeroSpending = {}    
for i in range(0, len(spreadsheetData.interventionList)):
    intervention = spreadsheetData.interventionList[i]
    zeroSpending[intervention] = 0.        
    
    
# outcomes for zero spending    
print 'zero spending...'
outfilename = 'zero_spending_regional.csv'  
header1 = ['region', 'thrive', 'deaths', 'stunting prev']  
with open(outfilename, "wb") as f:
    writer = csv.writer(f)
    writer.writerow(header1)
    for region in range(len(regionNameList)):
        regionName = regionNameList[region]
        print regionName
        spreadsheet = spreadsheetList[region]
        thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, 'dummy', 'dummy', costCurveType)    
        modelList = thisOptimisation.oneModelRunWithOutput(zeroSpending)    
        row =[regionName, modelList[numModelSteps-1].getOutcome('thrive'), modelList[numModelSteps-1].getOutcome('deaths'), modelList[numModelSteps-1].getOutcome('stunting prev')]
        writer.writerow(row)

# baseline 1 (IYCF cov scaled up manually)
print 'baseline 1....'
outfilename = 'baseline1_regional.csv'  
header1 = ['region', 'thrive', 'deaths', 'stunting prev']  
with open(outfilename, "wb") as f:
    writer = csv.writer(f)
    writer.writerow(header1)
    for region in range(len(regionNameList)):
        regionName = regionNameList[region]
        print regionName
        spreadsheet = spreadsheetList[region]
        thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, 'dummy', 'dummy', costCurveType)    
        thisSpending = thisOptimisation.getInitialAllocationDictionary()        
        modelList = thisOptimisation.oneModelRunWithOutputManuallyScaleIYCF(thisSpending, IYCF_cov_regional[region])
        row =[regionName, modelList[numModelSteps-1].getOutcome('thrive'), modelList[numModelSteps-1].getOutcome('deaths'), modelList[numModelSteps-1].getOutcome('stunting prev')]
        writer.writerow(row)    
    
# put regional current spending into csv 
print 'regional current spending...'
i=0     
outfilename = 'regional_current_spending.csv'  
with open(outfilename, "wb") as f:
    writer = csv.writer(f)
    for region in range(len(regionNameList)):
        regionName = regionNameList[region]
        print regionName
        spreadsheet = spreadsheetListIYCF[region]
        thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, 'dummy', 'dummy', costCurveType)    
        thisSpending = thisOptimisation.getInitialAllocationDictionary()
        interventionNames = [key for key in thisSpending.keys()]        
        if i<1: #do this once
            writer.writerow(['region'] + interventionNames)
        row = [regionName] + [value for value in thisSpending.values()]
        i+=1
        writer.writerow(row)       
