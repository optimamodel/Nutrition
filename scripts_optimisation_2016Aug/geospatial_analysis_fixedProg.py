# -*- coding: utf-8 -*-
"""
Created on Mon Jul 25 16:06:08 2016

@author: ruth
"""

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(moduleDir)
import optimisation

optimiseList = ['DALYs', 'stunting', 'deaths']
extraMoney = 10000000

numModelSteps = 180
MCSampleSize = 25
geoMCSampleSize = 25
cascadeValues = [1.0, 1.20, 1.50, 1.80, 2.0, 3.0, 'extreme'] 
regionNameList = ['Barisal', 'Chittagong', 'Dhaka', 'Khulna', 'Rajshahi', 'Rangpur', 'Sylhet']
spreadsheetFileStem = '../input_spreadsheets/Bangladesh/2016Aug02/subregionSpreadsheets/'
spreadsheetList = []
for regionName in regionNameList:
    spreadsheet = spreadsheetFileStem + regionName + '.xlsx'
    spreadsheetList.append(spreadsheet)


numCores = 21 # need this number times the number of otcomes you're optimising for
for optimise in optimiseList:
    print 'running GA for:  ', optimise
    
    resultsFileStem = '../Results2016Aug08fixedProgCosts/'+optimise+'/geospatial/'
    GAFile = 'GA_fixedProg_extra_'+str(extraMoney)    
    
    geospatialOptimisation = optimisation.GeospatialOptimisation(spreadsheetList, regionNameList, numModelSteps, cascadeValues, optimise, resultsFileStem)
    geospatialOptimisation.performParallelGeospatialOptimisationExtraMoney(geoMCSampleSize, MCSampleSize, GAFile, numCores, extraMoney)

    
