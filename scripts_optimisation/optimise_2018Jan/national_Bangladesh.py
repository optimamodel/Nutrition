import os, sys
root = '../../'
moduleDir = os.path.join(os.path.dirname(__file__), root)
sys.path.append(moduleDir)
import optimisation3 as optimisation

objectives = ['thrive', 'mortality_rate']#['thrive', 'mortality_rate_children', 'mortality_rate_PW', 'mortality_rate', 'total_anaemia_prev', 'wasting_prev']
budgetMultiples = [0.5, 1., 2., 3., 6.]
fileInfo = [root, '2017Nov', 'Bangladesh']
totalBudget = 10000000.

if __name__ == '__main__':
    thisOptimisation = optimisation.Optimisation(objectives, budgetMultiples, fileInfo, totalBudget=totalBudget)
    thisOptimisation.optimise()
    thisOptimisation.writeAllResults()