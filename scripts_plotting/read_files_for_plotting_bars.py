# -*- coding: utf-8 -*-
"""
Created on Tue Jun 28 15:15:57 2016

@author: ruth
"""
import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(moduleDir)
import optimisation
import pickle as pickle
cascadeValues = [0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 4.0] 

numModelSteps = 180

spreadsheetData = '../input_spreadsheets/Bangladesh/InputForCode_Bangladesh.xlsx'
thisOptimisation = optimisation.Optimisation(spreadsheetData, numModelSteps)

# BASELINE 
initialAllocation = thisOptimisation.getInitialAllocationDictionary()
baseline = thisOptimisation.oneModelRunWithOutput(initialAllocation)
numberOfDeathsBaseline = baseline[numModelSteps-1].getTotalCumulativeDeaths()[0]
numberOfStuntingBaseline =baseline[numModelSteps-1].getCumulativeAgingOutStunted()[0]


# OPTIMISING DEATHS
cascade_optimisedForDeaths = {}
for cascade in cascadeValues:
    filename = '../Results2016Jul/Bangladesh/deaths/v1/Bangladesh_cascade_deaths_v1_'+str(cascade)+'.pkl'
    infile = open(filename, 'rb')
    thisAllocation = pickle.load(infile)
    infile.close()
    cascade_optimisedForDeaths[cascade] = thisOptimisation.oneModelRunWithOutput(thisAllocation)

# OPTIMISING STUNTING
cascade_optimisedForStunting = {}
for cascade in cascadeValues:
    filename = '../Results2016Jul/Bangladesh/stunting/v1/Bangladesh_cascade_stunting_v1_'+str(cascade)+'.pkl'
    infile = open(filename, 'rb')
    thisAllocation = pickle.load(infile)
    infile.close()
    cascade_optimisedForStunting[cascade] = thisOptimisation.oneModelRunWithOutput(thisAllocation)
    

numberOfDeathsWhenOptimisingDeaths = {}
numberOfStuntingWhenOptimisingDeaths = {}
numberOfDeathsWhenOptimisingStunting = {}
numberOfStuntingWhenOptimisingStunting = {}
for key in cascade_optimisedForDeaths.keys():
    numberOfDeathsWhenOptimisingDeaths[key] = cascade_optimisedForDeaths[key][numModelSteps-1].getTotalCumulativeDeaths()[0]
    numberOfStuntingWhenOptimisingDeaths[key] = cascade_optimisedForDeaths[key][numModelSteps-1].getCumulativeAgingOutStunted()[0]
    numberOfDeathsWhenOptimisingStunting[key] = cascade_optimisedForStunting[key][numModelSteps-1].getTotalCumulativeDeaths()[0]
    numberOfStuntingWhenOptimisingStunting[key] = cascade_optimisedForStunting[key][numModelSteps-1].getCumulativeAgingOutStunted()[0]


