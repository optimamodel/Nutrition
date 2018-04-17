# -*- coding: utf-8 -*-
"""
Created on Tue Aug  2 17:27:39 2016

@author: ruth
"""

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(moduleDir)
from nutrition import optimisation

optimise = 'DALYs'
nCores = 7

numModelSteps = 180
MCSampleSize = 25
cascadeValues = ['extreme'] #[0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 'extreme'] #, 4.0]  
regionNameList = ['Barisal', 'Chittagong', 'Dhaka', 'Khulna', 'Rajshahi', 'Rangpur', 'Sylhet']
spreadsheetFileStem = '../input_spreadsheets/Bangladesh/2016Aug02/subregionSpreadsheets/'
spreadsheetList = []
for regionName in regionNameList:
    spreadsheet = spreadsheetFileStem + regionName + '.xlsx'
    spreadsheetList.append(spreadsheet)
    
resultsFileStem = '../Results2016Aug02/'+optimise+'/geospatial/'

geospatialOptimisation = optimisation.GeospatialOptimisation(spreadsheetList, regionNameList, numModelSteps, cascadeValues, optimise, resultsFileStem)
geospatialOptimisation.generateParallelResultsForGeospatialCascades(nCores, MCSampleSize)
