# -*- coding: utf-8 -*-
"""
Created on Mon Dec 18 14:52:22 2017

@author: ruth
"""

rootpath = '../'

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)

from nutrition import data
from old_files import helper
import csv
from copy import deepcopy as dcp
thisHelper = helper.Helper()
spreadsheet = rootpath + 'input_spreadsheets/Bangladesh/2017Nov/InputForCode_Bangladesh.xlsx'
thisData = data.readSpreadsheet(spreadsheet, thisHelper.keyList)
m,d,p = thisHelper.setupModelDerivedParameters(thisData)
numSteps = 13

header = ['scenario', 'cumulative child deaths', 'thrive']
WASHinterventions = ['WASH: Improved water source', 'WASH: Piped water', 'WASH: Improved sanitation', 'WASH: Hygenic disposal', 'WASH: Handwashing']

# make a zero dictionary
zero_cov = {}
for intervention in thisData.interventionCompleteList:
    zero_cov[intervention] = 0.0
    
rows = []    
    
# run baseline
for i in range(numSteps + 1):
    m.moveModelOneYear()
row0 = ['baseline', m.getTotalCumulativeDeathsChildren(), m.getOutcome('thrive')]
rows.append(row0)

# run for zero coverage
m,d,p = thisHelper.setupModelDerivedParameters(thisData)
m.moveModelOneYear()
m.updateCoverages(zero_cov)
for i in range(numSteps):
    m.moveModelOneYear()
row1 = ['zero', m.getTotalCumulativeDeathsChildren(), m.getOutcome('thrive')]
rows.append(row1)


for intervention in WASHinterventions:
    m,d,p = thisHelper.setupModelDerivedParameters(thisData)
    m.moveModelOneYear()
    covDict = dcp(zero_cov)
    covDict[intervention] = 0.85
    m.updateCoverages(covDict)
    for i in range(numSteps):
        m.moveModelOneYear()
        row = [intervention + ' 85%', m.getTotalCumulativeDeathsChildren(), m.getOutcome('thrive')]
    rows.append(row) 
    
    
filename = 'WASHdemo.csv'
with open(filename, 'wb') as f:
    w = csv.writer(f)
    w.writerow(header)
    for row in rows:
        w.writerow(row)