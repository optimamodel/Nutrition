# -*- coding: utf-8 -*-
"""
Created on Fri Dec 22 12:28:36 2017

@author: ruth
"""

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '../..')
sys.path.append(moduleDir)
from nutrition import optimisation

rootpath = '../..'

country = 'Bangladesh'
date = '2018Jan'
sheetDate = '2017Nov'
spreadsheet = rootpath+'/input_spreadsheets/'+country+'/'+sheetDate+'/InputForCode_'+country+'.xlsx'
totalBudget = 10000000
cascadeValues = [0.25, 0.5, 1.0, 2.0, 3.0, 4.0, 8.0]
objectiveList = ['thrive', 'deaths', 'anemia frac everyone', 'wasting_prev']
             
# list of interventions not to be defunded             
customInterventionList =['IPTp', 'Long-lasting insecticide-treated bednets', 'Family Planning']  

resultsFileStem = rootpath+'/Results/'+country+'/national/'+date

thisOptimisation = optimisation.Optimisation(cascadeValues, objectiveList, spreadsheet, resultsFileStem, country, totalBudget=totalBudget, parallel=True, numRuns=1)

thisOptimisation.setCustomFixedCosts(customInterventionList)
thisOptimisation.optimise()