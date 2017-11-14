import os, sys
rootpath = '..'
moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)
import optimisation

country = 'Bangladesh'
date = '2017Oct'

numModelSteps = 14

# NATIONAL
dataSpreadsheetName = rootpath+'/input_spreadsheets/'+country+'/'+date+'/InputForCode_Bangladesh.xlsx'
outcomeOfInterestList = ['wasting_prev', 'SAM_prev', 'MAM_prev', 'deaths']

cascadeValues = [0.25, 0.75, 1.0, 2.0, 3.0, 4.0, 8.0, 15.0, 30.0]
optimiseList = ['wasting_prev', 'SAM_prev', 'MAM_prev', 'deaths']
for optimise in optimiseList:
    resultsFileStem = rootpath+'/Results/'+date+'/'+optimise+'/national/'+country
    # time series
    thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem)
    thisOptimisation.outputCurrentSpendingToCSV()
    for outcomeOfInterest in outcomeOfInterestList:
        thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem)
        thisOptimisation.outputCascadeAndOutcomeToCSV(cascadeValues, outcomeOfInterest)