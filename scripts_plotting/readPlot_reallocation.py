# -*- coding: utf-8 -*-
"""
Created on Tue Jul 12 2016

@author: madhurakilledar and kelseygrantham
"""
import pickle
import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(moduleDir)
from plotting import plotallocations
import optimisation

country = 'Bangladesh'
version = 'Results20160718'

root = '../../%s/%s'%(country,version)
print "\n find input here : %s"%root



# NATIONAL
nationalAllocations = {}
# current baseline
numsteps = 180
spreadsheetPath = '../input_spreadsheets/%s/InputForCode_%s.xlsx'%(country, country)
thisOptimisation = optimisation.Optimisation(spreadsheetPath, numsteps)
nationalAllocations['baseline'] = thisOptimisation.getInitialAllocationDictionary()
# optimised
for objective in ['deaths','stunting']:
    filename = '%s/%s/national/%s_cascade_%s_1.0.pkl'%(root, objective, country, objective)
    infile = open(filename, 'rb')
    allocation = pickle.load(infile)
    nationalAllocations[objective] = allocation
    infile.close()
    # plot
    plotallocations(nationalAllocations['baseline'],nationalAllocations[objective])



# GEOSPATIAL
regions = ['Barisal','Chittagong','Dhaka','Khulna','Rajshahi','Rangpur','Sylhet']
numRegions = len(regions)
spreadsheets = []
geospatialAllocations = {}
for iReg in range(numRegions):
    region = 'region%s'%(iReg)
    regionName = regions[iReg]
    print regionName
    spreadsheetPath = '../input_spreadsheets/%s/subregionSpreadsheets/%s.xlsx'%(country,regionName)
    spreadsheets.append(spreadsheetPath)
    thisOptimisation = optimisation.Optimisation(spreadsheetPath, numsteps)
    geospatialAllocations[region] = {}
    geospatialAllocations[region]['baseline'] = thisOptimisation.getInitialAllocationDictionary()
    for objective in ['deaths','stunting']:
        filename = '%s/%s/geospatial/%s_cascade_%s_1.0.pkl'%(root, objective, region, objective)
        infile = open(filename, 'rb')
        allocation = pickle.load(infile)
        geospatialAllocations[region][objective] = allocation
        infile.close()
        # plot
        plotallocations(geospatialAllocations[region]['baseline'],geospatialAllocations[region][objective])
