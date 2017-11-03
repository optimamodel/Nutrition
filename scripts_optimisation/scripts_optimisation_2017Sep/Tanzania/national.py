import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '../../..')
sys.path.append(moduleDir)
import optimisation

rootpath = '../../..'
country = 'Tanzania'
date = '2017Sep'
spreadsheetDate = '2017Sep'

spreadsheet = rootpath+'/input_spreadsheets/'+country+'/'+spreadsheetDate+'/InputForCode_'+country+'.xlsx'

numModelSteps = 180
MCSampleSize = 25
cascadeValues = [0.25, 0.50, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0]
haveFixedProgCosts = False
numCores = 8

for optimise in ['deaths', 'thrive']:
    resultsFileStem = rootpath+'/Results/'+date+'/'+optimise+'/national/'+country
    thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, optimise, resultsFileStem)
    thisOptimisation.performParallelCascadeOptimisation(MCSampleSize, cascadeValues, numCores, haveFixedProgCosts)
