# -*- coding: utf-8 -*-
"""
Created on Thu Nov  9 14:57:15 2017

@author: ruth
"""

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '../../..')
sys.path.append(moduleDir)
import optimisation
import data
from copy import deepcopy as dcp
import helper
myHelper = helper.Helper()

rootpath = '../../..'
country = 'Tanzania'
date = '2017Sep'
spreadsheetDate = '2017Sep'
spreadsheet = rootpath+'/input_spreadsheets/'+country+'/'+spreadsheetDate+'/InputForCode_'+country+'.xlsx'
spreadsheet2 = rootpath+'/input_spreadsheets/'+country+'/'+spreadsheetDate+'/InputForCode_'+country+'_baseline2.xlsx'
costCurveType = 'standard'

numModelSteps = 180
MCSampleSize = 25
cascadeValues = [0.25, 0.50, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0]
haveFixedProgCosts = False
numCores = 8

# for baseline 2 custom coverages are these (interventions not modified are zero anyway)
spreadsheetData = data.readSpreadsheet(spreadsheet, myHelper.keyList)
customCoverages = dcp(spreadsheetData.coverage)
customCoverages['IYCF'] = 0.65
customCoverages['Vitamin A supplementation'] = 0.9 
customCoverages['Antenatal micronutrient supplementation'] = 0.58 

for optimise in ['deaths', 'thrive']:
    resultsFileStem = rootpath+'/Results/'+date+'/'+optimise+'/national_baseline2/'+country
    thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, optimise, resultsFileStem, costCurveType)
    thisOptimisation.performParallelCascadeOptimisationCustomCoverage(MCSampleSize, cascadeValues, numCores, haveFixedProgCosts, customCoverages, spreadsheet2)
