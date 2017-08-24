# -*- coding: utf-8 -*-
"""
Created on Wed Jul 12 22:50:19 2017

@author: ruth
"""

rootpath = '..'
import os, sys

moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)

import optimisation
import costcov
costCov = costcov.Costcov()
import helper
import costcov

costCov = costcov.Costcov()
helper = helper.Helper()

numModelSteps = 12 # this is becasue we get the population size to update coverages after 1 year

regionNameList = ['Barisal', 'Chittagong', 'Dhaka', 'Khulna', 'Rajshahi', 'Rangpur', 'Sylhet']
spreadsheetFileStem = rootpath + '/input_spreadsheets/Bangladesh/2016Oct/subregionSpreadsheets/'
spreadsheetList = []
for regionName in regionNameList:
    spreadsheet = spreadsheetFileStem + regionName + '.xlsx'
    spreadsheetList.append(spreadsheet)
    
#spending = [230189.1034, 830273.5871, 1315229.22, 216897.5043, 286073.4721, 121337.1132, 0] # this is Vit A taken directly from output spreadsheet
## get allocation dict of zeros 
#spreadsheetData = data.readSpreadsheet(spreadsheetList[0], helper.keyList)
#allocation = {}
#for intervention in spreadsheetData.interventionList:
#    allocation[intervention] = 0.0
#    
#coverages = {}    
#for region in range(len(regionNameList)): 
#    regionName = regionNameList[region]
#    print regionName
#    spreadsheet = spreadsheetList[region]
#    spreadsheetData = data.readSpreadsheet(spreadsheet, helper.keyList) 
#    thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, "dummy", "dummy")
#    thisAllocation = dcp(allocation)
#    thisAllocation['Vitamin A supplementation'] = spending[region]
#    #print thisAllocation
#    modelList = thisOptimisation.oneModelRunWithOutput(thisAllocation)
#    costCoverageInfo = thisOptimisation.getCostCoverageInfo() 
#    targetPopSize = optimisation.getTargetPopSizeFromModelInstance(spreadsheet, helper.keyList, modelList[numModelSteps-1]) 
#    intervention = 'Vitamin A supplementation'
#    coverage = costCov.function(thisAllocation[intervention], costCoverageInfo[intervention], targetPopSize[intervention]) / targetPopSize[intervention]
#    coverages[regionName] = dcp(coverage)    
#    
##print 'COVERAGES'
##print coverages


# now run model to get number of people stunted in each region for allocation
import pickle
date = '2017Apr'
optimise = 'thrive'
resultsFileStem =  '../Results/' + date + '/' + optimise + '/geospatialNotFixed_London/'
GAFile = 'GA_notFixed_3mTotal' 

for region in range(len(regionNameList)):
    regionName = regionNameList[region]
    print regionName
    spreadsheet = spreadsheetList[region]
    filename = '%s%s_%s.pkl'%(resultsFileStem, GAFile, regionName)
    infile = open(filename, 'rb')
    allocation = pickle.load(infile)
    infile.close()
    thisOptimisation = optimisation.Optimisation(spreadsheet, 180, optimise, resultsFileStem) 
    modelList = thisOptimisation.oneModelRunWithOutput(allocation)
    print 'stunting:  ', modelList[179].getOutcome('stunting')





