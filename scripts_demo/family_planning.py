# -*- coding: utf-8 -*-
"""
Created on Mon Dec  4 15:09:23 2017

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

zero_cov = {}
for intervention in thisData.interventionCompleteList:
    zero_cov[intervention] = 0.0
    
zeroDist = {}
for intervention in thisData.effectivenessFP:
    zeroDist[intervention] = 0.0    
    
header = ['scenario', 'cumulative neonatal deaths', 'cumulative child deaths', 'cumulative PW deaths', 'cumulative births', 'cumulative thrive']    

# run baseline
for i in range(numSteps + 1):
    m.moveModelOneYear()
row0 = ['baseline', m.listOfAgeCompartments[0].getCumulativeDeaths(), m.getTotalCumulativeDeathsChildren(), m.getTotalCumulativeDeathsPW(), m.cumulativeBirths, m.getOutcome('thrive')]

# run for zero FP coverage
m,d,p = thisHelper.setupModelDerivedParameters(thisData)
m.moveModelOneYear()
m.updateCoverages(zero_cov)
for i in range(numSteps):
    m.moveModelOneYear()
row1 = ['zero', m.listOfAgeCompartments[0].getCumulativeDeaths(), m.getTotalCumulativeDeathsChildren(), m.getTotalCumulativeDeathsPW(), m.cumulativeBirths, m.getOutcome('thrive')]

# run with each intervention scaled to 0.85
rows = []
for intervention in thisData.effectivenessFP:
    thisData.distributionFP = dcp(zeroDist)
    thisData.distributionFP[intervention] = 1.0
    m,d,p = thisHelper.setupModelDerivedParameters(thisData)
    m.moveModelOneYear()
    cov = {}
    cov['Family Planning'] = 0.85
    m.updateCoverages(cov)
    for i in range(numSteps):
        m.moveModelOneYear()
    row = [intervention + ' at 85%', m.listOfAgeCompartments[0].getCumulativeDeaths(), m.getTotalCumulativeDeathsChildren(), m.getTotalCumulativeDeathsPW(), m.cumulativeBirths, m.getOutcome('thrive')]
    rows.append(row)
   
   
# varying FP coverages and unmet need
thisData = data.readSpreadsheet(spreadsheet, thisHelper.keyList)   
rows2 = []
for covFP in [0.1, 0.3, 0.5, 0.6, 0.7, 0.85]:
    rows2.append(['FP cov ' + str(covFP)])
    for unmetNeed in [0.1, 0.3, 0.5]:
        thisData.demographics['unmet need for family planning'] = unmetNeed
        m,d,p = thisHelper.setupModelDerivedParameters(thisData)
        m.moveModelOneYear()
        cov = {}
        cov['Family Planning'] = covFP
        m.updateCoverages(cov)
        for i in range(numSteps):
            m.moveModelOneYear()
        row = ['unmet need ' + str(unmetNeed), m.listOfAgeCompartments[0].getCumulativeDeaths(), m.getTotalCumulativeDeathsChildren(), m.getTotalCumulativeDeathsPW(), m.cumulativeBirths, m.getOutcome('thrive')]
        rows2.append(row)
        
    


filename = 'family_planning.csv'
with open(filename, 'wb') as f:
    w = csv.writer(f)
    w.writerow(header)
    w.writerow(row0)
    w.writerow(row1)
    w.writerow('')
    for row in rows2:
        w.writerow(row)
    w.writerow('')
    for row in rows:
        w.writerow(row)