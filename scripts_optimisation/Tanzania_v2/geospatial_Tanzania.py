import os, sys
root = '../..'
moduleDir = os.path.join(os.path.dirname(__file__), root)
sys.path.append(moduleDir)
import optimisation

objectives = ['healthy_children']
fileInfo = [root, 'Tanzania']

if __name__ == '__main__':
    thisOptimisation = optimisation.GeospatialOptimisation(objectives, fileInfo, regions, numYears=6)
    thisOptimisation.optimiseScenarios()