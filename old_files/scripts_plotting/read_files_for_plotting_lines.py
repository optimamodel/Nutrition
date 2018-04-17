# -*- coding: utf-8 -*-
"""
Created on Tue Jun 28 11:31:42 2016

@author: ruth
"""
import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(moduleDir)
from nutrition import optimisation
import pickle
import numpy as np

# read the optimal budget allocations from file
filename = '../Results2016Jul/Bangladesh/deaths/v1/Bangladesh_cascade_deaths_v1_1.0.pkl'
infile = open(filename, 'rb')
deathsOptimumAllocation = pickle.load(infile)
infile.close()
filename = '../Results2016Jul/Bangladesh/stunting/v1/Bangladesh_cascade_stunting_v1_1.0.pkl'
infile = open(filename, 'rb')
stuntingOptimumAllocation = pickle.load(infile)
infile.close()


numModelSteps = 180

# NATIONAL
dataSpreadsheetName = '../input_spreadsheets/Bangladesh/InputForCode_Bangladesh.xlsx'
thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps)
initialAllocation = thisOptimisation.getInitialAllocationDictionary()

# run models and save output 
baseline = thisOptimisation.oneModelRunWithOutput(initialAllocation)
optimiseDeaths = thisOptimisation.oneModelRunWithOutput(deathsOptimumAllocation)
optimiseStunting = thisOptimisation.oneModelRunWithOutput(stuntingOptimumAllocation)

# GET Y AXIS FOR NUMBER OF DEATHS
numberOfDeaths_baseline = []
numberOfDeaths_optimiseDeaths = []
numberOfDeaths_optimiseStunting = []
numberOfDeaths_baseline.append(baseline[0].getTotalCumulativeDeaths())
numberOfDeaths_optimiseDeaths.append(optimiseDeaths[0].getTotalCumulativeDeaths())
numberOfDeaths_optimiseStunting.append(optimiseStunting[0].getTotalCumulativeDeaths())
for model in range(1, len(baseline)):
    difference = baseline[model].getTotalCumulativeDeaths() - baseline[model - 1].getTotalCumulativeDeaths()
    numberOfDeaths_baseline.append(difference)
    
    difference = optimiseDeaths[model].getTotalCumulativeDeaths() - optimiseDeaths[model - 1].getTotalCumulativeDeaths()
    numberOfDeaths_optimiseDeaths.append(difference)    
    
    difference = optimiseStunting[model].getTotalCumulativeDeaths() - optimiseStunting[model - 1].getTotalCumulativeDeaths()
    numberOfDeaths_optimiseStunting.append(difference) 


# GET Y AXIS FOR FRACTION OF CHILDREN STUNTED
stuntingPrev_baseline = []
stuntingPrev_optimiseDeaths = []
stuntingPrev_optimiseStunting = []
for model in range(0, len(baseline)):
    stuntingPrev_baseline.append(baseline[model].getTotalStuntedFraction())
    stuntingPrev_optimiseDeaths.append(optimiseDeaths[model].getTotalStuntedFraction())
    stuntingPrev_optimiseStunting.append(optimiseStunting[model].getTotalStuntedFraction())
    
# GET Y AXIS FOR NUMBER AGING OUT STUNTED
agingOutStunted_baseline = []
agingOutStunted_optimiseDeaths = []
agingOutStunted_optimiseStunting = []
agingOutStunted_baseline.append(baseline[0].getCumulativeAgingOutStunted())
agingOutStunted_optimiseDeaths.append(optimiseDeaths[0].getCumulativeAgingOutStunted())
agingOutStunted_optimiseStunting.append(optimiseStunting[0].getCumulativeAgingOutStunted())
for model in range(1, len(baseline)):
    difference = baseline[model].getCumulativeAgingOutStunted() - baseline[model - 1].getCumulativeAgingOutStunted()    
    agingOutStunted_baseline.append(difference)
    difference = optimiseDeaths[model].getCumulativeAgingOutStunted() - optimiseDeaths[model - 1].getCumulativeAgingOutStunted() 
    agingOutStunted_optimiseDeaths.append(difference)
    difference = optimiseStunting[model].getCumulativeAgingOutStunted() - optimiseStunting[model - 1].getCumulativeAgingOutStunted() 
    agingOutStunted_optimiseStunting.append(difference)    


# MAKE THESE YEARLY
# DEATHS
numberOfDeaths_baselineYearly = []
numberOfDeaths_optimiseDeathsYearly = []
numberOfDeaths_optimiseStuntingYearly = []
numYears = len(baseline)/12
for i in range(0, numYears):
    step = i*12
    numberOfDeaths_baselineYearly.append( sum(numberOfDeaths_baseline[step:(12+step)]) )
    numberOfDeaths_optimiseDeathsYearly.append( sum(numberOfDeaths_optimiseDeaths[step:(12+step)]) )
    numberOfDeaths_optimiseStuntingYearly.append( sum(numberOfDeaths_optimiseStunting[step:(12+step)]) )
    
# STUNTING PREV
stuntingPrev_baselineYearly = []
stuntingPrev_optimiseDeathsYearly = []
stuntingPrev_optimiseStuntingYearly = []  
for i in range(0, numYears):
    step = i*12
    stuntingPrev_baselineYearly.append( np.average(stuntingPrev_baseline[step:(12+step)]) )
    stuntingPrev_optimiseDeathsYearly.append( np.average(stuntingPrev_optimiseDeaths[step:(12+step)]) )
    stuntingPrev_optimiseStuntingYearly.append( np.average(stuntingPrev_optimiseStunting[step:(12+step)]) )
    
# AGING OUT STUNTED
agingOutStunted_baselineYearly = []
agingOutStunted_optimiseDeathsYearly = []
agingOutStunted_optimiseStuntingYearly = []
numYears = len(baseline)/12
for i in range(0, numYears):
    step = i*12
    agingOutStunted_baselineYearly.append( sum(agingOutStunted_baseline[step:(12+step)]) )
    agingOutStunted_optimiseDeathsYearly.append( sum(agingOutStunted_optimiseDeaths[step:(12+step)]) )
    agingOutStunted_optimiseStuntingYearly.append( sum(agingOutStunted_optimiseStunting[step:(12+step)]) ) 

    