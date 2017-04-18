# -*- coding: utf-8 -*-
"""
Created on Tue Apr 18 12:01:30 2017

@author: ruth
"""

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '../..')
sys.path.append(moduleDir)
import optimisation


rootpath = '../'

country = 'Bangladesh'
date = '2017Apr'
spreadsheetDate = '2016Oct'

spreadsheet = rootpath+'/input_spreadsheets/'+country+'/'+spreadsheetDate+'/InputForCode_'+country+'.xlsx'

numModelSteps = 24
MCSampleSize = 1
cascadeValues = [0.25]  
haveFixedProgCosts = False
numCores = 8

for optimise in ['deaths']:

    resultsFileStem = rootpath+'/Results/'+date+'/'+optimise+'/national/'+country

    thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, optimise, resultsFileStem)
    thisOptimisation.performParallelCascadeOptimisation(MCSampleSize, cascadeValues, numCores, haveFixedProgCosts)
