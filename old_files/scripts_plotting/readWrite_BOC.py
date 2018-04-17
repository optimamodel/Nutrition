# -*- coding: utf-8 -*-
"""
Created on Fri Jul 15 2016

@author: madhurakilledar
"""
import pickle
import csv
import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(moduleDir)
import optimisation

country = 'Bangladesh'
version = 'Results20160718'

root = '../../%s/%s'%(country,version)
print "\n find input here : %s"%root

outpath = '../../%s/%s_csv'%(country,version)
print "\n find output here : %s"%outpath
if not os.path.exists(outpath):
    os.makedirs(outpath)

cascadeMultiples = [0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 4.0] 
numsteps = 180


# NATIONAL
print "\n National..."
spreadsheetPath = '../input_spreadsheets/%s/InputForCode_%s.xlsx'%(country, country)
thisOptimisation = optimisation.Optimisation(spreadsheetPath, numsteps, "foo", "thisshouldnotbehere")

models = {}
numDeaths  = {}
numStunted = {}

# Baseline
allocation = thisOptimisation.getInitialAllocationDictionary()
models['baseline'] = thisOptimisation.oneModelRunWithOutput(allocation)

# read the optimal budget allocations from file
for scenario in ['deaths','stunting']:
    filename = '%s/%s/national/%s_cascade_%s_1.0.pkl'%(root, scenario, country, scenario)
    infile = open(filename, 'rb')
    allocation = pickle.load(infile)
    infile.close()
    models[scenario] = thisOptimisation.oneModelRunWithOutput(allocation)

# outcomes for baseline
numDeaths['baseline']  = models['baseline'][numsteps-1].getTotalCumulativeDeaths()
numStunted['baseline'] = models['baseline'][numsteps-1].getCumulativeAgingOutStunted()

# outcomes for various optimisations
print "outcomes for cascade"
cascadeModels = {}
for objective in ['deaths','stunting']:
    cascadeModels[objective] = {}
    numDeaths[objective] = {}
    numStunted[objective] = {}
    for multiple in cascadeMultiples:
        filename = '%s/%s/national/%s_cascade_%s_%s.pkl'%(root, objective, country, objective, str(multiple))
        infile = open(filename, 'rb')
        allocation = pickle.load(infile)
        infile.close()
        cascadeModels[objective][multiple]   = thisOptimisation.oneModelRunWithOutput(allocation)
        numDeaths[objective][multiple]  = cascadeModels[objective][multiple][numsteps-1].getTotalCumulativeDeaths()
        numStunted[objective][multiple] = cascadeModels[objective][multiple][numsteps-1].getCumulativeAgingOutStunted()


    # Repeat but for writing to csv
    rowHeader  = ["Multiple of current budget"]
    rowDeaths  = ['Number of deaths under 5']
    rowStunted = ['Number of child stunted at age 5']
    for multiple in cascadeMultiples:
        rowHeader.append(multiple)
        rowDeaths.append( numDeaths[objective][multiple])
        rowStunted.append(numStunted[objective][multiple])
    outfilename = '%s/%s_BOC_min%s.csv'%(outpath, country, objective)
    with open(outfilename, "wb") as f:
        writer = csv.writer(f)
        writer.writerow(rowHeader)
        writer.writerow(rowDeaths)
        writer.writerow(rowStunted)



# GEOSPATIAL
print "\n Geospatial..."
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
for iReg in range(numRegions):
    region = 'region%s'%(iReg)
    regionName = regions[iReg]
    print regionName
    spreadsheetPath = '../input_spreadsheets/%s/subregionSpreadsheets/%s.xlsx'%(country,regionName)
    spreadsheets.append(spreadsheetPath)
    thisOptimisation = optimisation.Optimisation(spreadsheetPath, numsteps, "foo", "thisshouldnotbehere")

    # Baseline
    allocation = thisOptimisation.getInitialAllocationDictionary()
    models['baseline'] = thisOptimisation.oneModelRunWithOutput(allocation)
    numDeaths['baseline'][regionName]  = models['baseline'][numsteps-1].getTotalCumulativeDeaths()
    numStunted['baseline'][regionName] = models['baseline'][numsteps-1].getCumulativeAgingOutStunted()

    # outcomes
    for objective in ['deaths','stunting']:
        cascadeModels[objective] = {}
        numDeaths[objective][regionName]  = {}
        numStunted[objective][regionName] = {}
        for multiple in cascadeMultiples:
            filename = '%s/%s/geospatial/%s_cascade_%s_%s.pkl'%(root, objective, region, objective, str(multiple))
            infile = open(filename, 'rb')
            allocation = pickle.load(infile)
            infile.close()
            cascadeModels[objective][multiple] = thisOptimisation.oneModelRunWithOutput(allocation)
            numDeaths[objective][regionName][multiple]  = cascadeModels[objective][multiple][numsteps-1].getTotalCumulativeDeaths()
            numStunted[objective][regionName][multiple] = cascadeModels[objective][multiple][numsteps-1].getCumulativeAgingOutStunted()

        # Repeat but for writing to csv
        rowHeader  = ["Multiple of current budget"]
        rowDeaths  = ['Number of deaths under 5']
        rowStunted = ['Number of child stunted at age 5']
        for multiple in cascadeMultiples:
            rowHeader.append(multiple)
            rowDeaths.append( numDeaths[objective][regionName][multiple])
            rowStunted.append(numStunted[objective][regionName][multiple])
        outfilename = '%s/%s_BOC_min%s.csv'%(outpath, regionName, objective)
        with open(outfilename, "wb") as f:
            writer = csv.writer(f)
            writer.writerow(rowHeader)
            writer.writerow(rowDeaths)
            writer.writerow(rowStunted)
