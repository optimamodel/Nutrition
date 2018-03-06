import os, sys
root = '../../'
moduleDir = os.path.join(os.path.dirname(__file__), root)
sys.path.append(moduleDir)
import optimisation3 as optimisation

objectives = ['thrive', 'healthy_children', 'mortality_rate_children', 'mortality_rate_PW', 'total_anaemia_prev', 'wasting_prev']
budgetMultiples = [0.5, 1., 2., 3., 4., 6., 8.]
fileInfo = [root, '2018Jan', 'Tanzania', '']
totalBudget = 1e7

if __name__ == '__main__':
    thisOptimisation = optimisation.Optimisation(objectives, budgetMultiples, fileInfo, totalBudget=totalBudget, filterProgs=True)
    thisOptimisation.optimise()
    thisOptimisation.writeAllResults()
