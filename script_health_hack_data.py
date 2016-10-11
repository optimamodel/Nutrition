# -*- coding: utf-8 -*-
"""
Created on Mon Oct 10 16:24:31 2016

@author: ruth
"""

import optimisation

optimise = 'stunting'
haveFixedProgCosts = False
numRuns = 100

dataSpreadsheetName = 'input_spreadsheets/Bangladesh/2016Sept12/InputForCode_Bangladesh.xlsx'
numModelSteps = 180
MCSampleSize = 50
resultsFileStem = 'dummy'
filename = 'health_hack_dummy_data'

thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem)
thisOptimisation.performParallelSampling(MCSampleSize, haveFixedProgCosts, numRuns, filename)
