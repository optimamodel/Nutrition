import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '../..')
sys.path.append(moduleDir)
import optimisation


rootpath = '../..'

country = 'Bangladesh'
date = '2017Oct'

spreadsheet = rootpath+'/input_spreadsheets/'+country+'/'+date+'/InputForCode_'+country+'.xlsx'

numModelSteps = 14
MCSampleSize = 5
cascadeValues = [0.25, 0.75, 1.0, 2.0, 3.0, 4.0, 5.0, 8.0, 12.0]
haveFixedProgCosts = False
numCores = 9
costCurve = 'standard'

interventionsToRemove = ['Public provision of complementary foods with iron',
                         'Public provision of complementary foods with iron (malaria area)',
                         'Iron and folic acid supplementation for pregnant women', 'Iron and folic acid supplementation for pregnant women (malaria area)',
                         'Iron and iodine fortification of salt', 'Iron fortification of wheat flour', 'Iron fortification of maize',
                         'Iron fortification of rice', 'IFA fortification of maize']

for optimise in ['SAM_prev', 'deaths']:

    resultsFileStem = rootpath+'/Results/'+date+'/'+optimise+'/national/'+country

    thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, optimise, resultsFileStem, costCurve, interventionsToRemove=interventionsToRemove)
    thisOptimisation.performParallelCascadeOptimisation(MCSampleSize, cascadeValues, numCores, haveFixedProgCosts)
