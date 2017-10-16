# -*- coding: utf-8 -*-
"""
Created on Fri Sep 22 12:13:34 2017

@author: ruth
"""

import os, sys
rootpath = '..'
moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)
import optimisation

country = 'Bangladesh'
date = '2017Aug'

numModelSteps = 14

# NATIONAL
dataSpreadsheetName = rootpath+'/input_spreadsheets/'+country+'/'+date+'/InputForCode_Bangladesh.xlsx'
outcomeOfInterestList = ['anemia frac everyone', 'thrive', 'deaths']

cascadeValues = [0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 4.0, 8.0, 15.0, 30.0]
optimise = 'anemia frac everyone'
resultsFileStem = rootpath+'/Results/'+date+'/'+optimise+'/national/'+country
# time series
thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem)
thisOptimisation.outputCurrentSpendingToCSV()
for outcomeOfInterest in outcomeOfInterestList:
    thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem)
    thisOptimisation.outputCascadeAndOutcomeToCSV(cascadeValues, outcomeOfInterest)