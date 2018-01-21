import setup
import optimisation3 as optimisation

objectives = ['thrive']
budgetMultiples = [1.]

if __name__ == '__main__':
    filePath, resultsPath = setup.getFilePath(root='../..', bookDate='2017Nov', country='Bangladesh')
    model = setup.setUpModel(filePath) # TODO: could use 'setUp' in Optimisation
    thisOptimisation = optimisation.Optimisation(model, objectives, budgetMultiples, resultsPath, 'Bangladesh')
    thisOptimisation.optimise()
