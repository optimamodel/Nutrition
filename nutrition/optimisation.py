import os
import play
import pso
import asd
import time
import cPickle as pickle
import pandas as pd
from copy import deepcopy as dcp
from multiprocessing import cpu_count, Process # TODO: would like to replace with Pool
from numpy import array, append, linspace, nanargmax, zeros, nonzero, inf
from scipy.interpolate import pchip
from csv import writer, reader
from itertools import izip
from collections import OrderedDict
from datetime import date

def rescaleAllocation(totalBudget, allocation):
    new = sum(allocation)
    if new == 0:
        rescaledAllocation = dcp(allocation)
    else:
        scaleRatio = totalBudget / new
        rescaledAllocation = [x * scaleRatio for x in allocation]
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
    thisModel.simulateOptimisation(newCoverages)
    outcome = thisModel.getOutcome(objective) * 1000.
    if objective == 'thrive' or objective == 'healthy_children' or objective == 'no_conditions':
        outcome *= -1
    return outcome


class Optimisation:
    def __init__(self, objectives, budgetMultiples, fileInfo, resultsPath=None, fixCurrentAllocations=False,
                 additionalFunds=0, removeCurrentFunds=False, numYears=None, costCurveType='linear',
                 parallel=True, numCPUs=None, numRuns=1, filterProgs=True, createResultsDir=True, maxIter=100,
                 swarmSize=50):
        root, analysisType, name, scenario = fileInfo
        self.name = name
        filePath = play.getFilePath(root=root, analysisType=analysisType, name=name)
        if resultsPath:
            self.resultsDir = resultsPath
        else:
            self.resultsDir = play.getResultsDir(root='', analysisType=analysisType, scenario=scenario)
        self.model = play.setUpModel(filePath, adjustCoverage=False, optimise=True,
                                     numYears=numYears)  # model has already moved 1 year
        self.budgetMultiples = budgetMultiples
        self.objectives = objectives
        self.fixCurrentAllocations = fixCurrentAllocations
        self.removeCurrentFunds = removeCurrentFunds
        self.additionalFunds = additionalFunds
        self.filterProgs = filterProgs
        self.maxIter = maxIter
        self.swarmSize = swarmSize
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
        if createResultsDir:
            self.createDirectory(self.resultsDir)

    ######### FILE HANDLING #########

    def createDirectory(self, resultsDir):
        # create directory if necessary
        if not os.path.exists(resultsDir):
            os.makedirs(resultsDir)

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
        self.currentAllocations = self.getCurrentAllocations()
        # self.currentAllocations, self.scaleFactor = self.scaleCostsForCurrentExpenditure()
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
        specialRegions = ['Kusini', 'Kaskazini', 'Mjini']  # we don't have current expenditure for these regions
        # remove cash transfers from scaling
        progName = 'Cash transfers'  # TODO: remove after Tanzania
        correctedFunds = currentAllocationsBefore[:]
        for i, prog in enumerate(self.programs):
            if prog.name == progName:
                correctedFunds[i] = 0
        if self.model.programInfo.currentExpenditure:
            currentCalculated = sum(correctedFunds) - sum(self.referenceAllocations)
            scaleFactor = self.model.programInfo.currentExpenditure / currentCalculated
            for program in self.programs:
                if (not program.reference) and (program.name != progName):
                    program.scaleUnitCosts(scaleFactor)
        elif any(sub in self.name for sub in specialRegions):  # TODO: this should be removed after Tanzania application
            scaleFactor = 0.334  # this is the median of all other regions
            for program in self.programs:
                if (not program.reference) and (program.name != progName):
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
        elif self.removeCurrentFunds and (not fixCurrent):  # this is additional to reference spending
            freeFunds = self.additionalFunds
        elif not self.removeCurrentFunds:
            freeFunds = sum(self.currentAllocations) - sum(self.fixedAllocations) + self.additionalFunds
        return freeFunds

    ######### OPTIMISATION ##########

    def optimise(self):
        print 'Optimising for {}'.format(self.name)
        newBudgets = self.checkForZeroBudget()
        if self.parallel:
            self.parallelRun(newBudgets)
        else:
            self.seriesRun(newBudgets)
        return

    def parallelRun(self, newBudgets):
        jobs = self.getJobs(newBudgets)
        runJobs(jobs, self.numCPUs)
        return

    def seriesRun(self, newBudgets):
        for objective in self.objectives:
            for multiple in newBudgets:
                self.runOptimisation(multiple, objective)

    def checkForZeroBudget(self):
        """For 0 free funds, spending is equal to the fixed costs"""
        if 0 in self.budgetMultiples:
            newBudgets = filter(lambda x: x > 0, self.budgetMultiples)
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

    def runOptimisation(self, multiple, objective):
        kwargs = dcp(self.kwargs)
        kwargs['freeFunds'] *= multiple
        if kwargs['freeFunds'] != 0:
            kwargs['objective'] = objective
            indxToKeep = self._selectProgsForObjective(objective)
            kwargs['indxToKeep'] = indxToKeep
            xmin = [0.] * len(indxToKeep)
            xmax = [kwargs['freeFunds']] * len(indxToKeep)  # TODO: could make this cost of saturation.
            runOutputs = []
            for run in range(self.numRuns):
                now = time.time()
                x0, fopt = pso.pso(objectiveFunction, xmin, xmax, kwargs=kwargs, maxiter=self.maxIter, swarmsize=self.swarmSize)
                x, fval, flag = asd.asd(objectiveFunction, x0, args=kwargs, xmin=xmin, xmax=xmax, verbose=0)
                runOutputs.append((x, fval[-1]))
                self.printMessages(objective, multiple, flag, now)
            bestAllocation = self.findBestAllocation(runOutputs)
            scaledAllocation = rescaleAllocation(kwargs['freeFunds'], bestAllocation)
            totalAllocation = _addFixedAllocations(self.fixedAllocations, scaledAllocation, kwargs['indxToKeep'])
            bestAllocationDict = self.createDictionary(totalAllocation)
        else:
            # if no money to distribute, return the fixed costs
            bestAllocationDict = self.createDictionary(self.fixedAllocations)
        self.writeToPickle(bestAllocationDict, multiple, objective)
        return

    def printMessages(self, objective, multiple, flag, now):
        print 'Finished optimisation for {} for objective {} and multiple {}'.format(self.name, objective, multiple)
        print 'The reason is {} and it took {} hours \n'.format(flag['exitreason'], (time.time() - now) / 3600.)

    def findBestAllocation(self, outputs):
        bestSample = min(outputs, key=lambda item: item[-1])
        return bestSample[0]

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
            zeroModel.simulateScalar(zeroCov, restrictedCov=True)
            zeroOutcome = zeroModel.getOutcome(objective)
            for indx, program in enumerate(self.programs):
                thisModel = dcp(self.model)
                thisCov = dcp(zeroCov)
                thisCov[program.name] = newCov
                if program.malariaTwin:
                    thisCov[program.name + ' (malaria area)'] = newCov
                thisModel.simulateScalar(thisCov, restrictedCov=True)
                outcome = thisModel.getOutcome(objective)
                if abs((outcome - zeroOutcome) / zeroOutcome) * 100. > threshold:  # no impact
                    indxToKeep.append(indx)
                    for twinIndx, twin in enumerate(self.programs):  # TODO: shouldn't have to search through twice
                        if twin.name == program.name + ' (malaria area)':
                            indxToKeep.append(twinIndx)
        else:  # keep all
            indxToKeep = [i for i in range(len(self.programs))]
        return indxToKeep

    def interpolateBOC(self, objective, spending, outcome):
        # need BOC for each objective in region
        # spending, outcome = self.getBOCvectors(objective)
        self.BOCs[objective] = pchip(spending, outcome, extrapolate=False)

    def getBOCvectors(self, objective, budgetMultiples):
        spending = array([])
        outcome = array([])
        for multiple in budgetMultiples:
            spending = append(spending, multiple * self.freeFunds)
            filePath = '{}/{}_{}_{}.pkl'.format(self.resultsDir, self.name, objective, multiple)
            f = open(filePath, 'rb')
            thisAllocation = pickle.load(f)
            f.close()
            output = self.oneModelRunWithOutput(thisAllocation).getOutcome(objective)
            outcome = append(outcome, output)
        return spending, outcome

    ########### FILE HANDLING ############

    def writeToPickle(self, allocation, multiple, objective):
        fileName = '{}/{}_{}_{}.pkl'.format(self.resultsDir, self.name, objective, multiple)
        outfile = open(fileName, 'wb')
        pickle.dump(allocation, outfile)
        return

    def readPickles(self):
        allocations = {}
        for objective in self.objectives:
            allocations[objective] = {}
            for multiple in self.budgetMultiples:
                filename = '{}/{}_{}_{}.pkl'.format(self.resultsDir, self.name, objective, multiple)
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
        model.simulateOptimisation(newCoverages)
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
        currentAdditionalList = [a - b for a, b in zip(self.currentAllocations, self.referenceAllocations)]
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
                    optimisedAdditional[objective][multiple][programName] = additionalFunds[programName] - \
                                                                            fixedCostsDict[programName]
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
                    coverages[objective][multiple][program.name] = "{0:.2f}".format(
                        (program.costCurveFunc(allocations[program.name]) / program.restrictedPopSize) * 100.)
        return coverages

    def writeCoveragesToCSV(self, coverages):
        filename = '{}/{}_coverages.csv'.format(self.resultsDir, self.name)
        with open(filename, 'wb') as f:
            w = writer(f)
            for objective in self.objectives:
                w.writerow([''])
                w.writerow([objective] + sorted(coverages[objective][self.budgetMultiples[0]].keys()))
                for multiple in self.budgetMultiples:
                    coverage = OrderedDict(sorted(coverages[objective][multiple].items()))
                    w.writerow([multiple] + coverage.values())

    def writeOutcomesToCSV(self, reference, current, optimised):
        allOutcomes = {}
        for objective in self.objectives:
            allOutcomes[objective] = {}
            allOutcomes[objective].update(reference[objective])
            allOutcomes[objective].update(current[objective])
            allOutcomes[objective].update(optimised[objective])
        filename = '{}/{}_outcomes.csv'.format(self.resultsDir, self.name)
        budgets = ['reference spending', 'current spending'] + self.budgetMultiples
        with open(filename, 'wb') as f:
            w = writer(f)
            for objective in self.objectives:
                w.writerow([objective])
                for multiple in budgets:
                    outcome = allOutcomes[objective][multiple]
                    w.writerow(['', multiple, outcome])

    def writeAllocationsToCSV(self, reference, current, optimised):
        allSpending = {}
        for objective in self.objectives:  # do i use this loop?
            allSpending[objective] = {}
            allSpending[objective].update(current)
            allSpending[objective].update(reference)
            allSpending[objective].update(optimised[objective])
        filename = '{}/{}_allocations.csv'.format(self.resultsDir, self.name)
        with open(filename, 'wb') as f:
            w = writer(f)
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
    def __init__(self, objectives, root, regionNames, numYears=None, costCurveType='linear'):
        self.root = root
        self.analysisType = 'regional'
        thisDate = date.today().strftime('%Y%b%d')
        self.resultsDir = os.path.join('results', thisDate)
        self.objectives = objectives
        self.budgetMultiples = [0, 0.01, 0.025, 0.04, 0.05, 0.075, 0.1, 0.2, 0.3, 0.6, 1]  # these multiples are in the interval (minFreeFunds, maxFreeFunds)
        self.regionNames = regionNames
        self.numYears = numYears
        self.numRegions = len(regionNames)
        budgetFilePath = os.path.join(self.root, 'data', 'optimisationBudgets.xlsx')
        self.scenarios = BudgetScenarios(budgetFilePath).getScenarios()  # TODO: super ugly file-finding
        self.BOCs = {}

    def getNationalCurrentSpending(self):
        nationalFunds = 0
        for name in self.regionNames:
            fileInfo = [self.root, self.analysisType, name, '']
            thisRegion = Optimisation([], [], fileInfo, fixCurrentAllocations=False, createResultsDir=False)
            nationalFunds += thisRegion.freeFunds
        return nationalFunds

    def readBOC(self, region, objective):
        filename = os.path.join(self.newResultsDir, 'BOCs', objective, 'pickles', region + '.csv')
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

    def writeBOCs(self, regions, objective):
        filename = os.path.join(self.newResultsDir, 'BOCs', objective, 'BOCs.csv')
        headers = ['spending'] + [region.name for region in regions]
        minSpend = min(regions[0].BOCs[objective].x)
        maxSpend = max(regions[0].BOCs[objective].x)
        newSpending = linspace(minSpend, maxSpend, 2000)
        regionalOutcomes = []
        with open(filename, 'wb') as f:
            w = writer(f)
            w.writerow(headers)
            for region in regions:
                thisBOC = region.BOCs[objective]
                interpolated = thisBOC(newSpending)
                regionalOutcomes.append(interpolated)
            columnLists = [newSpending] + regionalOutcomes
            w.writerows(zip(*columnLists))

    def getBOCjobs(self, regions, objective):
        jobs = []
        for region in regions:
            resultsPath = region.resultsDir
            prc = Process(target=self.optimiseAndWrite, args=(region, objective, resultsPath))
            jobs.append(prc)
        return jobs

    def optimiseAndWrite(self, region, objective, resultsPath):
        region.optimise()
        self.writeBudgetOutcome(region, objective, resultsPath)

    def writeBudgetOutcome(self, region, objective, resultsPath):
        spending, outcome = region.getBOCvectors(objective, self.budgetMultiples)
        filename = os.path.join(resultsPath, region.name + '.csv')
        with open(filename, 'wb') as f:
            w = writer(f)
            w.writerow(['spending', 'outcome'])
            w.writerows(izip(spending, outcome))

    def setUpRegions(self, objective, fixCurrent, additionalFunds):
        regions = []
        for name in self.regionNames:
            fileInfo = [self.root, self.analysisType, name, '']
            resultsPath = os.path.join(self.newResultsDir, 'BOCs', objective, 'pickles')
            thisRegion = Optimisation(self.objectives, self.budgetMultiples, fileInfo, resultsPath=resultsPath,
                                      fixCurrentAllocations=fixCurrent, removeCurrentFunds=False,
                                      additionalFunds=additionalFunds, numYears=self.numYears, filterProgs=False)
            regions.append(thisRegion)
        return regions

    def optimiseScenarios(self):
        for scenario, options in self.scenarios.iteritems():
            fixBetween, fixWithin, replaceCurrent, additionalFunds = options
            formScenario = scenario.lower().replace(' ', '')
            self.newResultsDir = os.path.join(self.resultsDir, self.analysisType, formScenario,
                                              str(int(additionalFunds / 1e6)) + 'm')
            for objective in self.objectives:
                # first distribute funds between regions
                self.getRegionalBOCs(objective, fixWithin,
                                     additionalFunds)  # specifies if current funding is fixed within a region
                optimalDistribution = self.distributeFunds(objective, options)
                # optimise within each region
                regions = self.optimiseAllRegions(optimalDistribution, objective, options)
                self.collateAllResults(regions, objective)
                # self.getOptimalOutcomes(regions, objective)

    def getRegionalBOCs(self, objective, fixWithin, additionalFunds):
        print '...Generating BOCs... \n'
        regions = self.setUpRegions(objective, fixWithin, additionalFunds)
        jobs = self.getBOCjobs(regions, objective)
        maxRegions = int(50 / (len(self.budgetMultiples) - 1))
        runJobs(jobs, maxRegions)

    def interpolateBOCs(self, objective, fixBetween, additionalFunds):
        regions = self.setUpRegions(objective, fixBetween, additionalFunds)
        for region in regions:
            spending, outcome = self.readBOC(region.name, objective)
            region.interpolateBOC(objective, spending, outcome)
        self.writeBOCs(regions, objective)
        return regions

    def distributeFunds(self, objective, options):
        fixBetween = options[0]
        additionalFunds = options[-1]
        regions = self.interpolateBOCs(objective, fixBetween, additionalFunds)
        optimalDistribution = self.gridSearch(regions, objective, options)
        return optimalDistribution

    def writeRefAndCurrentAllocations(self, regions, filename):
        sortedProgs = sorted([prog.name for prog in regions[0].programs])
        with open(filename, 'wb') as f:
            w = writer(f)
            w.writerow(['Reference'] + sortedProgs)
            for region in regions:
                name = region.name
                refDict = region.createDictionary(region.referenceAllocations)
                sortedRef = OrderedDict(sorted(refDict.items())).values()
                w.writerow([name] + sortedRef)
            w.writerow([])
            w.writerow(['Current'] + sortedProgs)
            for region in regions:
                name = region.name
                currentAdditional = [a - b for a, b in zip(region.currentAllocations, region.referenceAllocations)]
                currentAdditionalDict = region.createDictionary(currentAdditional)
                sortedCurrent = OrderedDict(sorted(currentAdditionalDict.items())).values()
                w.writerow([name] + sortedCurrent)
            w.writerow([])

    def gridSearch(self, regions, objective, options):
        costEffVecs, spendingVec = self.getBOCcostEffectiveness(regions, objective, options)
        totalFunds = self.getTotalFreeFunds(regions)
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
                    maxIdx = nanargmax(costEffThisRegion)
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
                spendingVec[bestRegion] = spendingVec[bestRegion][bestEffIdx + 1:]
                costEffVecs[bestRegion] = costEffVecs[bestRegion][bestEffIdx + 1:]
                # ensure regional spending doesn't exceed remaining funds
                for regionIdx in range(self.numRegions):
                    withinBudget = nonzero(spendingVec[regionIdx] <= remainingFunds)[0]
                    spendingVec[regionIdx] = spendingVec[regionIdx][withinBudget]
                    costEffVecs[regionIdx] = costEffVecs[regionIdx][withinBudget]
                newPercentBudgetSpent = (totalFunds - remainingFunds) / totalFunds * 100.
                if not (i % 100) or (newPercentBudgetSpent - percentBudgetSpent) > 1.:
                    percentBudgetSpent = newPercentBudgetSpent
            else:
                break  # nothing more to allocate

        # scale to ensure correct budget
        scaledRegionalAllocations = rescaleAllocation(totalFunds, regionalAllocations)
        return scaledRegionalAllocations

    def getBOCcostEffectiveness(self, regions, objective, options):
        fixBetween, fixWithin, removeCurrent, additionalFunds = options
        nationalFunds = self.getNationalCurrentSpending()
        numPoints = 10000
        costEffVecs = []
        spendingVec = []
        for region in regions:
            if fixBetween and not fixWithin:
                minSpending = sum(region.currentAllocations) - sum(region.referenceAllocations)
                maxSpending = minSpending + additionalFunds
            elif fixBetween and fixWithin:  # this is scenario 3, where the spending=0 corresponds to non-optimised current allocations
                minSpending = 0
                maxSpending = additionalFunds
            else:
                minSpending = 0
                maxSpending = nationalFunds + additionalFunds
            thisDeriv = region.BOCs[objective].derivative(nu=1)
            regionalSpending = linspace(minSpending, maxSpending, numPoints)[1:]  # exclude 0 to avoid division error
            adjustedSpending = regionalSpending - minSpending  # centers spending if current is fixed
            spendingVec.append(adjustedSpending)
            # use non-adjusted spending b/c we don't necessarily want to start at 0
            costEffectiveness = thisDeriv(regionalSpending)  # needs to be neg if have decreasing func
            costEffVecs.append(costEffectiveness)
        return costEffVecs, spendingVec

    def optimiseAllRegions(self, optimisedSpending, objective, options):
        print '...Optimising within regions... \n'
        _fixBetween, fixWithin, replaceCurrent, additionalFunds = options
        budgetMultiple = [1]
        newRegions = []
        jobs = []
        for i, name in enumerate(self.regionNames):
            regionalFunds = optimisedSpending[i]
            resultsDir = os.path.join(self.newResultsDir, 'pickles')
            fileInfo = [self.root, self.analysisType, name, '']
            newOptim = Optimisation([objective], budgetMultiple, fileInfo, resultsPath=resultsDir,
                                    fixCurrentAllocations=fixWithin, removeCurrentFunds=replaceCurrent,
                                    additionalFunds=regionalFunds, numYears=self.numYears, filterProgs=False)
            newRegions.append(newOptim)
            p = Process(target=newOptim.optimise)
            jobs.append(p)
        runJobs(jobs, min(cpu_count(), 50))
        return newRegions

    def collateAllResults(self, regions, objective):
        """collates all regional output from pickle files
        Uses append file method to avoid over-writing"""
        filename = os.path.join(self.newResultsDir, 'regional_allocations_' + objective + '.csv')
        # write the programs to row for each objective
        self.writeRefAndCurrentAllocations(regions, filename)
        sortedProgs = sorted([prog.name for prog in regions[0].programs])
        with open(filename, 'a') as f:
            w = writer(f)
            w.writerow([''] + sortedProgs)
            for region in regions:
                name = region.name
                filePath = os.path.join(self.newResultsDir, 'pickles', '{}_{}_{}.pkl'.format(name, objective, 1))
                infile = open(filePath, 'rb')
                thisAllocation = pickle.load(infile)
                infile.close()
                allocations = OrderedDict(sorted(thisAllocation.items()))
                # remove fixed funds
                fixedAllocations = region.fixedAllocations
                fixedAllocationsDict = region.createDictionary(fixedAllocations)
                fixedAllocations = OrderedDict(sorted(fixedAllocationsDict.items())).values()
                optimisedAdditional = [a - b for a, b in zip(allocations.values(), fixedAllocations)]
                w.writerow([name] + optimisedAdditional)
            w.writerow([])

    def getOptimalOutcomes(self, regions, objective):
        outcomes = ['total_stunted', 'wasting_prev', 'anaemia_prev_children', 'deaths_children', 'neonatal_deaths']
        fileToWrite = os.path.join(self.newResultsDir, 'optimal_outcomes_{}.csv'.format(objective))
        with open(fileToWrite, 'wb') as f:
            w = writer(f)
            w.writerow(['Region'] + outcomes)
            for region in regions:
                filename = os.path.join(self.newResultsDir, 'pickles', '{}_{}_{}.pkl'.format(region.name, objective, 1))
                infile = open(filename, 'rb')
                thisAllocation = pickle.load(infile)
                infile.close()
                allOutputs = []
                thisModel = region.oneModelRunWithOutput(thisAllocation)
                for outcome in outcomes:
                    allOutputs.append(thisModel.getOutcome(outcome))
                w.writerow([region.name] + allOutputs)

    def getTotalFreeFunds(self, regions):
        """ Need to wait the additional funds by number of regions so we don't have too much money"""
        return sum(
            region.additionalFunds / len(regions) + sum(region.currentAllocations) - sum(region.fixedAllocations) for
            region in regions)


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
        # [fixedBetweenRegions, fixedWithinRegion, replaceCurrent]
        # additionalFunds will be appended
        self.allScenarios = {'Scenario 1': [True, False, False],
                             'Scenario 2': [False, False, True],
                             'Scenario 3': [True, True, False]}

    def getScenarios(self):
        """
        This information should be contained in a separate .xlsx file,
        which details the current expenditure by region, and all the optimisation scenarios.
        :return:
        """
        thisSheet = pd.read_excel(self.filePath, 'Optimal funding scenario', index_col=[0])
        thisSheet = thisSheet.drop(['Current spending description', 'Additional spending description'], 1)
        scenarios = {}
        for scenario, row in thisSheet.iterrows():
            if pd.notnull(row[1]):
                scenarios[scenario] = self.allScenarios[scenario] + [row[0]]  # adding funds
        return scenarios
