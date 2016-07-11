# -*- coding: utf-8 -*-
"""
Created on Wed Jun 29 12:34:33 2016

@author: ruth
"""

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(moduleDir)
import optimisation
import pickle as pickle
from copy import deepcopy as dcp

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
cascadeValues = [0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 4.0] 

spreadsheet0 = '../input_spreadsheets/Bangladesh/subregionSpreadsheets/Barisal.xlsx'
spreadsheet1 = '../input_spreadsheets/Bangladesh/subregionSpreadsheets/Chittagong.xlsx'
spreadsheet2 = '../input_spreadsheets/Bangladesh/subregionSpreadsheets/Dhaka.xlsx'
spreadsheet3 = '../input_spreadsheets/Bangladesh/subregionSpreadsheets/Khulna.xlsx'
spreadsheet4 = '../input_spreadsheets/Bangladesh/subregionSpreadsheets/Rajshahi.xlsx'
spreadsheet5 = '../input_spreadsheets/Bangladesh/subregionSpreadsheets/Rangpur.xlsx'
spreadsheet6 = '../input_spreadsheets/Bangladesh/subregionSpreadsheets/Sylhet.xlsx'
spreadsheetList = [spreadsheet0, spreadsheet1, spreadsheet2, spreadsheet3, spreadsheet4, spreadsheet5, spreadsheet6]

# BASELINE
numberOfDeaths_baseline = {}
numberAgingOutStunted_baseline = {}
for region in range(0, len(spreadsheetList)):
    print "baseline region " + str(region)
    spreadsheetData = spreadsheetList[region]
    thisOptimisation = optimisation.Optimisation(spreadsheetData, timestep, numModelSteps, ages, birthOutcomes, wastingList, stuntingList, breastfeedingList, ageGroupSpans, agingRateList)
    initialAllocation = thisOptimisation.getInitialAllocationDictionary()
    baseline = thisOptimisation.oneModelRunWithOutput(initialAllocation)
    numberOfDeaths_baseline['region '+str(region)] = baseline[numModelSteps-1].getTotalCumulativeDeaths()[0]
    numberAgingOutStunted_baseline['region '+str(region)] = baseline[numModelSteps-1].getCumulativeAgingOutStunted()[0]
    



# EVERYTHING ELSE
numberOfDeaths_optimisingDeaths = {}
numberAgingOutStunted_optimisingDeaths = {}
numberOfDeaths_optimisingStunting = {}
numberAgingOutStunted_optimisingStunting = {}

for region in range(0, len(spreadsheetList)):
    spreadsheetData = spreadsheetList[region]
    thisOptimisation = optimisation.Optimisation(spreadsheetData, timestep, numModelSteps, ages, birthOutcomes, wastingList, stuntingList, breastfeedingList, ageGroupSpans, agingRateList)
    print "everything else region " + str(region)
    numberOfDeaths_optimisingDeaths['region '+str(region)] = {}
    numberAgingOutStunted_optimisingDeaths['region '+str(region)] = {}
    numberOfDeaths_optimisingStunting['region '+str(region)] = {}
    numberAgingOutStunted_optimisingStunting['region '+str(region)] = {}

    # OPTIMISING DEATHS
    cascade_optimisedForDeaths = {}
    for cascade in cascadeValues:
        filename = '../Results2016Jun/Bangladesh/deaths/geospatial/v3/region'+str(region)+'_cascade_deaths_'+str(cascade)+'.pkl'
        infile = open(filename, 'rb')
        thisAllocation = pickle.load(infile)
        infile.close()
        cascade_optimisedForDeaths[cascade] = dcp(thisOptimisation.oneModelRunWithOutput(thisAllocation))
    
    # OPTIMISING STUNTING
    cascade_optimisedForStunting = {}
    for cascade in cascadeValues:
        filename = '../Results2016Jun/Bangladesh/stunting/geospatial/v3/region'+str(region)+'_cascade_stunting_'+str(cascade)+'.pkl'
        infile = open(filename, 'rb')
        thisAllocation = pickle.load(infile)
        infile.close()
        cascade_optimisedForStunting[cascade] = dcp(thisOptimisation.oneModelRunWithOutput(thisAllocation))
    
    
    for key in cascade_optimisedForDeaths.keys():
        numberOfDeaths_optimisingDeaths['region '+str(region)][key] = cascade_optimisedForDeaths[key][numModelSteps-1].getTotalCumulativeDeaths()[0]
        numberAgingOutStunted_optimisingDeaths['region '+str(region)][key] = cascade_optimisedForDeaths[key][numModelSteps-1].getCumulativeAgingOutStunted()[0]
        numberOfDeaths_optimisingStunting['region '+str(region)][key] = cascade_optimisedForStunting[key][numModelSteps-1].getTotalCumulativeDeaths()[0]
        numberAgingOutStunted_optimisingStunting['region '+str(region)][key] = cascade_optimisedForStunting[key][numModelSteps-1].getCumulativeAgingOutStunted()[0]
