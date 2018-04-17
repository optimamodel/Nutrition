import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '../../..')
sys.path.append(moduleDir)
from nutrition import optimisation

rootpath = '../../..'
country = 'Laos'
date = '2017Jun'
spreadsheetDate = '2017Jun'

spreadsheet = rootpath+'/input_spreadsheets/'+country+'/'+spreadsheetDate+'/InputForCode_LaoPDR_29Jun2017.xlsx'

numModelSteps = 180
MCSampleSize = 25
cascadeValues = [0.25, 0.50, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0]
haveFixedProgCosts = False
numCores = 8

for optimise in ['thrive']:
    resultsFileStem = rootpath+'/Results/'+date+'/'+optimise+'/national/'+country
    thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, optimise, resultsFileStem)
    thisOptimisation.performParallelCascadeOptimisation(MCSampleSize, cascadeValues, numCores, haveFixedProgCosts)
