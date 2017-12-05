import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '../..')
sys.path.append(moduleDir)
import optimisation

rootpath = '../..'

country = 'Bangladesh'
date = '2017Nov5'
sheetDate = '2017Nov'
spreadsheet = rootpath+'/input_spreadsheets/'+country+'/'+sheetDate+'/InputForCode_'+country+'.xlsx'

cascadeValues = [0.25, 0.5, 1.0, 2.0, 3.0, 4.0, 8.0]
totalBudget = 20000000.
objectiveList = ['thrive', 'deaths']

interventionsToKeep = ['Vitamin A supplementation',
                       'Public provision of complementary foods','Public provision of complementary foods with iron',
                       'Public provision of complementary foods with iron (malaria area)',
                       'Sprinkles', 'Sprinkles (malaria area)',
                       'Zinc supplementation',
                       'Balanced energy-protein supplementation',
                       'Multiple micronutrient supplementation', 'Multiple micronutrient supplementation (malaria area)',
                       'Iron and folic acid supplementation for pregnant women', 'Iron and folic acid supplementation for pregnant women (malaria area)',
                       'IPTp', 'Long-lasting insecticide-treated bednets',
                       'IFA fortification of wheat flour', 'IFA fortification of maize', 'IFA fortification of rice',
                       'Family Planning',
                       'IYCF 1', 'IYCF 2', 'IYCF 3']

resultsFileStem = rootpath+'/Results/'+country+'/national/'+date

thisOptimisation = optimisation.Optimisation(cascadeValues, objectiveList, spreadsheet, resultsFileStem, country,
                                             totalBudget=totalBudget, parallel=True, numRuns=2, interventionsToKeep=interventionsToKeep)
thisOptimisation.optimise()