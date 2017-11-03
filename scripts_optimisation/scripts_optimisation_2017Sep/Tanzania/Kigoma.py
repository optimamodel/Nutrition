# -*- coding: utf-8 -*-
"""
Created on Tue Oct 10 11:47:20 2017

@author: ruth
"""

rootpath = '../../..'
import os, sys

moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)
import optimisation

country = 'Tanzania'
date = '2017Sep'
spreadsheetDate = '2017Sep'

optimise = 'deaths'
haveFixedProgCosts = False
nCores = 360 #(12*30 - not actually using all these)

costCurveType = 'standard'
numModelSteps = 180
MCSampleSize = 10
cascadeValues = [0.0, 0.1, 0.2, 0.4, 0.8, 1.0, 1.1, 1.25, 1.5, 1.7, 2.0, 75.0]
splitCascade = True

regionNameList = ['Kigoma']

spreadsheetFileStem = rootpath + '/input_spreadsheets/' + country + '/' + spreadsheetDate + '/regions/'
spreadsheetList = []
for regionName in regionNameList:
    spreadsheet = spreadsheetFileStem + '/InputForCode_' + regionName + '.xlsx'
    spreadsheetList.append(spreadsheet)

resultsFileStem = rootpath + '/Results/' + date + '/' + optimise + '/geospatialProgNotFixed/'

geospatialOptimisation = optimisation.GeospatialOptimisation(spreadsheetList, regionNameList, numModelSteps,
                                                             cascadeValues, optimise, resultsFileStem, costCurveType)
geospatialOptimisation.generateParallelResultsForGeospatialCascades(nCores, MCSampleSize, haveFixedProgCosts, splitCascade)