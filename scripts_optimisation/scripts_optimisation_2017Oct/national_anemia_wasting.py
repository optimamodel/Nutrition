import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '../..')
sys.path.append(moduleDir)
import optimisation


rootpath = '../..'

country = 'Bangladesh'
date = '2017Oct'

spreadsheet = rootpath+'/input_spreadsheets/'+country+'/'+date+'/InputForCode_'+country+'.xlsx'

numModelSteps = 14
MCSampleSize = 15
cascadeValues = [0.25, 0.75, 1.0, 2.0, 3.0, 4.0, 8.0, 15.0]
haveFixedProgCosts = False
numCores = 24

for optimise in ['wasting prev', 'severely wasted prev', 'moderately wasted prev']:

    resultsFileStem = rootpath+'/Results/'+date+'/'+optimise+'/national/'+country+'/'+country

    thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, optimise, resultsFileStem)
    thisOptimisation.performParallelCascadeOptimisation(MCSampleSize, cascadeValues, numCores, haveFixedProgCosts)
