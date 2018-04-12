import os, sys
root = '../../'
moduleDir = os.path.join(os.path.dirname(__file__), root)
sys.path.append(moduleDir)
import optimisation3 as optimisation

objectives = ['thrive']
budgetMultiples = [1.]
fileInfo = [root, '', 'Master']

if __name__ == '__main__':
    thisOptimisation = optimisation.Optimisation(objectives, budgetMultiples, fileInfo,
                                                 fixCurrentAllocations=True, additionalFunds=2000000, numYears=6)
    thisOptimisation.optimise()
    thisOptimisation.writeAllResults()
