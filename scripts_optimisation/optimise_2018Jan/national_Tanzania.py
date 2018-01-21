import setup
import optimisation3 as optimisation

objectives = ['thrive']
budgetMultiples = [1.]
fileInfo = ['../../', '2018Jan', 'Tanzania']
# totalBudget = 1647545487. # TODO: massive amount of money b/c of WASH -- what about MAM/SAM treatment... Looks weird
totalBudget = 20000000.


if __name__ == '__main__':
    thisOptimisation = optimisation.Optimisation(objectives, budgetMultiples, fileInfo, totalBudget=totalBudget, numModelSteps=13, numRuns=1)
    thisOptimisation.optimise()
