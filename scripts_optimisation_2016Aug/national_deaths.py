# -*- coding: utf-8 -*-
"""
Created on Tue Aug  2 17:11:33 2016

@author: ruth
"""

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(moduleDir)
import optimisation

optimise = 'deaths'
haveFixedProgCosts = False
numCores = 8

dataSpreadsheetName = '../input_spreadsheets/Bangladesh/2016Aug02/InputForCode_Bangladesh.xlsx'
numModelSteps = 180
MCSampleSize = 25
cascadeValues = [0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 4.0]  
resultsFileStem = '../Results2016Aug10/'+optimise+'/national/Bangladesh'

thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem)
thisOptimisation.performParallelCascadeOptimisation(MCSampleSize, cascadeValues, numCores, haveFixedProgCosts)
