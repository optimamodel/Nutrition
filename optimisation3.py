from copy import deepcopy as dcp
from multiprocessing import cpu_count, Process
from numpy import array, all, random

def runModelForNTimeSteps(steps, model):
    """
    Progresses the model a given number of steps
    :param steps: number of steps to iterate (int)
    :param model:
    :param saveEachStep:
    :return:
    """
    for step in range(steps):
        model.moveModelOneYear()
    return model

def rescaleAllocation(totalBudget, allocation):
    scaleRatio = totalBudget / sum(allocation)
    rescaledAllocation = [x * scaleRatio for x in allocation]
    return rescaledAllocation


def objectiveFunction(allocation, objective, model, availableBudget, fixedCosts, indxToKeep, steps):
    thisModel = dcp(model)
    totalSpending = dcp(fixedCosts)
    # scale the allocation appropriately
    if sum(allocation) == 0:
        scaledAllocation = dcp(allocation)
    else:
        scaledAllocation = rescaleAllocation(availableBudget, allocation)
    newCoverages = {}
    programs = thisModel.programInfo.programs
    for idx, program in enumerate(programs):
        if idx in indxToKeep:
            totalSpending[idx] += scaledAllocation.pop(0) # utilising preserved order of indxToKeep
        newCoverages[program.name] = program.costCurveFunc(totalSpending[idx]) / program.unrestrictedPopSize
    thisModel.runSimulationFromOptimisation(newCoverages)
    outcome = thisModel.getOutcome(objective) * 1000.
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

class MyBounds(object):
    def __init__(self, xmin, xmax):
        self.xmax = array(xmax)
        self.xmin = array(xmin)
    def __call__(self, **kwargs):
        x = kwargs['x_new']
        tmax = bool(all(x <= self.xmax))
        tmin = bool(all(x >= self.xmin))
        return tmax and tmin


class Optimisation:
    def __init__(self, objectivesList, budgetMultiples, fileInfo, costCurveType='standard',
                 totalBudget=None, parallel=True, numRuns=1, filterProgs=True):
        import setup
        self.country = fileInfo[2]
        filePath, resultsPath = setup.getFilePath(root=fileInfo[0], bookDate=fileInfo[1], country=self.country)
        self.model = setup.setUpModel(filePath, adjustCoverage=False, optimise=True) # model has already moved 1 year
        self.budgetMultiples = budgetMultiples
        self.objectivesList = objectivesList
        self.filterProgs = filterProgs
        self.programs = self.model.programInfo.programs
        self.numModelSteps = len(self.model.constants.simulationYears) # default to period for which data is supplied
        self.parallel = parallel
        self.numCPUs = cpu_count()
        self.numRuns = numRuns
        self.costCurveType = costCurveType
        self.timeSeries = None
        self.timeStepsPre = 1
        self.steps = self.numModelSteps - self.timeStepsPre
        for program in self.programs:
            program._setCostCoverageCurve()
        self.initialProgramAllocations = self.getInitialProgramAllocations()
        self.getFixedCosts()
        # either distribute manually entered budget, or distribute costs which are not fixed
        if totalBudget:
            self.availableBudget = totalBudget
        else:
            self.availableBudget = sum(self.initialProgramAllocations) - sum(self.fixedCosts)
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
        from scipy.optimize import basinhopping
        random.seed(1)
        kwargs = dcp(self.kwargs)
        kwargs['availableBudget'] *= multiple
        kwargs['objective'] = objective
        if self.filterProgs:
            indxToKeep = self._selectProgsForObjective(objective)
            kwargs['indxToKeep'] = indxToKeep
            xmin = [0.] * len(indxToKeep)
            xmax = [kwargs['availableBudget']] * len(indxToKeep)
            # bounds = [(xmin[0], xmax[0])] * len(indxToKeep)
        else:
            kwargs['indxToKeep'] = [i for i in range(len(self.programs))]
            xmin = [0.] * len(self.programs)
            xmax = [kwargs['availableBudget']] * len(self.programs)
            # bounds = [(xmin[0], xmax[0])] * len(self.programs)
        # args = (kwargs['objective'], kwargs['model'], kwargs['availableBudget'], kwargs['fixedCosts'], kwargs['indxToKeep'], kwargs['steps'])
        # myBounds = MyBounds(xmin, xmax)
        runOutputs = []
        for run in range(self.numRuns):
            now = time.time()
            x0, fopt = pso.pso(objectiveFunction, xmin, xmax, kwargs=kwargs, maxiter=300, swarmsize=50) # should be about 13 hours for 100*120
            print "Objective: " + str(objective)
            print "value * 1000: " + str(fopt)
            # res = basinhopping(objectiveFunction, x0, minimizer_kwargs={'args':args, 'method':'L-BFGS-B'}, accept_test=myBounds, disp=True)
            budgetBest, fval, exitflag, output = asd.asd(objectiveFunction, x0, kwargs, xmin=xmin,
                                                         xmax=xmax, verbose=0)
            # res = minimize(objectiveFunction, x0, method ='L-BFGS-B', args=args, options={'disp':True}, bounds=bounds)
            # bestAllocation = res.x
            print str((time.time() - now)/(60*60)) + ' hours'
            print "----------"
            outputOneRun = OutputClass(budgetBest, fval, exitflag, output.iterations, output.funcCount, output.fval,
                                       output.x)
            runOutputs.append(outputOneRun)
        bestAllocation = self.findBestAllocation(runOutputs)
        scaledAllocation = rescaleAllocation(kwargs['availableBudget'], bestAllocation)
        # add fixed costs to optimal additional funds
        indxToKeep = kwargs['indxToKeep']
        totalAllocation = []
        for idx, value in enumerate(self.fixedCosts):
            totalAllocation.append(value)
            if idx in indxToKeep:
                totalAllocation[idx] += scaledAllocation.pop(0)
        # scaledAllocation = [spending + fixedCost for spending, fixedCost in zip(scaledAllocation, self.fixedCosts)]
        bestAllocationDict = self.createDictionary(totalAllocation)
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
        for idx, program in enumerate(self.programs):
            if program.name in self.model.programInfo.referencePrograms:
                self.fixedCosts.append(self.initialProgramAllocations[idx])
            else:
                self.fixedCosts.append(0)

    def _selectProgsForObjective(self, objective):
        threshold = 0.5
        newCov = 1.
        indxToKeep = []
        # compare with 0 case # TODO: could make this attribute for all processes to share
        zeroCov = {prog.name: 0 for prog in self.programs}
        zeroModel = dcp(self.model)
        # get baseline case
        zeroModel.runSimulationGivenCoverage(zeroCov, restrictedCov=True)
        zeroOutcome = zeroModel.getOutcome(objective)
        for indx, program in enumerate(self.programs):
            thisModel = dcp(self.model)
            thisCov = dcp(zeroCov)
            thisCov[program.name] = newCov
            if program.malariaTwin:
                thisCov[program.name + ' (malaria area)'] = newCov
            thisModel.runSimulationGivenCoverage(thisCov, restrictedCov=True)
            outcome = thisModel.getOutcome(objective)
            if abs((outcome - zeroOutcome) / zeroOutcome) * 100. > threshold:  # no impact
                indxToKeep.append(indx)
                for twinIndx, twin in enumerate(self.programs): # TODO: shouldn't have to search through twice
                    if twin.name == program.name + ' (malaria area)':
                        indxToKeep.append(twinIndx)
        return indxToKeep

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
        model.runSimulationFromOptimisation(newCoverages)
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
        currentSpending = self.createDictionary(self.initialProgramAllocations)
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
            w.writerow([''] + sortedCurrent.values())
            for objective in self.objectivesList:
                w.writerow([''])
                w.writerow([objective] + sorted(optimised[objective][self.budgetMultiples[0]].keys()))
                for multiple in self.budgetMultiples:
                    allocation = OrderedDict(sorted(optimised[objective][multiple].items()))
                    w.writerow([multiple] + allocation.values())