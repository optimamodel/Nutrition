# -*- coding: utf-8 -*-
"""
Created on Thu Dec 21 15:30:44 2017

@author: ruth
"""

rootpath = '../'

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)

import data
import helper
import csv
from copy import deepcopy as dcp
thisHelper = helper.Helper()
spreadsheet = rootpath + 'input_spreadsheets/Bangladesh/2017Nov/InputForCode_Bangladesh.xlsx'
thisData = data.readSpreadsheet(spreadsheet, thisHelper.keyList)
m,d,p = thisHelper.setupModelDerivedParameters(thisData)
numSteps = 13


header = ['scenario', 'thrive', 'stunting prev', 'deaths: child', 'deaths: PW', 'deaths: neonatal', 'cumulative births', 'anemia: PW', 'anemia: WRA', 'anemia: children', 'wasting: all', 'wasting: MAM', 'wasting: SAM']   

# make a zero dictionary
zero_cov = {}
for intervention in thisData.interventionCompleteList:
    zero_cov[intervention] = 0.0
    
rows = []  
rows2 = []  
    
# run for zero coverage
m,d,p = thisHelper.setupModelDerivedParameters(thisData)
m.moveModelOneYear()
m.updateCoverages(zero_cov)
for i in range(numSteps):
    m.moveModelOneYear()
row1 = ['zero', m.getOutcome('thrive'), m.getOutcome('stunting prev'), m.getTotalCumulativeDeathsChildren(),  m.getTotalCumulativeDeathsPW(), m.listOfAgeCompartments[0].getCumulativeDeaths(), m.cumulativeBirths, m.getOutcome('anemia frac pregnant'), m.getOutcome('anemia frac WRA'), m.getOutcome('anemia frac children'), m.getOutcome('wasting_prev'), m.getOutcome('MAM_prev'), m.getOutcome('SAM_prev')]
rows.append(row1)
rows2.append(row1)


for intervention in thisData.interventionCompleteList:
    m,d,p = thisHelper.setupModelDerivedParameters(thisData)
    m.moveModelOneYear()
    covDict = dcp(zero_cov)
    covDict[intervention] = 0.95
    m.updateCoverages(covDict)
    for i in range(numSteps):
        m.moveModelOneYear()
        row = [intervention + ' 95%', m.getOutcome('thrive'), m.getOutcome('stunting prev'), m.getTotalCumulativeDeathsChildren(),  m.getTotalCumulativeDeathsPW(), m.listOfAgeCompartments[0].getCumulativeDeaths(), m.cumulativeBirths, m.getOutcome('anemia frac pregnant'), m.getOutcome('anemia frac WRA'), m.getOutcome('anemia frac children'), m.getOutcome('wasting_prev'), m.getOutcome('MAM_prev'), m.getOutcome('SAM_prev')]
        rows.append(row)
    #also get % difference        
    rowVals = row[1:]        
    rowPercent = [intervention + ' 95%']
    i = 1        
    for val in rowVals:
        percentChange = (val - row1[i]) / row1[i]
        i += 1
        rowPercent.append(percentChange)
    rows2.append(rowPercent)    
            
        
    
    
print 'writing file...'    
filename = 'demo_all_interventions_absolute.csv'
with open(filename, 'wb') as f:
    w = csv.writer(f)
    w.writerow(header)
    for row in rows:
        w.writerow(row)
        
    
print 'writing file 2 ...'    
filename = 'demo_all_interventions_percent_change.csv'
with open(filename, 'wb') as f:
    w = csv.writer(f)
    w.writerow(header)
    for row in rows2:
        w.writerow(row)        