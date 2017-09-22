import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '../../..')
sys.path.append(moduleDir)
import optimisation

rootpath = '../../..'
country = 'Tanzania'
date = '2017Sep'
spreadsheetDate = '2017Sep'

intervention = 'Vitamin A fortification of food'
effectivenessList = [1., 0.8, 0.6, 0.4, 0.2]

spreadsheet = rootpath+'/input_spreadsheets/'+country+'/'+spreadsheetDate+'/InputForCode_'+country+'_FortificationOnly.xlsx'

numModelSteps = 180
MCSampleSize = 25
cascadeValues = [1.]
haveFixedProgCosts = False
numCores = 10

for optimise in ['deaths', 'stunting']:
    for effectiveness in effectivenessList:
        resultsFileStem = rootpath+'/Results/'+date+'/'+optimise+'/national/'+country+'/FortificationOnly/'+str(effectiveness)+'_effective'
        thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, optimise, resultsFileStem)
        thisOptimisation.performParallelCascadeOptimisationAlteredInterventionEffectiveness(MCSampleSize, cascadeValues, numCores, haveFixedProgCosts, intervention, effectiveness)
