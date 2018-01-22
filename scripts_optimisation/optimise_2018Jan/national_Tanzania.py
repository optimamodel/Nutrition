import optimisation3 as optimisation

objectives = ['total_anaemia_prev', 'thrive', 'total_deaths', 'wasting_prev' ]
budgetMultiples = [0.5, 1., 2., 4.]
fileInfo = ['../../', '2018Jan', 'Tanzania']
totalBudget = 1688794001. # calculated using reference case & IYCF 1 at 15% coverage. Fixed costs of reference will be subtracted from this

if __name__ == '__main__':
    thisOptimisation = optimisation.Optimisation(objectives, budgetMultiples, fileInfo, totalBudget=totalBudget, numModelSteps=13, numRuns=1)
    thisOptimisation.optimise()
    thisOptimisation.writeAllResults()
