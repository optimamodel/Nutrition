import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '../..')
sys.path.append(moduleDir)
import optimisation

rootpath = '../..'

country = 'Bangladesh'
date = '2017Nov'
sheetDate = '2017Nov'

spreadsheet = rootpath+'/input_spreadsheets/'+country+'/'+sheetDate+'/InputForCode_'+country+'.xlsx'

cascadeValues = [0.25, 0.5, 1.0, 2.0, 3.0, 4.0, 8.0]
totalBudget = 20000000.

interventionsToRemove = ['Public provision of complementary foods with iron',
                         'Public provision of complementary foods with iron (malaria area)',
                         'Iron and folic acid supplementation for pregnant women', 'Iron and folic acid supplementation for pregnant women (malaria area)',
                         'Iron and iodine fortification of salt', 'Iron fortification of wheat flour', 'Iron fortification of maize',
                         'Iron fortification of rice', 'IFA fortification of maize']

objectiveList = ['thrive', 'deaths']

resultsFileStem = rootpath+'/Results/'+country+'/national/'+date

thisOptimisation = optimisation.Optimisation(cascadeValues, objectiveList, spreadsheet, resultsFileStem, country,
                                             totalBudget=totalBudget, parallel=True, interventionsToRemove=interventionsToRemove)
thisOptimisation.optimise()
