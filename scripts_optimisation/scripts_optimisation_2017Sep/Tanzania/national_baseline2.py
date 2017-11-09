# -*- coding: utf-8 -*-
"""
Created on Thu Nov  9 14:57:15 2017

@author: ruth
"""

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '../../..')
sys.path.append(moduleDir)
import optimisation

rootpath = '../../..'
country = 'Tanzania'
date = '2017Sep'
spreadsheetDate = '2017Sep'
# use the spreadsheet which has the baseline 2 coverages 
spreadsheet = rootpath+'/input_spreadsheets/'+country+'/'+spreadsheetDate+'/InputForCode_'+country+'_baseline2.xlsx'
costCurveType = 'standard'

numModelSteps = 180
MCSampleSize = 25
cascadeValues = [0.25, 0.50, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0]
haveFixedProgCosts = False
numCores = 8

for optimise in ['deaths', 'thrive']:
    resultsFileStem = rootpath+'/Results/'+date+'/'+optimise+'/national_baseline2/'+country
    thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, optimise, resultsFileStem, costCurveType)
    thisOptimisation.performParallelCascadeOptimisation(MCSampleSize, cascadeValues, numCores, haveFixedProgCosts)
