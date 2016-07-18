# -*- coding: utf-8 -*-
"""
Created on Fri Jul 15 2016

@author: madhurakilledar
"""
import pickle
import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(moduleDir)
import optimisation

cascadeMultiples = [0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 4.0] 
numsteps = 180

country = 'Bangladesh'
version = 'v5'
root = '../../Results2016Jun/%s'%(country)


# NATIONAL
models = {}
numDeaths  = {}
numStunted = {}

spreadsheetPath = '../input_spreadsheets/%s/InputForCode_%s.xlsx'%(country, country)
thisOptimisation = optimisation.Optimisation(spreadsheetPath, numsteps)

# Baseline
allocation = thisOptimisation.getInitialAllocationDictionary()
models['baseline'] = thisOptimisation.oneModelRunWithOutput(allocation)

# read the optimal budget allocations from file
for scenario in ['deaths','stunting']:
    filename = '%s/%s/%s/%s_cascade_%s_%s_1.0.pkl'%(root, scenario, version, country, scenario, version)
    infile = open(filename, 'rb')
    allocation = pickle.load(infile)
    infile.close()
    models[scenario] = thisOptimisation.oneModelRunWithOutput(allocation)

# outcomes for baseline
numDeaths['baseline']  = models['baseline'][numsteps-1].getTotalCumulativeDeaths()[0]
numStunted['baseline'] = models['baseline'][numsteps-1].getCumulativeAgingOutStunted()[0]

# outcomes for various optimisations
cascadeModels = {}
for objective in ['deaths','stunting']:
    cascadeModels[objective] = {}
    numDeaths[objective] = {}
    numStunted[objective] = {}
    for multiple in cascadeMultiples:
        filename = '%s/%s/%s/%s_cascade_%s_%s_%s.pkl'%(root, objective, version, country, objective, version, str(multiple))
        infile = open(filename, 'rb')
        allocation = pickle.load(infile)
        infile.close()
        cascadeModels[objective][multiple]   = thisOptimisation.oneModelRunWithOutput(allocation)
        numDeaths[objective][multiple]  = cascadeModels[objective][multiple][numsteps-1].getTotalCumulativeDeaths()[0]
        numStunted[objective][multiple] = cascadeModels[objective][multiple][numsteps-1].getCumulativeAgingOutStunted()[0]





# GEOSPATIAL
regions = ['Barisal','Chittagong','Dhaka','Khulna','Rajshahi','Rangpur','Sylhet']
numRegions = len(regions)
numsteps = 180

# initialise
models = {}
cascadeModels = {}
numDeaths  = {}
numStunted = {}
for scenario in ['baseline','deaths','stunting']:
    models[scenario]     = {}
    numDeaths[scenario]  = {}
    numStunted[scenario] = {}

# regional spreadsheet names
spreadsheets = []
for region in regions:
    spreadsheetPath = '../input_spreadsheets/Bangladesh/subregionSpreadsheets/%s.xlsx'%(region)
    spreadsheets.append[spreadsheetPath]
    thisOptimisation = optimisation.Optimisation(spreadsheetPath, numsteps)

    # Baseline
    allocation = thisOptimisation.getInitialAllocationDictionary()
    models['baseline'] = thisOptimisation.oneModelRunWithOutput(allocation)
    numDeaths['baseline'][region]  = models['baseline'][numsteps-1].getTotalCumulativeDeaths()[0]
    numStunted['baseline'][region] = models['baseline'][numsteps-1].getCumulativeAgingOutStunted()[0]

    # outcomes
    for objective in ['deaths','stunting']:
        cascadeModels[objective] = {}
        numDeaths[objective][region]  = {}
        numStunted[objective][region] = {}
        for multiple in cascadeMultiples:
            filename = '%s/%s/%s/%s_cascade_%s_%s_%s.pkl'%(root, objective, version, country, objective, version, str(multiple))
            infile = open(filename, 'rb')
            allocation = pickle.load(infile)
            infile.close()
            cascadeModels[objective][multiple] = thisOptimisation.oneModelRunWithOutput(allocation)
            numDeaths[objective][region][multiple]  = cascadeModels[objective][multiple][numsteps-1].getTotalCumulativeDeaths()[0]
            numStunted[objective][region][multiple] = cascadeModels[objective][multiple][numsteps-1].getCumulativeAgingOutStunted()[0]
