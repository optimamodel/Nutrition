# -*- coding: utf-8 -*-
"""
Created on Thu Jul 14 2016

@author: madhura
"""
import pickle
import numpy as np
import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(moduleDir)
from nutrition import optimisation

country = 'Bangladesh'
version = 'v5'
root = '../../Results2016Jun/%s'%(country)

numTimesteps = 180

allocation = {}
dataSpreadsheetName = '../input_spreadsheets/%s/InputForCode_Bangladesh.xlsx'%(country)
# Baseline
thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numTimesteps, 'foo', 'shouldnotbehere')
allocation['baseline'] = thisOptimisation.getInitialAllocationDictionary()
# read the optimal budget allocations from file
for scenario in ['deaths','stunting']:
    filename = '%s/%s/%s/%s_cascade_%s_%s_1.0.pkl'%(root, scenario, version, country, scenario, version)
    infile = open(filename, 'rb')
    allocation[scenario] = pickle.load(infile)
    infile.close()

# run models and save output 
print "\n run model within optimisation..."
modelRun = {}
for scenario in ['baseline','deaths','stunting']:
    print scenario
    modelRun[scenario] = thisOptimisation.oneModelRunWithOutput(allocation[scenario])



# GET Y AXIS FOR NUMBER OF DEATHS
print "\n Monthly Deaths" 
numDeaths = {}
for scenario in ['baseline','deaths','stunting']:
    print scenario
    numDeaths[scenario] = []
    numDeaths[scenario].append(modelRun[scenario][0].getTotalCumulativeDeaths())
    for i in range(1, numTimesteps):
        print modelRun[scenario][i].getTotalCumulativeDeaths()
        difference = modelRun[scenario][i].getTotalCumulativeDeaths() - modelRun[scenario][i-1].getTotalCumulativeDeaths()
        numDeaths[scenario].append(difference)
        
# GET Y AXIS FOR FRACTION OF CHILDREN STUNTED
stuntingPrev = {}
for scenario in ['baseline','deaths','stunting']:
    stuntingPrev[scenario] = []
    for i in range(0, numTimesteps):
        stuntingPrev[scenario].append(modelRun[scenario][i].getTotalStuntedFraction())
    
# GET Y AXIS FOR NUMBER AGING OUT STUNTED
print "\n Monthly number of children stunted over 5" 
numStuntedAfter5 = {}
for scenario in ['baseline','deaths','stunting']:
    print scenario
    numStuntedAfter5[scenario] = []
    numStuntedAfter5[scenario].append(modelRun[scenario][0].getCumulativeAgingOutStunted())
    for i in range(1, numTimesteps):
        print modelRun[scenario][i].getCumulativeAgingOutStunted()
        difference = modelRun[scenario][i].getCumulativeAgingOutStunted() - modelRun[scenario][i-1].getCumulativeAgingOutStunted()
        numStuntedAfter5[scenario].append(difference)

# MAKE THESE YEARLY
numYears = numTimesteps/12

# DEATHS
print "\n Annual deaths"
numDeathsYearly = {}
for scenario in ['baseline','deaths','stunting']:
    print scenario
    numDeathsYearly[scenario] = []
    for i in range(0, numYears):
        step = i*12
        numDeathsYearly[scenario].append( sum(numDeaths[scenario][step:12+step]) )
    print numDeathsYearly[scenario]
    
# STUNTING PREV
print "\n Annual prevalence of stunting"
stuntingPrevYearly = {}
for scenario in ['baseline','deaths','stunting']:
    print scenario
    stuntingPrevYearly[scenario] = []
    for i in range(0, numYears):
        step = i*12
        stuntingPrevYearly[scenario].append( np.average(stuntingPrev[scenario][step:12+step]) )
    print stuntingPrevYearly[scenario]

# AGING OUT STUNTED
print "\n number of children stunted after age 5"
numStuntedAfter5Yearly = {}
for scenario in ['baseline','deaths','stunting']:
    print scenario
    numStuntedAfter5Yearly[scenario] = []
    for i in range(0, numYears):
        step = i*12
        numStuntedAfter5Yearly[scenario].append( sum(numStuntedAfter5[scenario][step:12+step]) )
    print numStuntedAfter5Yearly[scenario]

