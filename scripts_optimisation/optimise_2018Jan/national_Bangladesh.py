import os, sys
root = '../../'
moduleDir = os.path.join(os.path.dirname(__file__), root)
sys.path.append(moduleDir)
import optimisation3 as optimisation

objectives = ['healthy_children', 'thrive']
budgetMultiples = [0.5, 1., 2., 3., 6.]
fileInfo = [root, '2017Nov', 'Bangladesh']
totalBudget = 10000000.

if __name__ == '__main__':
    thisOptimisation = optimisation.Optimisation(objectives, budgetMultiples, fileInfo, totalBudget=totalBudget, filterProgs=False)
    thisOptimisation.optimise()
    thisOptimisation.writeAllResults()