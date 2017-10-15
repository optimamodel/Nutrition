import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '../..')
sys.path.append(moduleDir)
import optimisation


rootpath = '../..'

country = 'Bangladesh'
date = '2017Aug'

spreadsheet = rootpath+'/input_spreadsheets/'+country+'/'+date+'/InputForCode_'+country+'.xlsx'

numModelSteps = 14
MCSampleSize = 1
cascadeValues = [1.]
haveFixedProgCosts = False
numCores = 1

for optimise in ['wasting prev']:

    resultsFileStem = rootpath+'/Results/'+date+'/'+optimise+'/national/'+country+'/'

    thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, optimise, resultsFileStem)
    thisOptimisation.performParallelCascadeOptimisation(MCSampleSize, cascadeValues, numCores, haveFixedProgCosts)
