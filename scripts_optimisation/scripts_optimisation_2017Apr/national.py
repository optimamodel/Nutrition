# -*- coding: utf-8 -*-
"""
Created on Tue Oct 25 2016

@author: madhura
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

numModelSteps = 180
MCSampleSize = 25
cascadeValues = [0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 4.0]  
haveFixedProgCosts = False
numCores = 16

for optimise in ['alive and thrive', 'stunting prev']:

    resultsFileStem = rootpath+'/Results/'+date+'/'+optimise+'/national/'+country

    thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, optimise, resultsFileStem)
    thisOptimisation.performParallelCascadeOptimisation(MCSampleSize, cascadeValues, numCores, haveFixedProgCosts)
