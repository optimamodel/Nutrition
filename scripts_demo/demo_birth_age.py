# -*- coding: utf-8 -*-
"""
Created on Thu Dec 14 15:41:14 2017

@author: ruth
"""

rootpath = '../'

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)

import data
import helper
import csv
thisHelper = helper.Helper()
spreadsheet = rootpath + 'input_spreadsheets/Bangladesh/2017Nov/InputForCode_Bangladesh.xlsx'
thisData = data.readSpreadsheet(spreadsheet, thisHelper.keyList)
m,d,p = thisHelper.setupModelDerivedParameters(thisData)
numSteps = 13

coverage = [0.25, 0.5, 0.75]

header = ['coverage', 'cumulative neonatal deaths', 'cumulative child deaths', 'cumulative PW deaths', 'cumulative thrive', 'stunting prevalence']

rows = []
for cov in coverage:
    m,d,p = thisHelper.setupModelDerivedParameters(thisData)
    m.moveModelOneYear()
    covDict = {'Birth age intervention':cov}
    m.updateCoverages(covDict)
    for i in range(numSteps):
        m.moveModelOneYear()
    row = [cov, m.listOfAgeCompartments[0].getCumulativeDeaths(), m.getTotalCumulativeDeathsChildren(), m.getTotalCumulativeDeathsPW(), m.getOutcome('thrive'), m.getOutcome('stunting prev')]
    rows.append(row) 
    
    
filename = 'birth_age_intervention.csv'
with open(filename, 'wb') as f:
    w = csv.writer(f)
    w.writerow(header)
    for row in rows:
        w.writerow(row)