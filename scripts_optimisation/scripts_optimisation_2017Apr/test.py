# -*- coding: utf-8 -*-
"""
Created on Thu Oct 27 14:10:32 2016

@author: ruth
"""

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '../..')
sys.path.append(moduleDir)
import optimisation


rootpath = '../..'

country = 'Bangladesh'
date = '2017Apr'
spreadsheetDate = '2017Jan'

spreadsheet = rootpath+'/input_spreadsheets/'+country+'/'+spreadsheetDate+'/InputForCode_'+country+'.xlsx'

numModelSteps = 24
MCSampleSize = 1
cascadeValues = [7.0]  
haveFixedProgCosts = False
numCores = 8

for optimise in ['alive and thrive', 'stunting prev']: #['stunting']:

    resultsFileStem = rootpath+'/Results/'+date+'/'+optimise+'/test/'+country

    thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, optimise, resultsFileStem)
    thisOptimisation.performParallelCascadeOptimisation(MCSampleSize, cascadeValues, numCores, haveFixedProgCosts)
