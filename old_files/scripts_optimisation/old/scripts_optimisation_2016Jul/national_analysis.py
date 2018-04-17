# -*- coding: utf-8 -*-
"""
Created on Wed Aug  3 13:03:54 2016

@author: ruth
"""

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(moduleDir)
from nutrition import optimisation

optimise = 'stunting'

dataSpreadsheetName = '../input_spreadsheets/Bangladesh/2016Aug02/InputForCode_Bangladesh.xlsx'
numModelSteps = 180
MCSampleSize = 25
cascadeValues = [0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 4.0]  
resultsFileStem = '../Results2016Aug02/'+optimise+'/national/Bangladesh'

thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem)
#thisOptimisation.plotReallocation()
thisOptimisation.plotTimeSeries()