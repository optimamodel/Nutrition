# -*- coding: utf-8 -*-
"""
Created on Fri Jun 17 13:56:23 2016

@author: ruth
"""

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(moduleDir)
import optimisation

dataSpreadsheetName = '../input_spreadsheets/Bangladesh/InputForCode_Bangladesh.xlsx'
numModelSteps = 24 #180

#timestep = 1./12. 
#ages = ["<1 month", "1-5 months", "6-11 months", "12-23 months", "24-59 months"]
#birthOutcomes = ["Pre-term SGA", "Pre-term AGA", "Term SGA", "Term AGA"]
#wastingList = ["normal", "mild", "moderate", "high"]
#stuntingList = ["normal", "mild", "moderate", "high"]
#breastfeedingList = ["exclusive", "predominant", "partial", "none"]
#keyList = [ages, birthOutcomes, wastingList, stuntingList, breastfeedingList]
#ageGroupSpans = [1., 5., 6., 12., 36.] # number of months in each age group
#agingRateList = [1./1., 1./5., 1./6., 1./12., 1./36.] # fraction of people aging out per MONTH (WARNING use ageSpans to define this)

MCSampleSize = 1 #25
#cascadeValues = [0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 4.0]  
cascadeValues = [1.0] #[0.25, 0.50, 0.75, 1.0]

#thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, timestep, numModelSteps, ages, birthOutcomes, wastingList, stuntingList, breastfeedingList, ageGroupSpans, agingRateList)
thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps)


optimise = 'deaths'
filename = 'Bangladesh_cascade_deaths_v4_'
thisOptimisation.performCascadeOptimisation(optimise, MCSampleSize, filename, cascadeValues)

   
