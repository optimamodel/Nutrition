# -*- coding: utf-8 -*-
"""
Created on Mon Jul 25 16:06:08 2016

@author: ruth
"""

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(moduleDir)
from nutrition import optimisation

optimiseList = ['DALYs'] #['DALYs', 'stunting', 'deaths']
haveFixedProgCosts = False

numModelSteps = 180
MCSampleSize = 25
geoMCSampleSize = 25
cascadeValues = [0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 'extreme']
regionNameList = ['Barisal', 'Chittagong', 'Dhaka', 'Khulna', 'Rajshahi', 'Rangpur', 'Sylhet']
spreadsheetFileStem = '../input_spreadsheets/Bangladesh/2016Aug02/subregionSpreadsheets/'
spreadsheetList = []
for regionName in regionNameList:
    spreadsheet = spreadsheetFileStem + regionName + '.xlsx'
    spreadsheetList.append(spreadsheet)


numCores = 8 # need this number times the number of otcomes you're optimising for
for optimise in optimiseList:
    print 'running GA for:  ', optimise
    
    resultsFileStem = '../Results2016Aug12/'+optimise+'/geospatial/'
    GAFile = 'GA'    
    
    geospatialOptimisation = optimisation.GeospatialOptimisation(spreadsheetList, regionNameList, numModelSteps, cascadeValues, optimise, resultsFileStem)
    geospatialOptimisation.performParallelGeospatialOptimisation(geoMCSampleSize, MCSampleSize, GAFile, numCores, haveFixedProgCosts)

    
