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

timestep = 1./12. 
numsteps = 180
ages = ["<1 month", "1-5 months", "6-11 months", "12-23 months", "24-59 months"]
birthOutcomes = ["Pre-term SGA", "Pre-term AGA", "Term SGA", "Term AGA"]
wastingList = ["normal", "mild", "moderate", "high"]
stuntingList = ["normal", "mild", "moderate", "high"]
breastfeedingList = ["exclusive", "predominant", "partial", "none"]
keyList = [ages, birthOutcomes, wastingList, stuntingList, breastfeedingList]
ageGroupSpans = [1., 5., 6., 12., 36.] # number of months in each age group
agingRateList = [1./1., 1./5., 1./6., 1./12., 1./36.] # fraction of people aging out per MONTH (WARNING use ageSpans to define this)
numModelSteps = 180

spreadsheetData = '.../input_spreadsheets/Bangladesh/InputForCode_Bangladesh.xlsx'
thisOptimisation = optimisation.Optimisation(spreadsheetData, timestep, numModelSteps, ages, birthOutcomes, wastingList, stuntingList, breastfeedingList, ageGroupSpans, agingRateList)

# BASELINE 
initialAllocation = thisOptimisation.getInitialAllocationDictionary()
baseline = thisOptimisation.oneModelRunWithOutput(initialAllocation)
numberOfDeathsBaseline = baseline[numModelSteps-1].getTotalCumulativeDeaths()[0]
numberOfStuntingBaseline =baseline[numModelSteps-1].getCumulativeAgingOutStunted()[0]


# OPTIMISING DEATHS
cascade_optimisedForDeaths = {}
for cascade in cascadeValues:
    filename = '../Results2016Jun/Bangladesh/deaths/v5/Bangladesh_cascade_deaths_v5_'+str(cascade)+'.pkl'
    infile = open(filename, 'rb')
    thisAllocation = pickle.load(infile)
    infile.close()
    cascade_optimisedForDeaths[cascade] = thisOptimisation.oneModelRunWithOutput(thisAllocation)

# OPTIMISING STUNTING
cascade_optimisedForStunting = {}
for cascade in cascadeValues:
    filename = '../Results2016Jun/Bangladesh/stunting/v5/Bangladesh_cascade_stunting_v5_'+str(cascade)+'.pkl'
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


