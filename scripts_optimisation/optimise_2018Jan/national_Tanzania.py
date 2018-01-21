import setup
import optimisation3 as optimisation

objectives = ['thrive']
budgetMultiples = [1.]
fileInfo = ['../../', '2018Jan', 'Tanzania']

if __name__ == '__main__':
    thisOptimisation = optimisation.Optimisation(objectives, budgetMultiples, fileInfo, numModelSteps=13)
    thisOptimisation.optimise()
