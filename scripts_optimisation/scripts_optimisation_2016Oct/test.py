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
date = '2016Oct'

spreadsheet = rootpath+'/input_spreadsheets/'+country+'/'+date+'/InputForCode_'+country+'.xlsx'

numModelSteps = 12
MCSampleSize = 1
cascadeValues = [7.0]  
haveFixedProgCosts = False
numCores = 8

for optimise in ['stunting']:

    resultsFileStem = '/home/ruthpearson/Nutrition/Results/'+date+'/'+optimise+'/national/'+country+'_test'

    thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, optimise, resultsFileStem)
    thisOptimisation.performParallelCascadeOptimisation(MCSampleSize, cascadeValues, numCores, haveFixedProgCosts)
