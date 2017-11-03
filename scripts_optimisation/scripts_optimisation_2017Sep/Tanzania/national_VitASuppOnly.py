import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '../../..')
sys.path.append(moduleDir)
import optimisation

rootpath = '../../..'
country = 'Tanzania'
date = '2017Sep'
spreadsheetDate = '2017Sep'

spreadsheet = rootpath+'/input_spreadsheets/'+country+'/'+spreadsheetDate+'/TanzaniaHatSheets'+'/InputForCode_'+country+'Hat_VitASuppOnly.xlsx'

costCurveType = 'standard'
numModelSteps = 180
MCSampleSize = 4
cascadeValues = [1.]
haveFixedProgCosts = False
numCores = 1

for optimise in ['thrive']:
    resultsFileStem = rootpath+'/Results/'+date+'/'+optimise+'/national/'+country+'Hat/'+'VitASuppOnly/'
    thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, optimise, resultsFileStem, costCurveType)
    thisOptimisation.performParallelCascadeOptimisation(MCSampleSize, cascadeValues, numCores, haveFixedProgCosts)
