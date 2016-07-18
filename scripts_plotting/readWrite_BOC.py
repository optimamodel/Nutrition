# -*- coding: utf-8 -*-
"""
Created on Fri Jul 15 2016

@author: madhurakilledar
"""
import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(moduleDir)
import optimisation
import pickle

cascade = [0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 4.0] 
numsteps = 180

country = 'Bangladesh'
version = 'v5'
root = '../../Results2016Jun/%s'%(country)

dataSpreadsheetName = '../input_spreadsheets/%s/InputForCode_%s.xlsx'%(country, country)
thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numsteps)

# Baseline
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


numDeaths  = {}
numStunted = {}

numDeaths['baseline']  = modelRun['baseline'][numsteps-1].getTotalCumulativeDeaths()[0]
numStunted['baseline'] = modelRun['baseline'][numsteps-1].getCumulativeAgingOutStunted()[0]


for objective in ['deaths','stunting']:
    modelRun[objective] = {}
    numDeaths[objective] = {}
    numStunted[objective] = {}
    for multiple in cascade:
        filename = '%s/%s/%s/%s_cascade_%s_%s_%s.pkl'%(root, objective, version, country, objective, version, str(multiple))
        infile = open(filename, 'rb')
        allocation = pickle.load(infile)
        infile.close()
        modelRun[objective][multiple]   = thisOptimisation.oneModelRunWithOutput(allocation)
        numDeaths[objective][multiple]  = modelRun[objective][multiple][numsteps-1].getTotalCumulativeDeaths()[0]
        numStunted[objective][multiple] = modelRun[objective][multiple][numsteps-1].getCumulativeAgingOutStunted()[0]
