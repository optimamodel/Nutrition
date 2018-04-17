import os, sys

root = '..'
moduleDir = os.path.join(os.path.dirname(__file__), root)
sys.path.append(moduleDir)
from nutrition import optimisation

objectives = ['healthy_children']
budgetMultiples = [1., 2., 4., 6., 8., 10.]
fileInfo = [root, 'national', 'Tanzania', '']
additionalFunds = 1e7

if __name__ == '__main__':
    thisOptimisation = optimisation.Optimisation(objectives, budgetMultiples, fileInfo, additionalFunds=additionalFunds,
                                                 filterProgs=True)
    thisOptimisation.optimise()
    thisOptimisation.writeAllResults()
