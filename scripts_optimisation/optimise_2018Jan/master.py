import os, sys
root = '../../'
moduleDir = os.path.join(os.path.dirname(__file__), root)
sys.path.append(moduleDir)
import optimisation3 as optimisation

objectives = ['thrive']
budgetMultiples = [1.]
fileInfo = [root, '', 'Master']
totalBudget = 6.e9

if __name__ == '__main__':
    thisOptimisation = optimisation.Optimisation(objectives, budgetMultiples, fileInfo, totalBudget=totalBudget)
    thisOptimisation.optimise()
    thisOptimisation.writeAllResults()