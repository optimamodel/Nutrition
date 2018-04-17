# -*- coding: utf-8 -*-
"""
Created on Wed Jun 22 13:25:50 2016

@author: ruth
"""

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(moduleDir)
from nutrition import optimisation

numModelSteps = 180

# NATIONAL
dataSpreadsheetName = '../input_spreadsheets/Bangladesh/InputForCode_Bangladesh.xlsx'
thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps)
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
    thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps)
    allocation = thisOptimisation.getInitialAllocationDictionary()
    geospatialInitialAllocation.append( {'region '+str(region):allocation} )
