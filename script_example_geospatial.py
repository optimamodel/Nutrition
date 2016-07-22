# -*- coding: utf-8 -*-
"""
Created on Mon Jul 11 17:54:47 2016

@author: ruth
"""

import optimisation

numModelSteps = 24
MCSampleSize = 1
geoMCSampleSize = 1
cascadeValues = [0.25, 0.50] #, 0.75, 1.0, 1.50, 2.0, 3.0, 4.0]  
optimise = 'deaths'
spreadsheet0 = 'input_spreadsheets/Bangladesh/subregionSpreadsheets/Barisal.xlsx'
spreadsheet1 = 'input_spreadsheets/Bangladesh/subregionSpreadsheets/Chittagong.xlsx'
spreadsheet2 = 'input_spreadsheets/Bangladesh/subregionSpreadsheets/Dhaka.xlsx'
spreadsheet3 = 'input_spreadsheets/Bangladesh/subregionSpreadsheets/Khulna.xlsx'
spreadsheet4 = 'input_spreadsheets/Bangladesh/subregionSpreadsheets/Rajshahi.xlsx'
spreadsheet5 = 'input_spreadsheets/Bangladesh/subregionSpreadsheets/Rangpur.xlsx'
spreadsheet6 = 'input_spreadsheets/Bangladesh/subregionSpreadsheets/Sylhet.xlsx'
spreadsheetList = [spreadsheet0, spreadsheet1] #, spreadsheet2, spreadsheet3, spreadsheet4, spreadsheet5, spreadsheet6]

regionNameList = ['Barisal', 'Chittagong'] #, 'Dhaka', 'Khulna', 'Rajshahi', 'Rangpur', 'Sylhet']
#regionNameList = ['region0', 'region1', 'region2', 'region3', 'region4', 'region5', 'region6']
resultsFileStem = 'ResultsExampleParallel/deaths/geospatial/Barisal'
GAresultsFileStem = 'ResultsExampleParallel/deaths/geospatial/GAResult'

#geospatialOptimisation = optimisation.GeospatialOptimisation(spreadsheetList, regionNameList, numModelSteps, cascadeValues, optimise, resultsFileStem)
#geospatialOptimisation.generateAllRegionsBOC()
#geospatialOptimisation.performGeospatialOptimisation(geoMCSampleSize, MCSampleSize, GAresultsFileStem)
#geospatialOptimisation.generateResultsForGeospatialCascades()

#geospatialOptimisation = optimisation.GeospatialOptimisation(spreadsheetList, regionNameList, numModelSteps, cascadeValues, optimise, resultsFileStem)
#nCores = 2
#geospatialOptimisation.generateParallelResultsForGeospatialCascades(nCores)

optimisation1 = optimisation.Optimisation(spreadsheet0, numModelSteps)
processes = optimisation1.performParallelCascadeOptimisation(optimise, MCSampleSize, resultsFileStem, cascadeValues)






