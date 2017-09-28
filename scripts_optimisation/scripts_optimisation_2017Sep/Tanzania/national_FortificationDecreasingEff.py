import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '../../..')
sys.path.append(moduleDir)
import optimisation

rootpath = '../../..'
country = 'Tanzania'
date = '2017Sep'
spreadsheetDate = '2017Sep'

intervention = 'Vitamin A fortification of food'
effectivenessList = [0.4,0.2]

spreadsheet = rootpath+'/input_spreadsheets/'+country+'/'+spreadsheetDate+'/TanzaniaHatSheets'+'/InputForCode_'+country+'Hat_FortificationOnly.xlsx'

costCurveType = 'standard'
savePlot = False
numModelSteps = 180
MCSampleSize = 4
cascadeValues = [1.]
haveFixedProgCosts = False
numCores = 2

for optimise in ['thrive']:
    for effectiveness in effectivenessList:
        resultsFileStem = rootpath+'/Results/'+date+'/'+optimise+'/national/'+country+'Hat'+'/FortificationOnly/'+str(effectiveness)+'_effective/'
        thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, optimise, resultsFileStem, costCurveType)
        thisOptimisation.performParallelCascadeOptimisationAlteredInterventionEffectiveness(MCSampleSize, cascadeValues, numCores, haveFixedProgCosts, intervention, effectiveness, savePlot)
