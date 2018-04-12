# -*- coding: utf-8 -*-
"""
Created on Tue Oct  4 11:13:27 2016

@author: ruth
"""
import optimisation
import data 
import pickle
from old_files import costcov, helper

costCov = costcov.Costcov()
helper = helper.Helper()

numModelSteps = 12 # this is becasue we get the population size to update coverages after 1 year
optimise = 'stunting'
GAFile = 'GA_fixedProg_extra_'+str(10000000)   
resultsFileStem = 'Results/2016Oct/'+optimise+'/geospatial/fixedCosts/'

regionNameList = ['Barisal', 'Chittagong', 'Dhaka', 'Khulna', 'Rajshahi', 'Rangpur', 'Sylhet']
spreadsheetFileStem = 'input_spreadsheets/Bangladesh/2016Oct/subregionSpreadsheets/'
spreadsheetList = []
for regionName in regionNameList:
    spreadsheet = spreadsheetFileStem + regionName + '.xlsx'
    spreadsheetList.append(spreadsheet)
    
finalCoverages = {}     
for region in range(len(regionNameList)): 
    regionName = regionNameList[region]
    print regionName
    spreadsheet = spreadsheetList[region]
    spreadsheetData = data.readSpreadsheet(spreadsheet, helper.keyList) 
    finalCoverages[regionName] = {}
    thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, optimise, resultsFileStem)
    filename = '%s%s_%s.pkl'%(resultsFileStem, GAFile, regionName)
    infile = open(filename, 'rb')
    allocation = pickle.load(infile)
    infile.close()  
    modelList = thisOptimisation.oneModelRunWithOutput(allocation)
    costCoverageInfo = thisOptimisation.getCostCoverageInfo() 
    targetPopSize = optimisation.getTargetPopSizeFromModelInstance(spreadsheet, helper.keyList, modelList[numModelSteps-1])   
    for i in range(0, len(spreadsheetData.interventionList)):
        intervention = spreadsheetData.interventionList[i]
        finalCoverages[regionName][intervention] = costCov.function(allocation[intervention], costCoverageInfo[intervention], targetPopSize[intervention]) / targetPopSize[intervention]


print finalCoverages

