# -*- coding: utf-8 -*-
"""
Created on Tue Oct 25 2016

@author: madhura
"""

rootpath = '../..'

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)
import optimisation

country = 'Bangladesh'
date = '2016Oct'

optimiseList = ['stunting','deaths'] #['DALYs', 'stunting', 'deaths']

extraMoney = 10000000
haveFixedProgCosts = True

rerunMCSampleSize = 25
geoMCSampleSize = 25
# WARNING: these must match values used in the other geospatial scripts
numModelSteps = 180
cascadeValues = [1.0, 1.1, 1.25, 1.5, 1.7, 2.0, 'extreme'] 

resultsPath = '/home/ruthpearson/Nutrition/Results/'

regionNameList = ['Barisal', 'Chittagong', 'Dhaka', 'Khulna', 'Rajshahi', 'Rangpur', 'Sylhet']
spreadsheetFileStem = rootpath+'/input_spreadsheets/'+country+'/'+date+'/subregionSpreadsheets/'
spreadsheetList = []
for regionName in regionNameList:
    spreadsheet = spreadsheetFileStem + regionName + '.xlsx'
    spreadsheetList.append(spreadsheet)


numCores = 8 # need this number times the number of outcomes you're optimising for
for optimise in optimiseList:
    print 'running GA for:  ', optimise
    
    resultsFileStem = resultsPath+'/'+date+'/'+optimise+'/geospatial/'
    GAFile = 'GA_fixedProg_extra_'+str(extraMoney)    
    
    geospatialOptimisation = optimisation.GeospatialOptimisation(spreadsheetList, regionNameList, numModelSteps, cascadeValues, optimise, resultsFileStem)
    geospatialOptimisation.performParallelGeospatialOptimisationExtraMoney(geoMCSampleSize, rerunMCSampleSize, GAFile, numCores, extraMoney, haveFixedProgCosts)

    
