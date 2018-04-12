# -*- coding: utf-8 -*-
"""
Created on Tue May  9 14:56:33 2017

@author: ruth
"""

rootpath = '../..'
import os, sys

moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)
import optimisation

country = 'Bangladesh'
date = '2017Apr'
spreadsheetDate = '2016Oct'

optimise = 'thrive'
haveFixedProgCosts = True
nCores = 49

numModelSteps = 180
MCSampleSize = 25
cascadeValues = [1.0, 1.1, 1.25, 1.5, 1.7, 2.0, 'extreme']
regionNameList = ['Barisal', 'Chittagong', 'Dhaka', 'Khulna', 'Rajshahi', 'Rangpur', 'Sylhet']
spreadsheetFileStem = rootpath + '/input_spreadsheets/' + country + '/' + spreadsheetDate + '/subregionSpreadsheets/'
spreadsheetList = []
for regionName in regionNameList:
    spreadsheet = spreadsheetFileStem + regionName + '.xlsx'
    spreadsheetList.append(spreadsheet)

resultsFileStem = rootpath + '/Results/' + date + '/' + optimise + '/geospatialFixed/'

geospatialOptimisation = optimisation.GeospatialOptimisation(spreadsheetList, regionNameList, numModelSteps,
                                                             cascadeValues, optimise, resultsFileStem)
geospatialOptimisation.generateParallelResultsForGeospatialCascades(nCores, MCSampleSize, haveFixedProgCosts)