# -*- coding: utf-8 -*-
"""
Created on Fri Jul 22 15:47:27 2016

@author: ruth
"""

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(moduleDir)
import optimisation

optimise = 'stunting'
numCores = 8

dataSpreadsheetName = '../input_spreadsheets/Bangladesh/InputForCode_Bangladesh.xlsx'
numModelSteps = 180
MCSampleSize = 25
cascadeValues = [0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 4.0]  
resultsFileStem = '../Results2016Jul/'+optimise+'/national/Bangladesh'

thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps)
thisOptimisation.performParallelCascadeOptimisation(optimise, MCSampleSize, resultsFileStem, cascadeValues, numCores)
