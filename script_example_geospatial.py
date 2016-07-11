# -*- coding: utf-8 -*-
"""
Created on Mon Jul 11 17:54:47 2016

@author: ruth
"""

import optimisation

numModelSteps = 180
MCSampleSize = 25
cascadeValues = [0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 4.0]  
spreadsheet0 = 'input_spreadsheets/Bangladesh/subregionSpreadsheets/Barisal.xlsx'
thisOptimisation = optimisation.Optimisation(spreadsheet0, numModelSteps)

optimise = 'deaths'
filename = 'region0_cascade_deaths_'
thisOptimisation.performCascadeOptimisation(optimise, MCSampleSize, filename, cascadeValues)

BOC_deaths_spending, BOC_deaths_outcome = thisOptimisation.generateBOCVectors(filename, cascadeValues, 'deaths')
BOC_stunting_spending, BOC_stunting_outcome = thisOptimisation.generateBOCVectors(filename, cascadeValues, 'stunting')