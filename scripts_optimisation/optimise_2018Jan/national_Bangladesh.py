import os, sys
root = '../../'
moduleDir = os.path.join(os.path.dirname(__file__), root)
sys.path.append(moduleDir)
import optimisation3 as optimisation

objectives = ['thrive', 'mortality_rate', 'total_anaemia_prev', 'wasting_prev']
budgetMultiples = [0.5, 1., 2., 4., 6., 8.]
fileInfo = [root, '2017Nov', 'Bangladesh']
totalBudget = 10000000.

if __name__ == '__main__':
    thisOptimisation = optimisation.Optimisation(objectives, budgetMultiples, fileInfo, totalBudget=totalBudget)
    thisOptimisation.optimise()
    thisOptimisation.writeAllResults()