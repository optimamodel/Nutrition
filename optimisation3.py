import os
from copy import deepcopy as dcp
import play
import cPickle as pickle
from multiprocessing import cpu_count, Process
from numpy import array, random, append, linspace, argmax, zeros, nonzero, inf, argmin
from scipy.interpolate import pchip
from math import ceil
from csv import writer, reader
from itertools import izip
from collections import OrderedDict
from datetime import date

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
    new = sum(allocation)
    if new == 0:
        rescaledAllocation = dcp(allocation)
    else:
        scaleRatio = totalBudget / new
        rescaledAllocation = [x * scaleRatio for x in allocation]
    # try:
    #     scaleRatio = totalBudget / sum(allocation)
    #     rescaledAllocation = [x * scaleRatio for x in allocation]
    # except ZeroDivisionError:
    #     rescaledAllocation = dcp(allocation)
    return rescaledAllocation

def runJobs(jobs, max_jobs):
    while jobs:
        thisRound = min(max_jobs, len(jobs))
        for process in range(thisRound):
            p = jobs[process]
            p.start()
        for process in range(thisRound):  # this loop ensures this round waits until processes are finished
            p = jobs[process]
            p.join()
        jobs = jobs[thisRound:]
    return

def _addFixedAllocations(allocations, fixedAllocations, indxList):
    """Assumes order is preserved from original list"""
    modified = dcp(allocations)
    for i, j in enumerate(indxList):
        modified[j] += fixedAllocations[i]
    return modified

def objectiveFunction(allocation, objective, model, freeFunds, fixedAllocations, indxToKeep):
    thisModel = dcp(model)
    totalAllocations = dcp(fixedAllocations)
    # scale the allocation appropriately
    scaledAllocation = rescaleAllocation(freeFunds, allocation)
    newCoverages = {}
    programs = thisModel.programInfo.programs
    totalAllocations = _addFixedAllocations(totalAllocations, scaledAllocation, indxToKeep)
    for idx, program in enumerate(programs):
        newCoverages[program.name] = program.costCurveFunc(totalAllocations[idx]) / program.unrestrictedPopSize
    thisModel.runSimulationFromOptimisation(newCoverages)
    outcome = thisModel.getOutcome(objective) * 1000.
    if objective == 'thrive' or objective == 'healthy_children':
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

class Optimisation: # TODO: would like
    def __init__(self, objectives, budgetMultiples, fileInfo, resultsPath=None, fixCurrentAllocations=False,
                 additionalFunds=0, removeCurrentFunds=False, numYears=None, costCurveType='linear',
                 parallel=True, numCPUs=None, numRuns=1, filterProgs=True):
        root, country, name, analysisType = fileInfo
        self.name = name
        filePath = play.getFilePath(root=root, country=country, name=name)
        if not resultsPath:
            resultsPath = play.getResultsDir(root=root, country=self.name, analysisType=analysisType)
        self.createDirectory(resultsPath) # TODO: probably only want this to happen when calling 'optimise'
        self.model = play.setUpModel(filePath, adjustCoverage=False, optimise=True, numYears=numYears) # model has already moved 1 year
        self.budgetMultiples = budgetMultiples # TODO: would like if get a budget of 0, that this just runs the model w/o optimisation.
        self.objectives = objectives
        self.fixCurrentAllocations = fixCurrentAllocations
        self.removeCurrentFunds = removeCurrentFunds
        self.additionalFunds = additionalFunds
        self.filterProgs = filterProgs
        self.BOCs = {}
        self.programs = self.model.programInfo.programs
        self.parallel = parallel
        if numCPUs:
            self.numCPUs = numCPUs
        else:
            self.numCPUs = cpu_count()
        self.numRuns = numRuns
        # self.costCurveType = costCurveType # TODO: currently doesn't do anything.
        self.timeSeries = None
        for program in self.programs:
            program._setCostCoverageCurve()
        self.calculateAllocations(fixCurrentAllocations)
        self.kwargs = {'model': self.model,
                'freeFunds': self.freeFunds, 'fixedAllocations': self.fixedAllocations}

    ######### FILE HANDLING #########

    def createDirectory(self, resultsPath):
        # check that results directory exists and if not then create it
        self.resultDir = resultsPath
        if not os.path.exists(self.resultDir):
            os.makedirs(self.resultDir)

    ######### SETUP ############

    def calculateAllocations(self, fixCurrentAllocations):
        """
        Designed so that currentAllocations >= fixedAllocations >= referenceAllocations.
        referenceAllocations: these allocations cannot be reduced because it is impractical to do so.
        fixedAllocations: this is funding which cannot be reduced because of the user's wishes.
        currentAllocations: this is the total current funding (incl. reference & fixed allocations) determined by program initial coverage.
        :param fixCurrentAllocations:
        :return:
        """
        self.referenceAllocations = self.getReferenceAllocations()
        self.currentAllocations, self.scaleFactor = self.scaleCostsForCurrentExpenditure()
        self.fixedAllocations = self.getFixedAllocations(fixCurrentAllocations)
        self.freeFunds = self.getFreeFunds(fixCurrentAllocations)


    def getReferenceAllocations(self):
        """
        Reference programs are not included in nutrition budgets, therefore these must be removed before future calculations.
        :return: 
        """
        referenceAllocations = []
        for program in self.programs:
            if program.reference:
                referenceAllocations.append(program.getSpending())
            else:
                referenceAllocations.append(0)
        return referenceAllocations

    def getCurrentAllocations(self):
        allocations = []
        for program in self.programs:
            allocations.append(program.getSpending())
        return allocations

    def getFixedAllocations(self, fixCurrentAllocations):
        """
        Fixed allocations will contain reference allocations as well, for easy use in the objective function.
        Reference progs stored separately for ease of model output.
        :param fixCurrentAllocations:
        :return:
        """
        if fixCurrentAllocations:
            fixedAllocations = dcp(self.currentAllocations)
        else:
            fixedAllocations = dcp(self.referenceAllocations)
        return fixedAllocations
            
    def scaleCostsForCurrentExpenditure(self):
        # if there is a current budget specified, scale unit costs so that current coverages yield this budget (excluding reference progs).
        # ::WARNING:: Currently, this should only be used for LINEAR cost curves
        # specificBudget / calculatedBudget * oldUnitCost = newUnitCost
        currentAllocationsBefore = self.getCurrentAllocations()
        if self.model.programInfo.currentExpenditure:
            currentCalculated = sum(currentAllocationsBefore) - sum(self.referenceAllocations)
            scaleFactor = self.model.programInfo.currentExpenditure / currentCalculated
            for program in self.programs:
                if not program.reference:
                    program.scaleUnitCosts(scaleFactor)
        else:
            scaleFactor = 1
        return self.getCurrentAllocations(), scaleFactor

    def getFreeFunds(self, fixCurrent):
        """
        freeFunds = currentExpenditure + additionalFunds - fixedFunds (if not remove current funds)
        freeFunds = additional (if want to remove current funds)

        fixedFunds includes both reference programs as well as currentExpenditure, if the latter is to be fixed.
        I.e. if all of the currentExpenditure is fixed, freeFunds = additionalFunds.
        :return:
        """
        if self.removeCurrentFunds and fixCurrent:
            raise Exception("::Error: Cannot remove current funds and fix current funds simultaneously::")
        elif self.removeCurrentFunds and (not fixCurrent): # this is additional to reference spending
            freeFunds = self.additionalFunds
        elif not self.removeCurrentFunds:
            freeFunds = sum(self.currentAllocations) - sum(self.fixedAllocations) + self.additionalFunds
        return freeFunds

    ######### OPTIMISATION ##########

    def optimise(self):
        print ""
        print "::STARTING NEW REGION::"
        print self.name
        print " "
        newBudgets = self.checkForZeroBudget()
        if self.parallel:
            self.parallelRun(newBudgets)
        else:
            self.seriesRun(newBudgets)
        return

    def parallelRun(self, newBudgets):
        jobs = self.getJobs(newBudgets)
        self.runJobs(jobs)
        return

    def seriesRun(self, newBudgets):
        for objective in self.objectives:
            for multiple in newBudgets:
                self.runOptimisation(multiple, objective)

    def checkForZeroBudget(self):
        """For 0 free funds, spending is equal to the fixed costs"""
        if 0 in self.budgetMultiples:
            newBudgets = filter(lambda x: x> 0, self.budgetMultiples)
            # output fixed spending
            for objective in self.objectives:
                allocationDict = self.createDictionary(self.fixedAllocations)
                self.writeToPickle(allocationDict, 0, objective)
        else:
            newBudgets = self.budgetMultiples
        return newBudgets

    def getJobs(self, newBudgets):
        jobs = []
        for objective in self.objectives:
            for multiple in newBudgets:
                p = Process(target=self.runOptimisation, args=(multiple, objective))
                jobs.append(p)
        return jobs

    def runJobs(self, jobs): # TODO: version of this in module scope now
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
        random.seed(1)
        kwargs = dcp(self.kwargs)
        kwargs['freeFunds'] *= multiple
        if kwargs['freeFunds'] != 0:
            kwargs['objective'] = objective
            indxToKeep = self._selectProgsForObjective(objective)
            kwargs['indxToKeep'] = indxToKeep
            xmin = [0.] * len(indxToKeep)
            xmax = [kwargs['freeFunds']] * len(indxToKeep) # TODO: could make this cost of saturation.
            runOutputs = []
            for run in range(self.numRuns):
                now = time.time() # TODO: could make 9600 iterations -- 100*100
                x0, fopt = pso.pso(objectiveFunction, xmin, xmax, kwargs=kwargs, maxiter=100, swarmsize=50)
                print "Objective: " + str(objective)
                print "Multiple: " + str(multiple)
                print "value: " + str(fopt/1000.)
                budgetBest, fval, exitflag, output = asd.asd(objectiveFunction, x0, kwargs, xmin=xmin,
                                                             xmax=xmax, verbose=0)
                print str((time.time() - now)/(60*60)) + ' hours'
                print "----------"
                outputOneRun = OutputClass(budgetBest, fval, exitflag, output.iterations, output.funcCount, output.fval,
                                           output.x)
                runOutputs.append(outputOneRun)
            bestAllocation = self.findBestAllocation(runOutputs)
            scaledAllocation = rescaleAllocation(kwargs['freeFunds'], bestAllocation)
            totalAllocation = _addFixedAllocations(self.fixedAllocations, scaledAllocation, kwargs['indxToKeep'])
            bestAllocationDict = self.createDictionary(totalAllocation)
        else:
            # if no money to distribute, return the fixed costs
            bestAllocationDict = self.createDictionary(self.fixedAllocations)
        self.writeToPickle(bestAllocationDict, multiple, objective)
        return

    def findBestAllocation(self, outputs):
        bestSample = min(outputs, key=lambda item: item.fval)
        return bestSample.budgetBest

    def createDictionary(self, allocations):
        """Ensure keys and values have matching orders"""
        keys = [program.name for program in self.programs]
        returnDict = {key: value for key, value in zip(keys, allocations)}
        return returnDict

    def _selectProgsForObjective(self, objective):
        if self.filterProgs:
            threshold = 0.5
            newCov = 1.
            indxToKeep = []
            # compare with 0 case
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
        else: # keep all
            indxToKeep = [i for i in range(len(self.programs))]
        return indxToKeep

    def interpolateBOC(self, objective, spending, outcome, optimiseCurrent):
        # need BOC for each objective in region
        # spending, outcome = self.getBOCvectors(objective)
        self.BOCs[objective] = {}
        self.BOCs[objective][optimiseCurrent] = pchip(spending, outcome, extrapolate=False)

    def getBOCvectors(self, objective):
        spending = array([])
        outcome = array([])
        for multiple in self.budgetMultiples:
            spending = append(spending, multiple * self.freeFunds)
            filePath = '{}/{}_{}_{}.pkl'.format(self.resultDir, self.name, objective, multiple)
            f = open(filePath, 'rb')
            thisAllocation = pickle.load(f)
            f.close()
            output = self.oneModelRunWithOutput(thisAllocation).getOutcome(objective)
            outcome = append(outcome, output)
        return spending, outcome


    ########### FILE HANDLING ############

    def writeToPickle(self, allocation, multiple, objective):
        fileName = '{}/{}_{}_{}.pkl'.format(self.resultDir, self.name, objective, multiple)
        outfile = open(fileName, 'wb')
        pickle.dump(allocation, outfile)
        return

    def readPickles(self):
        allocations = {}
        for objective in self.objectives:
            allocations[objective] = {}
            for multiple in self.budgetMultiples:
                filename = '{}/{}_{}_{}.pkl'.format(self.resultDir, self.name, objective, multiple)
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
        for objective in self.objectives:
            outcomes[objective] = {}
            for multiple in self.budgetMultiples:
                thisAllocation = allocations[objective][multiple]
                outcomes[objective][multiple] = self.getOutcome(thisAllocation, objective)
        return outcomes

    def getCurrentOutcome(self, currentSpending):
        currentOutcome = {}
        for objective in self.objectives:
            currentOutcome[objective] = {}
            currentOutcome[objective]['current spending'] = self.getOutcome(currentSpending, objective)
        return currentOutcome

    def getZeroSpendingOutcome(self):
        zeroSpending = {program.name: 0 for program in self.programs}
        baseline = {}
        for objective in self.objectives:
            baseline[objective] = {}
            baseline[objective]['zero spending'] = self.getOutcome(zeroSpending, objective)
        return baseline

    def getReferenceOutcome(self, refSpending):
        reference = {}
        for objective in self.objectives:
            reference[objective] = {}
            reference[objective]['reference spending'] = self.getOutcome(refSpending, objective)
        return reference

    def getCoverages(self, allocations):
        newCoverages = {}
        for program in self.programs:
            newCoverages[program.name] = program.costCurveFunc(allocations[program.name]) / program.unrestrictedPopSize
        return newCoverages

    def writeAllResults(self):
        currentSpending = self.createDictionary(self.currentAllocations)
        currentOutcome = self.getCurrentOutcome(currentSpending)
        referenceSpending = self.createDictionary(self.referenceAllocations)
        referenceOutcome = self.getReferenceOutcome(referenceSpending)
        optimisedAllocations = self.readPickles()
        optimisedOutcomes = self.getOptimisedOutcomes(optimisedAllocations)
        currentAdditionalList = [a-b for a,b in zip(self.currentAllocations, self.referenceAllocations)]
        currentAdditional = self.createDictionary(currentAdditionalList)
        optimisedAdditional = self.getOptimisedAdditional(optimisedAllocations)
        coverages = self.getOptimalCoverages(optimisedAllocations)
        self.writeOutcomesToCSV(referenceOutcome, currentOutcome, optimisedOutcomes)
        self.writeAllocationsToCSV(referenceSpending, currentAdditional, optimisedAdditional)
        self.writeCoveragesToCSV(coverages)

    def getOptimisedAdditional(self, optimised):
        fixedCostsDict = self.createDictionary(self.fixedAllocations)
        optimisedAdditional = {}
        for objective in self.objectives:
            optimisedAdditional[objective] = {}
            for multiple in self.budgetMultiples:
                additionalFunds = optimised[objective][multiple]
                optimisedAdditional[objective][multiple] = {}
                for programName in additionalFunds.iterkeys():
                    optimisedAdditional[objective][multiple][programName] = additionalFunds[programName] - fixedCostsDict[programName]
        return optimisedAdditional

    def getOptimalCoverages(self, optimisedAllocations):
        coverages = {}
        for objective in self.objectives:
            coverages[objective] = {}
            for multiple in self.budgetMultiples:
                coverages[objective][multiple] = {}
                allocations = optimisedAllocations[objective][multiple]
                for program in self.programs:
                    # this gives the restricted coverage
                    coverages[objective][multiple][program.name] = "{0:.2f}".format((program.costCurveFunc(allocations[program.name]) / program.restrictedPopSize) * 100.)
        return coverages

    def writeCoveragesToCSV(self, coverages):
        import csv
        from collections import OrderedDict
        filename = '{}/{}_coverages.csv'.format(self.resultDir, self.name)
        with open(filename, 'wb') as f:
            w = csv.writer(f)
            for objective in self.objectives:
                w.writerow([''])
                w.writerow([objective] + sorted(coverages[objective][self.budgetMultiples[0]].keys()))
                for multiple in self.budgetMultiples:
                    coverage = OrderedDict(sorted(coverages[objective][multiple].items()))
                    w.writerow([multiple] + coverage.values())

    def writeOutcomesToCSV(self, reference, current, optimised):
        import csv
        allOutcomes = {}
        for objective in self.objectives:
            allOutcomes[objective] = {}
            allOutcomes[objective].update(reference[objective])
            allOutcomes[objective].update(current[objective])
            allOutcomes[objective].update(optimised[objective])
        filename = '{}/{}_outcomes.csv'.format(self.resultDir, self.name)
        budgets =  ['reference spending', 'current spending'] + self.budgetMultiples
        with open(filename, 'wb') as f:
            w = csv.writer(f)
            for objective in self.objectives:
                w.writerow([objective])
                for multiple in budgets:
                    outcome = allOutcomes[objective][multiple]
                    w.writerow(['',multiple, outcome])

    def writeAllocationsToCSV(self, reference, current, optimised):
        import csv
        from collections import OrderedDict
        allSpending = {}
        for objective in self.objectives: # do i use this loop?
            allSpending[objective] = {}
            allSpending[objective].update(current)
            allSpending[objective].update(reference)
            allSpending[objective].update(optimised[objective])
        filename = '{}/{}_allocations.csv'.format(self.resultDir, self.name)
        with open(filename, 'wb') as f:
            w = csv.writer(f)
            sortedRef = OrderedDict(sorted(reference.items()))
            w.writerow(['reference'] + sortedRef.keys())
            w.writerow([''] + sortedRef.values())
            w.writerow([''])
            sortedCurrent = OrderedDict(sorted(current.items()))
            w.writerow(['current'] + sortedCurrent.keys())
            w.writerow([''] + sortedCurrent.values())
            for objective in self.objectives:
                w.writerow([''])
                w.writerow([objective] + sorted(optimised[objective][self.budgetMultiples[0]].keys()))
                for multiple in self.budgetMultiples:
                    allocation = OrderedDict(sorted(optimised[objective][multiple].items()))
                    w.writerow([multiple] + allocation.values())

class GeospatialOptimisation:
    def __init__(self, objectives, fileInfo, regionNames, numYears=None, costCurveType='linear'):
        self.root, self.country = fileInfo
        thisDate = date.today().strftime('%Y%b%d')
        self.resultsDir = '{}/Results/{}/geospatial/{}'.format(self.root, self.country, thisDate)
        self.objectives = objectives
        self.budgetMultiples = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1]
        self.regionNames = regionNames
        self.numYears = numYears
        self.numRegions = len(regionNames)
        self.scenarios = BudgetScenarios(self.root+'/input_spreadsheets/'+self.country+'/optimisationBudgets.xlsx').getScenarios()  # TODO: super ugly file-finding
        self.BOCs = {}
        self.getBOCdirs()

    def getBOCdirs(self):
        self.BOCdir = {}
        for objective in self.objectives:
            self.BOCdir[objective] = '{}/{}/BOCs'.format(self.resultsDir, objective)

    def getNationalCurrentSpending(self):
        nationalFunds = 0
        for name in self.regionNames:
            fileInfo = [self.root, self.country+'/regions/', name, '']
            thisRegion = Optimisation([], [], fileInfo, fixCurrentAllocations=False)
            nationalFunds += thisRegion.freeFunds
        return nationalFunds

    def readBOC(self, region, objective, optimiseCurrent):
        filename = '{}/{}_optimCurr_{}.csv'.format(self.BOCdir[objective], region, optimiseCurrent)
        with open(filename, 'rb') as f:
            regionalSpending = []
            regionalOutcome = []
            r = reader(f)
            for row in r:
                regionalSpending.append(row[0])
                regionalOutcome.append(row[1])
        # remove column headers
        regionalSpending = array(regionalSpending[1:])
        regionalOutcome = array(regionalOutcome[1:])
        return regionalSpending, regionalOutcome

    def interpolateBOCs(self, regions, objective, options):
        optimiseCurrent = options[1]
        for region in regions:
            spending, outcome = self.readBOC(region.name, objective, optimiseCurrent)
            region.interpolateBOC(objective, spending, outcome, optimiseCurrent)
        self.writeBOCs(regions, objective, optimiseCurrent)
        return regions

    def writeBOCs(self, regions, objective, optimiseCurrent):
        filename = '{}/BOCs_optimCurr_{}.csv'.format(self.BOCdir[objective], optimiseCurrent)
        headers = ['spending'] + [region.name for region in regions]
        minSpend = min(regions[0].BOCs[objective][optimiseCurrent].x) # all regions should have the same min and max
        maxSpend = max(regions[0].BOCs[objective][optimiseCurrent].x)
        newSpending = linspace(minSpend, maxSpend, 2000)
        regionalOutcomes = []
        with open(filename, 'wb') as f:
            w = writer(f)
            w.writerow(headers)
            for region in regions: # TODO: where to start and end spending to generate the BOC?
                thisBOC = region.BOCs[objective][optimiseCurrent]
                interpolated = thisBOC(newSpending)
                regionalOutcomes.append(interpolated)
            columnLists = [newSpending] + regionalOutcomes
            w.writerows(zip(*columnLists))

    def getRegionalBOCs(self):
        """Scenarios split up into scenario 3 and other scenarios, since 1,2,4 can all use the same BOC,
        while 3 requires a different curve which doesn't begin with optimised current spending.
        Creates optimisation objects with correct parameters for these two kinds of BOCs"""
        nationalFunds = self.getNationalCurrentSpending()
        thisScenario = 'Scenario 3'
        otherScenarios = ['Scenario 1', 'Scenario 2', 'Scenario 4']
        jobs = []
        # scenario 3 is the only scenario using a non-optimised current allocation
        if thisScenario in self.scenarios:
            # true, false, false, nationalExtraFunds
            fixCurrent, optimiseCurrent, removeCurrent, additionalFunds = self.scenarios[thisScenario]
            jobs += self.getBOCjobs(fixCurrent, optimiseCurrent, removeCurrent, additionalFunds)
        # the other three scenarios will use the same BOC
        if any(scenario in self.scenarios for scenario in otherScenarios):
            # these params chosen so we generate points for the whole curve (0-maxspending)
            fixCurrent = False
            optimiseCurrent = True
            removeCurrent = True
            maxKey = max(self.scenarios, key=lambda i: i[-1])
            additionalFunds = nationalFunds + self.scenarios[maxKey][-1] # national + max additional
            jobs += self.getBOCjobs(fixCurrent, optimiseCurrent, removeCurrent, additionalFunds)
        numRegions = int(50/9)
        runJobs(jobs, numRegions)

    def getBOCjobs(self, fixCurrent, optimiseCurrent, removeCurrent, additionalFunds):
        jobs = []
        for objective in self.objectives:
            for name in self.regionNames:
                fileInfo = [self.root, self.country + '/regions/', name, '']
                resultsPath = '{}/optimCurr_{}'.format(self.BOCdir[objective], optimiseCurrent)
                thisRegion = Optimisation([objective], self.budgetMultiples, fileInfo,
                                          resultsPath=resultsPath,
                                          fixCurrentAllocations=fixCurrent, removeCurrentFunds=removeCurrent,
                                          additionalFunds=additionalFunds, numYears=self.numYears, filterProgs=False)
                BOCexists = self.checkForBOC(name, objective, optimiseCurrent)
                if not BOCexists:
                    prc = Process(target=self.optimiseAndWrite, args=(thisRegion, objective, optimiseCurrent))
                    jobs.append(prc)
        return jobs

    def optimiseAndWrite(self, region, objective, optimiseCurrent):
        region.optimise()
        self.writeBudgetOutcome(region, objective, optimiseCurrent)

    def writeBudgetOutcome(self, region, objective, optimiseCurrent):
        spending, outcome = region.getBOCvectors(objective)
        filename = '{}/{}_optimCurr_{}.csv'.format(self.BOCdir[objective], region.name, optimiseCurrent)
        with open(filename, 'wb') as f:
            w = writer(f)
            w.writerow(['spending', 'outcome'])
            w.writerows(izip(spending, outcome))

    def checkForBOC(self, region, objective, optimiseCurrent):
        if os.path.exists(self.BOCdir[objective]):
            filename = '{}/{}_optimCurr_{}.csv'.format(self.BOCdir[objective], region, optimiseCurrent)
            return os.path.isfile(filename)
        else:
            return False

    def setUpRegions(self, scenario, options):
        fixCurrent, optimiseCurrent, removeCurrent, additionalFunds = options
        regions = []
        for name in self.regionNames:
            fileInfo = [self.root, self.country+'/regions/', name, '']
            thisRegion = Optimisation(self.objectives, self.budgetMultiples, fileInfo, fixCurrentAllocations=fixCurrent,
                                      removeCurrentFunds=removeCurrent, additionalFunds=additionalFunds, numYears=self.numYears,
                                      filterProgs=False)
            regions.append(thisRegion)
        return regions


    def optimiseScenarios(self):
        """
        Each scenario is run in series because of the large number of parallel jobs for each regions.
        :return:
        """
        self.getRegionalBOCs()
        # options: [fixedAllocations, progOpt, removeCurrent, additionalFunds]
        for scenario, options in self.scenarios.iteritems(): # TODO: scenario 1 can be taken directly from BOCs
            formattedScenario = scenario.lower().replace(' ', '')
            regions = self.setUpRegions(scenario, options)
            allPrograms = [prog.name for prog in regions[0].programs]
            filename = self.createCSV(formattedScenario)
            self.writeRefAndCurrentAllocations(regions, filename, allPrograms)
            for objective in self.objectives:
                self.interpolateBOCs(regions, objective, options)
                optimisedRegionalSpending = self.distributeFunds(regions, objective, scenario, options)
                regions = self.optimiseAllRegions(regions, optimisedRegionalSpending, objective, formattedScenario, options)
                self.collateAllResults(regions, objective, formattedScenario, allPrograms, filename)

    def writeRefAndCurrentAllocations(self, regions, filename, allPrograms):
        with open(filename, 'a') as f:
            w = writer(f)
            w.writerow(['Reference'] + allPrograms)
            for region in regions:
                name = region.name
                refAllocations = region.referenceAllocations
                w.writerow([name] + refAllocations)
            w.writerow([])
            w.writerow(['Current'] + allPrograms)
            for region in regions:
                name = region.name
                currentAdditional = [a-b for a,b in zip(region.currentAllocations, region.referenceAllocations)]
                w.writerow([name] + currentAdditional)
            w.writerow([])


    def distributeFunds(self, regions, objective, scenario, options):
        # regionalBOCs = self.readBOCs(objective, optimiseCurrent)
        # fixCurrent, optimiseCurrent, removeCurrent, additionalFunds = options
        optimisedRegionalSpending = self.gridSearchTwo(regions, objective, options)
        return optimisedRegionalSpending

    def gridSearch(self, regions, objective, options): # TODO: I THINK ITS THE OUTCOME WHCIH IS INCORRECT>>> WE'RE TRYING TO MAXIMISE IN THIS ALGORITHM...
        costEffVecs, spendingVec, outcomeVec = self.getBOCcostEffectiveness(regions, objective, options)
        totalFunds = self.getTotalFreeFunds(regions) # TODO: check this
        remainingFunds = dcp(totalFunds)
        regionalAllocations = zeros(len(regions))
        percentBudgetSpent = 0.
        maxIters = int(1e6)

        for i in range(maxIters):
            bestEff = -inf
            bestRegion = None
            for regionIdx in range(len(regions)):
                # find most effective spending in each region
                costEffThisRegion = costEffVecs[regionIdx]
                if len(costEffThisRegion):
                    maxIdx = argmax(costEffThisRegion)
                    maxEff = costEffThisRegion[maxIdx]
                    if maxEff > bestEff:
                        bestEff = maxEff
                        bestEffIdx = maxIdx
                        bestRegion = regionIdx

            # once the most cost-effective spending is found, adjust all spending and outcome vectors, update available funds and regional allocation
            if bestRegion is not None:
                fundsSpent = spendingVec[bestRegion][bestEffIdx]
                #TODO: seems to be if it hit a negative...
                remainingFunds -= fundsSpent
                spendingVec[bestRegion] -= fundsSpent
                outcomeVec[bestRegion] -= outcomeVec[bestRegion][bestEffIdx] # TODO: issue could be that gradient is constant but one is being chosen, so the subtracted outcome can make it negative
                regionalAllocations[bestRegion] += fundsSpent
                # remove funds and outcomes at or below zero
                spendingVec[bestRegion] = spendingVec[bestRegion][bestEffIdx+1: ]
                outcomeVec[bestRegion] = outcomeVec[bestRegion][bestEffIdx+1: ]
                # ensure regional spending doesn't exceed remaining funds
                for regionIdx in range(self.numRegions):
                    withinBudget = nonzero(spendingVec[regionIdx] <= remainingFunds)[0]
                    spendingVec[regionIdx] = spendingVec[regionIdx][withinBudget]
                    outcomeVec[regionIdx] = outcomeVec[regionIdx][withinBudget]
                    costEffVecs[regionIdx] = outcomeVec[regionIdx] / spendingVec[regionIdx] # TODO could be issue here...
                    costEffVecs[regionIdx][costEffVecs[regionIdx] < 0] = 0
                newPercentBudgetSpent = (totalFunds - remainingFunds) / totalFunds * 100.
                if not(i%100) or (newPercentBudgetSpent - percentBudgetSpent) > 1.:
                    percentBudgetSpent = newPercentBudgetSpent
            else:
                print percentBudgetSpent
                print regionalAllocations
                print " "
                break # nothing more to allocate

        # scale to ensure correct budget
        scaledRegionalAllocations = rescaleAllocation(totalFunds, regionalAllocations)
        return scaledRegionalAllocations

    def gridSearchTwo(self, regions, objective, options):
        costEffVecs, spendingVec = self.getBOCcostEffectivenessTwo(regions, objective, options)
        totalFunds = self.getTotalFreeFunds(regions) # TODO: check this
        remainingFunds = dcp(totalFunds)
        regionalAllocations = zeros(len(regions))
        percentBudgetSpent = 0.
        maxIters = int(1e6)

        for i in range(maxIters):
            bestEff = -inf
            bestRegion = None
            for regionIdx in range(len(regions)):
                # find most effective spending in each region
                costEffThisRegion = costEffVecs[regionIdx]
                if len(costEffThisRegion):
                    maxIdx = argmax(costEffThisRegion)
                    maxEff = costEffThisRegion[maxIdx]
                    if maxEff > bestEff:
                        bestEff = maxEff
                        bestEffIdx = maxIdx
                        bestRegion = regionIdx
            # once the most cost-effective spending is found, adjust all spending and outcome vectors, update available funds and regional allocation
            if bestRegion is not None:
                fundsSpent = spendingVec[bestRegion][bestEffIdx]
                remainingFunds -= fundsSpent
                spendingVec[bestRegion] -= fundsSpent
                regionalAllocations[bestRegion] += fundsSpent
                # remove funds and derivatives at or below zero
                spendingVec[bestRegion] = spendingVec[bestRegion][bestEffIdx+1: ]
                costEffVecs[bestRegion] = costEffVecs[bestRegion][bestEffIdx+1: ]
                # ensure regional spending doesn't exceed remaining funds
                for regionIdx in range(self.numRegions):
                    withinBudget = nonzero(spendingVec[regionIdx] <= remainingFunds)[0]
                    spendingVec[regionIdx] = spendingVec[regionIdx][withinBudget]
                    costEffVecs[regionIdx] = costEffVecs[regionIdx][withinBudget]
                newPercentBudgetSpent = (totalFunds - remainingFunds) / totalFunds * 100.
                if not(i%100) or (newPercentBudgetSpent - percentBudgetSpent) > 1.:
                    percentBudgetSpent = newPercentBudgetSpent
            else:
                break # nothing more to allocate

        # scale to ensure correct budget
        scaledRegionalAllocations = rescaleAllocation(totalFunds, regionalAllocations)
        return scaledRegionalAllocations

    def getBOCcostEffectiveness(self, regions, objective, options):
        fixCurrent, optimiseCurrent, removeCurrent, additionalFunds = options
        nationalFunds = self.getNationalCurrentSpending()
        numPoints = 10000
        costEffVecs = []
        spendingVec = []
        outcomeVec = []
        for region in regions:
            if fixCurrent:
                minSpending = sum(region.currentAllocations) - sum(region.referenceAllocations)
                maxSpending = minSpending + additionalFunds
            else:
                minSpending = 0
                maxSpending = nationalFunds + additionalFunds
            regionalSpending = linspace(minSpending, maxSpending, numPoints)[1:] # exclude 0 to avoid division error
            adjustedSpending = regionalSpending - minSpending # centers spending if current is fixed
            spendingVec.append(adjustedSpending)
            regionalBOC = region.BOCs[objective][optimiseCurrent]
            regionalOutcome = regionalBOC(adjustedSpending)
            outcomeVec.append(regionalOutcome)
            regionalCostEff = regionalOutcome / adjustedSpending
            costEffVecs.append(regionalCostEff)
        return costEffVecs, spendingVec, outcomeVec

    def getBOCcostEffectivenessTwo(self, regions, objective, options):
        fixCurrent, optimiseCurrent, removeCurrent, additionalFunds = options
        nationalFunds = self.getNationalCurrentSpending()
        numPoints = 10000
        costEffVecs = []
        spendingVec = []
        for region in regions:
            if fixCurrent:
                minSpending = sum(region.currentAllocations) - sum(region.referenceAllocations)
                maxSpending = minSpending + additionalFunds
            else:
                minSpending = 0
                maxSpending = nationalFunds + additionalFunds
            thisDeriv = region.BOCs[objective][optimiseCurrent].derivative(nu=1)
            regionalSpending = linspace(minSpending, maxSpending, numPoints)[1:] # exclude 0 to avoid division error
            adjustedSpending = regionalSpending - minSpending # centers spending if current is fixed
            spendingVec.append(adjustedSpending)
            costEffectiveness = -thisDeriv(adjustedSpending) # TODO: if we have a DECREASING FUNC (Like deaths etc) need to be negative
            costEffVecs.append(costEffectiveness)
        return costEffVecs, spendingVec



    def readBOCs(self, objective, optimiseCurrent):
        regionalBOCs = []
        for name in self.regionNames:
            filename = '{}/{}_optimCurr_{}.csv'.format(self.BOCdir[objective], name, optimiseCurrent)
            with open(filename, 'r') as f:
                regionalSpending = []
                regionalOutcome = []
                r = reader(f)
                for row in r:
                    regionalSpending.append(row[0])
                    regionalOutcome.append(row[1])
            # remove column headers
            regionalSpending = array(regionalSpending[1:])
            regionalOutcome = array(regionalOutcome[1:])
            regionalBOCs.append(pchip(regionalSpending, regionalOutcome))
        return regionalBOCs

    def createCSV(self, scenario):
        direc = '{}/{}/dependent'.format(self.resultsDir, scenario)
        if not os.path.exists(direc):
            os.makedirs(direc)
        filename = '{}/regional_allocations.csv'.format(direc)
        with open(filename, 'w') as f:
            pass
        return filename

    def optimiseAllRegions(self, regions, optimisedSpending, objective, scenario, options):
        fixCurrent, optimiseCurrent, removeCurrent, additionalFunds = options
        budgetMultiple = [1]
        newRegions = []
        jobs = []
        for i, region in enumerate(regions):
            name = region.name
            regionalFunds = optimisedSpending[i]
            resultsDir = '{}/{}/dependent'.format(self.resultsDir, scenario)
            fileInfo = [self.root, self.country + '/regions', name, '']
            newOptim = Optimisation([objective], budgetMultiple, fileInfo, resultsPath=resultsDir,
                                    fixCurrentAllocations=fixCurrent, additionalFunds=regionalFunds,
                                    numYears=self.numYears)
            newRegions.append(newOptim)
            p = Process(target=newOptim.optimise)
            jobs.append(p)
        runJobs(jobs, min(cpu_count(), 50))
        return newRegions

    def collateAllResults(self, regions, objective, scenario, allPrograms, filename):
        """collates all regional output from pickle files
        Uses append file method to avoid over-writing"""

        # write the programs to row for each objective
        with open(filename, 'a') as f:
            w = writer(f)
            w.writerow([objective] + allPrograms)
            for region in regions:
                name = region.name
                filePath = '{}/{}/dependent/{}_{}_{}.pkl'.format(self.resultsDir, scenario, name, objective, 1)
                infile = open(filePath, 'rb')
                thisAllocation = pickle.load(infile)
                infile.close()
                allocations = OrderedDict(sorted(thisAllocation.items()))
                # remove fixed funds
                fixedAllocations = region.fixedAllocations
                fixedAllocationsDict = region.createDictionary(fixedAllocations)
                fixedAllocations = OrderedDict(sorted(fixedAllocationsDict.items())).values()
                optimisedAdditional = [a-b for a,b in zip(allocations.values(), fixedAllocations)]
                w.writerow([name] + optimisedAdditional)
            w.writerow([])

    def getTotalFreeFunds(self, regions):
        """ Need to wait the additional funds by number of regions so we don't have too much money"""
        return sum(region.additionalFunds/len(regions) + sum(region.currentAllocations) - sum(region.fixedAllocations) for region in regions)

class BudgetScenarios:
    """
    Descriptions of budget scenarios found in the corresponding .xlsx file
    Need to specify:
    - is current regional spending fixed
    - is current allocation to be programatically optimised
    - amount of additional funds, if any.

    """

    def __init__(self, filePath):
        self.filePath = filePath
        # [fixedRegionalSpending, optimiseCurrent, removeCurrentFunds]
        # then will get additionalFunds
        # TODO: scenario 1 is a difficult case, b/c it's not really even geospatial. This we should treat it differently.
        # TODO: decide if want 2 and 4, since 2 just has additionalFunds=0
        self.allScenarios = {'Scenario 1': [True, True, False], 'Scenario 2': [False, True, True],
                          'Scenario 3': [True, False, False], 'Scenario 4': [False, True, True]}

    def getScenarios(self):
        """
        This information should be contained in a separate .xlsx file,
        which details the current expenditure by region, and all the optimisation scenarios.
        :return:
        """
        import pandas as pd
        thisSheet = pd.read_excel(self.filePath, 'Optimal funding scenario', index_col=[0])
        thisSheet = thisSheet.drop(['Current spending description', 'Additional spending description'], 1)
        scenarios = {}
        for scenario, row in thisSheet.iterrows():
            if pd.notnull(row[1]):
                scenarios[scenario] = self.allScenarios[scenario] + [row[0]] # adding funds
        return scenarios

