# -*- coding: utf-8 -*-
"""
Created on Fri Jun 17 13:56:23 2016

@author: ruth
"""

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(moduleDir)
from nutrition import optimisation

numModelSteps = 180
MCSampleSize = 25
#cascadeValues = [0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 4.0]  
cascadeValues = [0.25, 0.50, 0.75, 1.0]

spreadsheet0 = '../input_spreadsheets/Bangladesh/subregionSpreadsheets/Barisal.xlsx'

thisOptimisation = optimisation.Optimisation(spreadsheet0, numModelSteps)

optimise = 'deaths'
filename = 'region0_cascade_deaths_'
thisOptimisation.performCascadeOptimisation(optimise, MCSampleSize, filename, cascadeValues)

   
