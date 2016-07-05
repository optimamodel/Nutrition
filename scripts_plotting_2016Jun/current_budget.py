# -*- coding: utf-8 -*-
"""
Created on Wed Jun 22 13:25:50 2016

@author: ruth
"""

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(moduleDir)
import optimisation

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

# NATIONAL
dataSpreadsheetName = '../InputForCode_Bangladesh.xlsx'
thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, timestep, numModelSteps, ages, birthOutcomes, wastingList, stuntingList, breastfeedingList, ageGroupSpans, agingRateList)
initialAllocation = thisOptimisation.getInitialAllocationDictionary()

# GEOSPATIAL
spreadsheet0 = '../OptimisationScripts/subregionSpreadsheets/Barisal.xlsx'
spreadsheet1 = '../OptimisationScripts/subregionSpreadsheets/Chittagong.xlsx'
spreadsheet2 = '../OptimisationScripts/subregionSpreadsheets/Dhaka.xlsx'
spreadsheet3 = '../OptimisationScripts/subregionSpreadsheets/Khulna.xlsx'
spreadsheet4 = '../OptimisationScripts/subregionSpreadsheets/Rajshahi.xlsx'
spreadsheet5 = '../OptimisationScripts/subregionSpreadsheets/Rangpur.xlsx'
spreadsheet6 = '../OptimisationScripts/subregionSpreadsheets/Sylhet.xlsx'
spreadsheetList = [spreadsheet0, spreadsheet1, spreadsheet2, spreadsheet3, spreadsheet4, spreadsheet5, spreadsheet6]

geospatialInitialAllocation = []
for region in range(0,7):
    dataSpreadsheetName = spreadsheetList[region]
    thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, timestep, numModelSteps, ages, birthOutcomes, wastingList, stuntingList, breastfeedingList, ageGroupSpans, agingRateList)
    allocation = thisOptimisation.getInitialAllocationDictionary()
    geospatialInitialAllocation.append( {'region '+str(region):allocation} )
