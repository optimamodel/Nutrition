# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 10:58:55 2018

@author: ruth
"""

import os, sys
rootpath = '..'
moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)
import optimisation

country = 'Bangladesh'
date = '2018Jan'
sheetDate = '2017Nov'

# NATIONAL
spreadsheet = rootpath+'/input_spreadsheets/'+country+'/'+sheetDate+'/InputForCode_Bangladesh.xlsx'
totalBudget = 10000000
cascadeValues = [0.25, 0.5, 1.0, 2.0, 3.0, 4.0, 8.0]
objectiveList = ['thrive', 'deaths', 'anemia frac everyone', 'wasting_prev']

resultsFileStem = rootpath+'/Results/'+country+'/national/'+date

thisOptimisation = optimisation.Optimisation(cascadeValues, objectiveList, spreadsheet, resultsFileStem, country,
                                             totalBudget=totalBudget, parallel=True, numRuns=1)
thisOptimisation.writeAllResults()
