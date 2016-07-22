# -*- coding: utf-8 -*-
"""
Created on Fri Jul 22 14:58:46 2016

@author: ruth
"""

import time
t0 = time.time()

import optimisation
numModelSteps = 180
MCSampleSize = 1
optimise = 'deaths'
spreadsheet0 = 'input_spreadsheets/Bangladesh/subregionSpreadsheets/Barisal.xlsx'
filename = 'time_test'
optimisation1 = optimisation.Optimisation(spreadsheet0, numModelSteps)
optimisation1.performSingleOptimisation(optimise, MCSampleSize, filename)

t1 = time.time()
total = t1-t0

#  DETAIL TIMING RUN RESULTS BELOW FOR OUR RECORDS
# total = 346 s = 5.75 min for:  MCSampleSize = 1, numModelSteps = 180  (on Ruth's laptop)