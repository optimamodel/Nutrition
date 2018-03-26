import os, sys
root = '../..'
moduleDir = os.path.join(os.path.dirname(__file__), root)
sys.path.append(moduleDir)
import optimisation3 as optimisation


regions = ['Dar_es_Salaam', 'Dodoma']
objectives = ['thrive']
fileInfo = [root, 'Tanzania']

if __name__ == '__main__':
    thisOptimisation = optimisation.GeospatialOptimisation(objectives, fileInfo, None, regions, numYears=6)
    thisOptimisation.optimiseScenarios()