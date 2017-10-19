# -*- coding: utf-8 -*-
"""
Created on Mon Jul 11 17:54:47 2016

@author: ruth

This is an example script of how to use the geospatial class to generate and harvest results.
Use as a reference, do not edit.
"""

import optimisation

numModelSteps = 180
MCSampleSize = 4
geoMCSampleSize = 4
cascadeValues = [0.25, 1.0, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 4.0]  
costCurveType = 'standard'
haveFixedProgCosts = False
splitCascade = True
optimise = 'deaths'
regionNameList = ['Barisal', 'Chittagong', 'Dhaka', 'Khulna', 'Rajshahi', 'Rangpur', 'Sylhet']
spreadsheetFileStem = 'input_spreadsheets/Bangladesh/2016Oct/subregionSpreadsheets/'
spreadsheetList = []
for regionName in regionNameList:
    spreadsheet = spreadsheetFileStem + regionName + '.xlsx'
    spreadsheetList.append(spreadsheet)

# this is the location of the optimisation results per region (to be generated or harvested)
resultsFileStem = 'ResultsExample/'+optimise+'/geospatial/'

# this is the location of the results from the geospatial analysis
GAFile = 'GA_'

# check athena and then specify how many cores you are going to use (this translates into the number of jobs as we assume 1 core per job)
nCores = 56

# instantiate a geospatial object
geospatialOptimisation = optimisation.GeospatialOptimisation(spreadsheetList, regionNameList, numModelSteps, cascadeValues, optimise, resultsFileStem, costCurveType)

# use it to genarate geospatial cascades if they're not already there (these will be stored in the resultsFileStem location)
geospatialOptimisation.generateParallelResultsForGeospatialCascades(nCores, MCSampleSize, haveFixedProgCosts, splitCascade)

# now use those results to perform the geospatial optimisation
nCores = 7
geospatialOptimisation.performParallelGeospatialOptimisation(geoMCSampleSize, MCSampleSize, GAFile, nCores, haveFixedProgCosts)

# plot the reallocation of spending per region
geospatialOptimisation.plotPostGAReallocationByRegion(GAFile)









