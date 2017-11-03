import os, sys
rootpath = '..'
moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)
import optimisation

## LAOS
country = 'Laos'
date = '2017Jun'

numModelSteps = 180

# NATIONAL
dataSpreadsheetName = rootpath+'/input_spreadsheets/'+country+'/'+date+'/InputForCode_LaoPDR_29Jun2017.xlsx'
outcomeOfInterestList = ['thrive']

cascadeValues = [0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 4.0]
optimise = 'thrive'
resultsFileStem = rootpath+'/Results/'+date+'/'+optimise+'/national/'+country
# both time series when optimising for thrive
thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem)
thisOptimisation.outputCurrentSpendingToCSV()
thisOptimisation.outputTimeSeriesToCSV('thrive')
thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem) #this repitition is necessary
thisOptimisation.outputTimeSeriesToCSV('deaths')
# both outcomes for thrive cascade
thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise,
                                             resultsFileStem)  # this one might not be
for outcomeOfInterest in outcomeOfInterestList:
    thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem)
    thisOptimisation.outputCascadeAndOutcomeToCSV(cascadeValues, outcomeOfInterest)


## MADAGASCAR
country = 'Madagascar'
date = '2017Jun'

numModelSteps = 180

# NATIONAL
dataSpreadsheetName = rootpath+'/input_spreadsheets/'+country+'/'+date+'/InputForCode_'+country+'_29Jun2017.xlsx'
outcomeOfInterestList = ['thrive']

cascadeValues = [0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 4.0]
optimise = 'thrive'
resultsFileStem = rootpath+'/Results/'+date+'/'+optimise+'/national/'+country
# both time series when optimising for thrive
thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem)
thisOptimisation.outputCurrentSpendingToCSV()
thisOptimisation.outputTimeSeriesToCSV('thrive')
thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem) #this repitition is necessary
thisOptimisation.outputTimeSeriesToCSV('deaths')
# both outcomes for thrive cascade
thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise,
                                             resultsFileStem)  # this one might not be
for outcomeOfInterest in outcomeOfInterestList:
    thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem)
    thisOptimisation.outputCascadeAndOutcomeToCSV(cascadeValues, outcomeOfInterest)







