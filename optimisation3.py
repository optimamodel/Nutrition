from copy import deepcopy as dcp
from operator import add

def runModelForNTimeSteps(steps, model, saveEachStep=False): # TODO: may not use the 'save each step' at all
    """
    Progresses the model a given number of steps
    :param steps: number of steps to iterate (int)
    :param model:
    :param saveEachStep:
    :return:
    """
    modelList = []
    for step in range(steps):
        model.moveModelOneYear()
        if saveEachStep:
            modelList.append(dcp(model))
    return model, modelList

def rescaleAllocation(totalBudget, allocation):
    scaleRatio = totalBudget / sum(allocation)
    rescaledAllocation = [x * scaleRatio for x in allocation]
    return rescaledAllocation


def objectiveFunction(allocation, objective, model, availableBudget, fixedCosts, steps):
    thisModel = dcp(model)
    # scale the allocation appropriately
    if sum(allocation) == 0:
        scaledAllocation = dcp(allocation)
    else:
        scaledAllocation = rescaleAllocation(availableBudget, allocation)
    # add the fixed costs to the scaled allocation of available budget
    scaledAllocation = map(add, scaledAllocation, fixedCosts)
    newCoverages = {}
    programs = thisModel.programInfo.programs
    for idx in range(len(programs)):
        program = programs[idx]
        newCoverages[program.name] = program.costCurveFunc(scaledAllocation[idx]) / program.unrestrictedPopSize # TODO: use this or another metric?
    thisModel.applyNewProgramCoverages(newCoverages)
    modelThisRun = runModelForNTimeSteps(steps, thisModel)[0]
    outcome = modelThisRun.getOutcome(objective) * 1000.
    if objective == 'thrive':
        outcome *= -1
    return outcome

class OutputClass:
    def __init__(self, budgetBest, fval, exitflag, cleanOutputIterations, cleanOutputFuncCount, cleanOutputFvalVector, cleanOutputXVector):
        self.budgetBest = budgetBest
        self.fval = fval
        self.exitflag = exitflag
        self.cleanOutputIterations = cleanOutputIterations
        self.cleanOutputFuncCount = cleanOutputFuncCount
        self.cleanOutputFvalVector = cleanOutputFvalVector
        self.cleanOutputXVector = cleanOutputXVector

class Optimisation:
    def __init__(self, objectivesList, budgetMultiples, fileInfo, costCurveType='standard',
                 totalBudget=None, parallel=True, numRuns=10, numModelSteps=14):
        from multiprocessing import cpu_count
        import setup
        self.country = fileInfo[2]
        filePath, resultsPath = setup.getFilePath(root=fileInfo[0], bookDate=fileInfo[1], country=self.country)
        model = setup.setUpModel(filePath)
        self.budgetMultiples = budgetMultiples
        self.objectivesList = objectivesList
        self.programs = model.programInfo.programs
        self.numModelSteps = numModelSteps
        self.parallel = parallel
        self.numCPUs = cpu_count()
        self.numRuns = numRuns
        self.costCurveType = costCurveType
        self.timeSeries = None
        self.timeStepsPre = 1
        self.model = runModelForNTimeSteps(self.timeStepsPre, model)[0]
        for pop in self.model.populations:
            self.model._setConditionalProbabilities(pop) # TODO: include this in another function in future
        self.steps = numModelSteps - self.timeStepsPre #  TODO: implement so that goes to the max year of projections automatically
        for program in self.programs:
            program._setCostCoverageCurve()
        self.inititalProgramAllocations = self.getInitialProgramAllocations()
        self.getFixedCosts()
        self.totalBudget = totalBudget if totalBudget else sum(self.inititalProgramAllocations)
        self.availableBudget = self.totalBudget - sum(self.fixedCosts)
        self.kwargs = {'model': self.model, 'steps': self.steps,
                'availableBudget': self.availableBudget, 'fixedCosts': self.fixedCosts}
        # check that results directory exists and if not then create it
        import os
        self.resultDirectories = {}
        for objective in self.objectivesList + ['results']:
            self.resultDirectories[objective] = resultsPath +'/'+objective
            if not os.path.exists(self.resultDirectories[objective]):
                os.makedirs(self.resultDirectories[objective])


    ######### OPTIMISATION ##########

    def optimise(self):
        if self.parallel:
            self.parallelRun()
        else:
            self.seriesRun()
        return

    def parallelRun(self):
        jobs = self.getJobs()
        self.runJobs(jobs)
        return

    def seriesRun(self):
        for objective in self.objectivesList:
            for multiple in self.budgetMultiples:
                self.runOptimisation(multiple, objective)

    def getJobs(self):
        from multiprocessing import Process
        jobs = []
        for objective in self.objectivesList:
            for multiple in self.budgetMultiples:
                p = Process(target=self.runOptimisation, args=(multiple, objective))
                jobs.append(p)
        return jobs

    def runJobs(self, jobs):
        while jobs:
            thisRound = min(self.numCPUs, len(jobs))
            for process in range(thisRound):
                p = jobs[process]
                p.start()
            for process in range(thisRound): # this loop ensures this round waits until processes are finished
                p = jobs[process]
                p.join()
            jobs = jobs[thisRound:]
        return

    def runOptimisation(self, multiple, objective):
        import pso as pso
        import asd as asd
        from copy import deepcopy as dcp
        import time
        kwargs = dcp(self.kwargs)
        kwargs['availableBudget'] *= multiple
        kwargs['objective'] = objective
        xmin = [0.] * len(self.programs)
        xmax = [kwargs['availableBudget']] * len(self.programs)
        runOutputs = []
        for run in range(self.numRuns):
            now = time.time()
            x0, fopt = pso.pso(objectiveFunction, xmin, xmax, kwargs=kwargs, maxiter=45, swarmsize=100) # 45*100 should take about 5 hours
            print "Objective: " + str(objective)
            print "value * 1000: " + str(fopt)
            budgetBest, fval, exitflag, output = asd.asd(objectiveFunction, x0, kwargs, xmin=xmin,
                                                         xmax=xmax, verbose=1)
            print time.time() - now
            outputOneRun = OutputClass(budgetBest, fval, exitflag, output.iterations, output.funcCount, output.fval,
                                       output.x)
            runOutputs.append(outputOneRun)
        bestAllocation = self.findBestAllocation(runOutputs)
        # scaledAllocation = self.adjustAllocation(bestAllocation, kwargs) # PROBABLY DELETE
        scaledAllocation = rescaleAllocation(kwargs['availableBudget'], bestAllocation)
        # add fixed costs to optimal additional funds
        scaledAllocation = [spending + fixedCost for spending, fixedCost in zip(scaledAllocation, self.fixedCosts)]
        bestAllocationDict = self.createDictionary(scaledAllocation)
        self.writeToPickle(bestAllocationDict, multiple, objective)
        return

    def findBestAllocation(self, outputs):
        bestSample = max(outputs, key=lambda item: item.fval)
        return bestSample.budgetBest

    def createDictionary(self, allocations):
        """Ensure keys and values have matching orders"""
        keys = [program.name for program in self.programs]
        returnDict = {key: value for key, value in zip(keys, allocations)}
        return returnDict

    def getInitialProgramAllocations(self):
        allocations = []
        for program in self.programs:
            allocations.append(program.getSpending())
        return allocations

    def getFixedCosts(self):
        # TODO: could clean this up by seeting 'reference' as attribute of program
        self.fixedCosts = []
        for idx in range(len(self.programs)):
            self.fixedCosts.append(0)
            program = self.programs[idx]
            for prog in self.model.programInfo.referencePrograms:
                if program.name == prog:
                    spending = self.inititalProgramAllocations[idx]
                    self.fixedCosts[idx] = spending


    ########### FILE HANDLING ############

    def writeToPickle(self, allocation, multiple, objective):
        import pickle
        fileName = self.resultDirectories[objective]+'/'+ self.country+'_cascade_'+str(objective)+'_'+str(multiple)+'.pkl'
        outfile = open(fileName, 'wb')
        pickle.dump(allocation, outfile)
        return

    def readPickles(self):
        import pickle
        allocations = {}
        for objective in self.objectivesList:
            allocations[objective] = {}
            direc = self.resultDirectories[objective]
            for multiple in self.budgetMultiples:
                filename = '%s/%s_cascade_%s_%s.pkl' % (direc, self.country, objective, str(multiple))
                f = open(filename, 'rb')
                allocations[objective][multiple] = pickle.load(f)
                f.close()
        return allocations

    def getOutcome(self, allocation, objective):
        model = self.oneModelRunWithOutput(allocation)
        outcome = model.getOutcome(objective)
        return outcome

    def oneModelRunWithOutput(self, allocationDictionary):
        model = dcp(self.model)
        newCoverages = self.getCoverages(allocationDictionary)
        model.applyNewProgramCoverages(newCoverages)
        steps = self.numModelSteps - self.timeStepsPre
        model = runModelForNTimeSteps(steps, model)[0]
        return model

    def getOptimisedOutcomes(self, allocations):
        outcomes = {}
        for objective in self.objectivesList:
            outcomes[objective] = {}
            for multiple in self.budgetMultiples:
                thisAllocation = allocations[objective][multiple]
                outcomes[objective][multiple] = self.getOutcome(thisAllocation, objective)
        return outcomes

    def getCurrentOutcome(self, currentSpending):
        currentOutcome = {}
        for objective in self.objectivesList:
            currentOutcome[objective] = {}
            currentOutcome[objective]['current spending'] = self.getOutcome(currentSpending, objective)
        return currentOutcome

    def getZeroSpendingOutcome(self):
        zeroSpending = {program.name: 0 for program in self.programs}
        baseline = {}
        for objective in self.objectivesList:
            baseline[objective] = {}
            baseline[objective]['zero spending'] = self.getOutcome(zeroSpending, objective)
        return baseline

    def getCoverages(self, allocations):
        newCoverages = {}
        for program in self.programs:
            newCoverages[program.name] = program.costCurveFunc(allocations[program.name]) / program.unrestrictedPopSize
        return newCoverages

    def writeAllResults(self):
        baselineOutcome = self.getZeroSpendingOutcome()
        currentSpending = self.createDictionary(self.inititalProgramAllocations)
        currentOutcome = self.getCurrentOutcome(currentSpending)
        optimisedAllocations = self.readPickles()
        optimisedOutcomes = self.getOptimisedOutcomes(optimisedAllocations)
        self.writeOutcomesToCSV(baselineOutcome,currentOutcome, optimisedOutcomes)
        self.writeAllocationsToCSV(currentSpending, optimisedAllocations)

    def writeOutcomesToCSV(self, baseline, current, optimised):
        import csv
        allOutcomes = {}
        for objective in self.objectivesList:
            allOutcomes[objective] = {}
            allOutcomes[objective].update(baseline[objective])
            allOutcomes[objective].update(current[objective])
            allOutcomes[objective].update(optimised[objective])
        direc = self.resultDirectories['results']
        filename = '%s/%s_outcomes.csv'%(direc, self.country)
        budgets =  ['zero spending','current spending'] + self.budgetMultiples
        with open(filename, 'wb') as f:
            w = csv.writer(f)
            for objective in self.objectivesList:
                w.writerow([objective])
                for multiple in budgets:
                    outcome = allOutcomes[objective][multiple]
                    w.writerow(['',multiple, outcome])

    def writeAllocationsToCSV(self, current, optimised):
        import csv
        from collections import OrderedDict
        allSpending = {}
        for objective in self.objectivesList:
            allSpending[objective] = {}
            allSpending[objective].update(current)
            allSpending[objective].update(optimised[objective])
        direc = self.resultDirectories['results']
        filename = '%s/%s_allocations.csv'%(direc, self.country)
        with open(filename, 'wb') as f:
            w = csv.writer(f)
            sortedCurrent = OrderedDict(sorted(current.items()))
            w.writerow(['current'] + sortedCurrent.keys())
            w.writerow(['']+ sortedCurrent.values())
            for objective in self.objectivesList:
                w.writerow([''])
                w.writerow([objective] + sorted(optimised[objective][self.budgetMultiples[0]].keys()))
                for multiple in self.budgetMultiples:
                    allocation = OrderedDict(sorted(optimised[objective][multiple].items()))
                    w.writerow([multiple] + allocation.values())

    # def generateCostCurves(self, model, resultsFileStem=None,
    #                        budget=None, cascade=None, scale=True):
    #     '''Generates & stores cost curves in dictionary by intervention.'''
    #     import costcov
    #     costCov = costcov.Costcov()
    #     targetPopSize = self.getTargetPopSizeFromModelInstance(model) # TODO: this function could use calculations in the spreadsheet (target pop tab)
    #     totalPopSize = self.getAllPopSizes(model)
    #     costCurvesDict = {}
    #     for intervention in self.data.interventionList:
    #         costCurvesDict[intervention] = costCov.getCostCoverageCurve(self.costCoverageInfo[intervention],
    #                                                                     targetPopSize[intervention], totalPopSize, self.costCurveType)
    #     if resultsFileStem is not None:  # save plot
    #         costCov.saveCurvesToPNG(costCurvesDict, self.costCurveType, self.data.interventionList, targetPopSize, resultsFileStem,
    #                                 budget, cascade, scale=scale)
    #     return costCurvesDict

    def getAllPopSizes(self, model):
        allCompartments = model.listOfAgeCompartments + model.listOfReproductiveAgeCompartments + model.listOfPregnantWomenAgeCompartments
        popSizes = {pop.name: pop.getTotalPopulation() for pop in allCompartments}
        return popSizes
