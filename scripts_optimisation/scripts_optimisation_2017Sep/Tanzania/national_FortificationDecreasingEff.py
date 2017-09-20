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
cascadeValues = [0.25, 0.50, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0]
haveFixedProgCosts = False
numCores = 40

for optimise in ['deaths','thrive']:
    for effectiveness in effectivenessList:
        resultsFileStem = rootpath+'/Results/'+date+'/'+optimise+'/national/'+country+'/FortificationOnly/'+str(effectiveness)+'_effective'
        thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, optimise, resultsFileStem)
        thisOptimisation.performParallelCascadeOptimisationAlteredInterventionEffectiveness(MCSampleSize, cascadeValues, numCores, haveFixedProgCosts, intervention, effectiveness)
