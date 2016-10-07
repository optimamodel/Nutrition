# -*- coding: utf-8 -*-
"""
Created on Fri Aug 19 12:58:25 2016

@author: ruth
"""
import optimisation
outcomeOfInterestList = ['deaths', 'stunting', 'DALYs'] 
optimiseForList = ['deaths', 'stunting', 'DALYs'] 
numModelSteps = 180
cascadeValues = [0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 4.0]  
dataSpreadsheetName = 'input_spreadsheets/Bangladesh/2016Aug02/InputForCode_Bangladesh.xlsx'


for optimise in optimiseForList:
    for outcomeOfInterest in outcomeOfInterestList:
        print optimise, '  ' , outcomeOfInterest

        resultsFileStem = 'ResultsJoleneDALY/'+optimise+'/national/Bangladesh'
        thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem)
        thisOptimisation.outputCurrentSpendingToCSV()
        thisOptimisation.outputCascadeAndOutcomeToCSV(cascadeValues, outcomeOfInterest)
        thisOptimisation.outputTimeSeriesToCSV(outcomeOfInterest)

