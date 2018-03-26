import os
from copy import deepcopy as dcp
import play
import cPickle as pickle
from multiprocessing import cpu_count, Process
from numpy import array, random, append, linspace, argmax, zeros, nonzero, inf
from scipy.interpolate import pchip
from math import ceil
from csv import writer
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
    try:
        scaleRatio = totalBudget / sum(allocation)
        rescaledAllocation = [x * scaleRatio for x in allocation]
    except ZeroDivisionError:
        rescaledAllocation = dcp(allocation)
    return rescaledAllocation

def runJobs(jobs, max_jobs):
    while jobs:
        thisRound = min(max_jobs, len(jobs)) # TODO: problem is this only accounts for the number of regions, not the multiples or objectives inside
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

def objectiveFunction(allocation, objective, model, freeFunds, fixedAllocations, indxToKeep, numYears):
    thisModel = dcp(model)
    totalAllocations = dcp(fixedAllocations)
    # scale the allocation appropriately
    scaledAllocation = rescaleAllocation(freeFunds, allocation)
    newCoverages = {}
    programs = thisModel.programInfo.programs
    totalAllocations = _addFixedAllocations(totalAllocations, scaledAllocation, indxToKeep)
    for idx, program in enumerate(programs):
        newCoverages[program.name] = program.costCurveFunc(totalAllocations[idx]) / program.unrestrictedPopSize
    thisModel.runSimulationFromOptimisation(newCoverages, numYears)
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
    def __init__(self, objectives, budgetMultiples, fileInfo, resultsPath=None, fixCurrentAllocations=False, optimiseCurrent=False,
                 additionalFunds=0, numYears=None, costCurveType='linear', parallel=True, numRuns=1, filterProgs=True):
        root, country, name, analysisType = fileInfo
        self.name = name
        filePath = play.getFilePath(root=root, country=country, name=name)
        if not resultsPath:
            resultsPath = play.getResultsDir(root=root, country=self.name, analysisType=analysisType)
        self.createDirectory(resultsPath)
        self.model = play.setUpModel(filePath, adjustCoverage=False, optimise=True) # model has already moved 1 year
        self.budgetMultiples = budgetMultiples
        self.objectives = objectives
        self.fixCurrentAllocations = fixCurrentAllocations
        self.optimiseCurrent = optimiseCurrent # TODO: ensures we have an optimised budget level equal to current. IMPLEMENT
        self.additionalFunds = additionalFunds
        self.filterProgs = filterProgs
        self.programs = self.model.programInfo.programs
        if numYears: # TODO: new param in model specifying how long to run
            self.numYears = numYears
        else:
            self.numYears = len(self.model.constants.simulationYears) # default to period for which data is supplied # TODO: see about this in terms of the new param in Model.
        self.parallel = parallel
        self.numCPUs = cpu_count()
        self.numRuns = numRuns
        # self.costCurveType = costCurveType # TODO: currently doesn't do anything.
        self.timeSeries = None
        for program in self.programs:
            program._setCostCoverageCurve()
        self.calculateAllocations(fixCurrentAllocations)
        self.kwargs = {'model': self.model, 'numYears': self.numYears,
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
        self.currentAllocations = self.scaleCostsForCurrentExpenditure()
        self.fixedAllocations = self.getFixedAllocations(fixCurrentAllocations)
        self.freeFunds = self.getFreeFunds()

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
        return self.getCurrentAllocations()

    def getFreeFunds(self):
        """
        freeFunds = currentExpenditure + additionalFunds - fixedFunds

        fixedFunds includes both reference programs as well as currentExpenditure, if the latter is to be fixed.
        I.e. if all of the currentExpenditure is fixed, freeFunds = additionalFunds.
        :return:
        """
        freeFunds = sum(self.currentAllocations) - sum(self.fixedAllocations) + self.additionalFunds
        return freeFunds

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
        for objective in self.objectives:
            for multiple in self.budgetMultiples:
                self.runOptimisation(multiple, objective)

    def getJobs(self):
        jobs = []
        for objective in self.objectives:
            for multiple in self.budgetMultiples:
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

    def runOptimisation(self, multiple, objective): # TODO: don't want to handle the 0 budget in here, since it isn't even an optimisation. Just run model with 0 spending.
        import pso as pso
        import asd as asd
        from copy import deepcopy as dcp
        import time
        random.seed(1)
        kwargs = dcp(self.kwargs)
        kwargs['freeFunds'] *= multiple
        kwargs['objective'] = objective
        indxToKeep = self._selectProgsForObjective(objective)
        kwargs['indxToKeep'] = indxToKeep
        xmin = [0.] * len(indxToKeep)
        xmax = [kwargs['freeFunds']] * len(indxToKeep) # TODO: could make this cost of saturation.
        runOutputs = []
        print self.additionalFunds
        print self.fixCurrentAllocations
        print self.freeFunds
        print multiple
        print objective
        for run in range(self.numRuns):
            now = time.time()
            x0, fopt = pso.pso(objectiveFunction, xmin, xmax, kwargs=kwargs, maxiter=1, swarmsize=10) # should be about 13 hours for 100*120
            print "Objective: " + str(objective)
            print "Multiple: " + str(multiple)
            print "value: " + str(fopt/1000.)
            budgetBest, fval, exitflag, output = asd.asd(objectiveFunction, x0, kwargs, xmin=xmin,
                                                         xmax=xmax, verbose=2, MaxIter=5)
            print str((time.time() - now)/(60*60)) + ' hours'
            print "----------"
            outputOneRun = OutputClass(budgetBest, fval, exitflag, output.iterations, output.funcCount, output.fval,
                                       output.x)
            runOutputs.append(outputOneRun)
        bestAllocation = self.findBestAllocation(runOutputs)
        scaledAllocation = rescaleAllocation(kwargs['freeFunds'], bestAllocation)
        totalAllocation = _addFixedAllocations(self.fixedAllocations, scaledAllocation, kwargs['indxToKeep'])
        bestAllocationDict = self.createDictionary(totalAllocation)
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

    def interpolateBOCs(self):
        # need BOC for each objective in region
        self.BOCs = {}
        for objective in self.objectives:
            spending, outcome = self.getBOCvectors(objective)
            self.BOCs[objective] = pchip(spending, outcome, extrapolate=False)

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

    def oneModelRunWithOutput(self, allocationDictionary): # TODO: could get it to take objective as well?
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
    def __init__(self, objectives, fileInfo, BOCsFileStem, regionNames, numYears=None, costCurveType='linear'):
        self.root, self.country = fileInfo
        thisDate = date.today().strftime('%Y%b%d')
        self.resultsDir = '{}/Results/{}/geospatial/{}'.format(self.root, self.country, thisDate)
        self.objectives = objectives
        self.budgetMultiples = [1., 'national'] #[0.25, 0.5, 1, 3, 6, 'national']
        self.regionNames = regionNames
        self.numYears = numYears
        self.numRegions = len(regionNames)
        self.scenarios = BudgetScenarios(self.root+'/input_spreadsheets/'+self.country+'/optimisationBudgets.xlsx').getScenarios()  # TODO: super ugly file-finding
        if BOCsFileStem is not None: # None when optimising regions independently
            self.checkForRegionalBOCs()

    # TODO: would like the directory to be tanzania/regional/'region'/'objective'/
    # TODO: would also like to specific which run has fixed spending & what kind

    def optimiseScenarios(self):
        """
        Each scenario is run in series because of the large number of parallel jobs for each regions.
        :return:
        """
        # options: [fixedAllocations,progOpt, additionalFunds]
        for scenario, options in self.scenarios.iteritems():
            formattedScenario = scenario.lower().replace(' ', '')
            regions = self.setUpRegionalOptimisations(formattedScenario, options)
            regions = self.getRegionalBOCs(regions)
            # distribute funds between regions
            for objective in self.objectives:
                self.optimiseAllRegions(regions, objective, formattedScenario, options)
                self.collateAllResults(objective, regions)

    def setUpRegionalOptimisations(self, scenario, options):
        fixCurrent, optimiseCurrent, additionalFunds = options
        regions = []
        for region in self.regionNames:
            resultsDir = '{}/{}/independent'.format(self.resultsDir, scenario) # TODO: not happy with this way of providing directory and file info
            fileInfo = [self.root, self.country + '/regions', region, ''] # TODO: bit of a cheat here
            thisRegion = Optimisation(self.objectives, self.budgetMultiples, fileInfo, resultsPath=resultsDir,
                                      fixCurrentAllocations=fixCurrent,
                                      optimiseCurrent=optimiseCurrent, additionalFunds=additionalFunds)
            regions.append(thisRegion)
        regions = self.getBudgetMultiples(regions)
        return regions

    def getRegionalBOCs(self, regions):
        from math import ceil
        jobs = []
        max_jobs = int(ceil(float(cpu_count()) / (float(len(self.objectives)) * float(len(self.budgetMultiples))))) # TODO: bit of a hack solution.
        for region in regions:
            jobs.append(Process(target=region.optimise))
        runJobs(jobs, max_jobs)
        for region in regions:
            region.interpolateBOCs()
        return regions

    def optimiseAllRegions(self, regions, objective, scenario, options):
        fixCurrent, optimiseCurrent, dummyFunds = options
        optimisedRegionalBudgetList = self.gridSearch(regions, objective)
        budgetMultiple = [1]
        for i, region in enumerate(regions):
            name = region.name
            regionalFunds = optimisedRegionalBudgetList[i]
            resultsDir = '{}/{}/dependent'.format(self.resultsDir, scenario)
            fileInfo = [self.root, self.country + '/regions', name, '']
            newOptim = Optimisation([objective], budgetMultiple, fileInfo, resultsPath=resultsDir,
                                    fixCurrentAllocations=fixCurrent,
                                    optimiseCurrent=optimiseCurrent, additionalFunds=regionalFunds)
            prc = Process(target=newOptim.optimise())
            prc.start()

    def collateAllResults(self, objective, scenario):
        """collates all regional output from pickle files
        Uses append file method to avoid over-writing"""

        # write the programs to row for each objective
        # TODO: could be issue that 3 regions have additional programs to the others.
        direc = '{}/{}/dependent/results'.format(self.resultsDir, scenario)
        filename = '{}/regional_allocations.csv'.format(direc)
        with open(filename, 'a') as f:
            w = writer(f)
            w.writerow(['Regions'] + 'SORTED PROGS') # TODO
        for name in self.regionNames:
            filePath = '{}/{}/dependent/{}_{}_{}.pkl'.format(self.resultsDir, scenario, name, objective, 1)
            infile = open(filePath, 'rb')
            thisAllocation = pickle.load(infile)
            infile.close()
            with open('regional_allocations.csv', 'a') as f:
                w = writer(f)
                allocations = OrderedDict(sorted(thisAllocation[objective]['1'].items()))
                w.writerow([name] + allocations.values())
                w.writerow([])

    def getBudgetMultiples(self, regions): # TODO: would like to choose multiples more specifically for each region
        """maxBudget = additionalSpending or national budget + additional, depending on whether current spending is fixed.
         always need 0 and national budget to be considered to prevent unwanted behaviour if spending in a region gets very small or large, respectively"""
        totalFreeFunds = self.getTotalFreeFunds(regions)
        for region in regions:
            theseMultiples = dcp(self.budgetMultiples)
            maxMultiple = ceil(totalFreeFunds / region.freeFunds) # TODO: check we want freeFunds
            theseMultiples[-1] = maxMultiple # should replace national
            region.budgetMultiples = dcp(theseMultiples)
        return regions

    def getTotalFreeFunds(self, regions):
        return sum(region.freeFunds for region in regions)

    def gridSearch(self, regions, objective):
        costEffVecs, spendingVec, outcomeVec = self.getBOCcostEffectiveness(regions, objective)
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
                    print maxEff
                    print bestEff
                    if maxEff > bestEff:
                        bestEff = maxEff
                        bestEffIdx = maxIdx
                        print regionIdx
                        bestRegion = regionIdx

            # once the most cost-effective spending is found, adjust all spending and outcome vectors, update available funds and regional allocation
            if bestRegion is not None:
                fundsSpent = spendingVec[bestRegion][bestEffIdx]
                remainingFunds -= fundsSpent
                spendingVec[bestRegion] -= fundsSpent
                outcomeVec[bestRegion] -= outcomeVec[bestRegion][bestEffIdx]
                regionalAllocations[bestRegion] += fundsSpent
                # remove funds and outcomes at or below zero
                spendingVec[bestRegion] = spendingVec[bestRegion][bestEffIdx+1: ]
                outcomeVec[bestRegion] = outcomeVec[bestRegion][bestEffIdx+1: ]
                # ensure regional spending doesn't exceed remaining funds
                for regionIdx in range(self.numRegions):
                    withinBudget = nonzero(spendingVec[regionIdx] <= remainingFunds)[0]
                    spendingVec[regionIdx] = spendingVec[regionIdx][withinBudget]
                    outcomeVec[regionIdx] = outcomeVec[regionIdx][withinBudget]
                    costEffVecs[regionIdx] = outcomeVec[regionIdx] / spendingVec[regionIdx]
                newPercentBudgetSpent = (totalFunds - remainingFunds) / totalFunds * 100.
                if not(i%100) or (newPercentBudgetSpent - percentBudgetSpent) > 1.:
                    percentBudgetSpent = newPercentBudgetSpent
            else:
                break # nothing more to allocate

        # scale to ensure correct budget
        scaledRegionalAllocations = rescaleAllocation(totalFunds, regionalAllocations)
        return scaledRegionalAllocations

    def getBOCcostEffectiveness(self, regions, objective):
        numPoints = 2000
        costEffs = []
        spending = []
        outcome = []
        for region in regions:
            thisBOC = region.BOCs[objective]
            thisDeriv = thisBOC.derivative(nu=1)
            maxSpending = region.freeFunds  # TODO: check use of free funds and for min spending
            minSpending = sum(region.fixedAllocations) - sum(region.referenceAllocations)
            regionalSpending = linspace(minSpending, maxSpending, numPoints)
            spending.append(regionalSpending)
            outcome.append(thisBOC(spending))
            costEffs.append(thisDeriv(spending))
        return costEffs, spending, outcome

    #
    # def checkForRegionalBOCs(self):
    #     import os
    #     if os.path.exists(self.BOCsFileStem):
    #         BOCsList = [self.BOCsFileStem + region + '_BOC.csv' for region in self.regionNameList]
    #         if all([os.path.isfile(f) for f in BOCsList]): # all files must exist
    #             self.regionalBOCs = self.readRegionalBOCs()
    #         else:
    #             self.regionalBOCs = None
    #     else:
    #         os.makedirs(self.BOCsFileStem)
    #         self.regionalBOCs = None
    #
    # def readRegionalBOCs(self):
    #     import csv
    #     from numpy import array
    #     from scipy.interpolate import pchip
    #     # get BOC curve
    #     regionalBOCs = []
    #     for region in self.regionNameList:
    #         with open(self.BOCsFileStem + region + "_BOC.csv", 'rb') as f:
    #             regionalSpending = []
    #             regionalOutcome = []
    #             reader = csv.reader(f)
    #             for row in reader:
    #                 regionalSpending.append(row[0])
    #                 regionalOutcome.append(row[1])
    #         # remove column headers
    #         regionalSpending = array(regionalSpending[1:])
    #         regionalOutcome = array(regionalOutcome[1:])
    #         regionalBOCs.append(pchip(regionalSpending, regionalOutcome))
    #     return regionalBOCs
    #
    #
    # def generateAllRegionsBOC(self):  # TODO: there will be a problem here if (extraFunds + current) > (largestCascade * current)
    #     print 'reading files to generate regional BOCs..'
    #     import optimisation
    #     import math
    #     from copy import deepcopy as dcp
    #     from scipy.interpolate import pchip
    #     regionalBOCs = []
    #     for region in range(0, self.numRegions):
    #         print 'generating BOC for region: ', self.regionNameList[region]
    #         thisSpreadsheet = self.regionSpreadsheetList[region]
    #         filename = self.resultsFileStem + self.regionNameList[region]
    #         thisOptimisation = optimisation.Optimisation(thisSpreadsheet, self.numModelSteps, self.optimise, filename,
    #                                                      'dummyCostCurve')
    #         # if final cascade value is 'extreme' replace it with value we used to generate .pkl file
    #         thisCascade = dcp(self.cascadeValues)
    #         regionalTotalBudget = self.currentRegionalBudgets[region]
    #         if self.cascadeValues[-1] == 'extreme':
    #             thisCascade[-1] = math.ceil(self.nationalBudget / regionalTotalBudget)
    #         spending, outcome = thisOptimisation.generateBOCVectors(thisCascade, self.optimise)
    #         self.saveBOCcurves(spending, outcome, self.regionNameList[region])  # save so can directly optimise next time
    #         BOCthisRegion = pchip(spending, outcome)
    #         regionalBOCs.append(BOCthisRegion)
    #     print 'finished generating regional BOCs from files'
    #     self.regionalBOCs = regionalBOCs
    #
    # def saveBOCcurves(self, spending, outcome, regionName):
    #     import csv
    #     from itertools import izip
    #     with open(self.BOCsFileStem + regionName + '_BOC.csv', 'wb') as f:
    #         writer = csv.writer(f)
    #         writer.writerow(['spending', 'outcome'])
    #         writer.writerows(izip(spending, outcome))
    #     return
    #
    # def outputRegionalBOCsFile(self, filename):
    #     # if BOCs not generated, generate them
    #     if self.regionalBOCs == None:
    #         self.generateAllRegionsBOC()
    #     regionalBOCsReformat = {}
    #     for region in range(0, self.numRegions):
    #         regionName = self.regionNameList[region]
    #         regionalBOCsReformat[regionName] = {}
    #         for key in ['spending', 'outcome']:
    #             regionalBOCsReformat[regionName][key] = self.regionalBOCs[key][region]
    #     outfile = open(filename, 'wb')
    #     pickle.dump(regionalBOCsReformat, outfile)
    #     outfile.close()
    #
    # def outputTradeOffCurves(self):
    #     import csv
    #     if self.tradeOffCurves == None:
    #         self.getTradeOffCurves()
    #     # outfile = open(filename, 'wb')
    #     # pickle.dump(self.tradeOffCurves, outfile)
    #     # outfile.close()
    #     outfilename = '%strade_off_curves.csv' % (self.resultsFileStem)
    #     with open(outfilename, "wb") as f:
    #         writer = csv.writer(f)
    #         for region in range(self.numRegions):
    #             regionName = self.regionNameList[region]
    #             spending = self.tradeOffCurves[regionName]['spending'].tolist()
    #             outcome = self.tradeOffCurves[regionName]['outcome'].tolist()
    #             row1 = ['spending'] + spending
    #             row2 = ['outcome'] + outcome
    #             writer.writerow([regionName])
    #             writer.writerow(row1)
    #             writer.writerow(row2)
    #
    #
    # def outputBOCs(self):
    #     from numpy import linspace
    #     import csv
    #     if self.regionalBOCs == None:
    #         self.generateAllRegionsBOC()
    #     spendingVec = linspace(0., self.nationalBudget, 10000)
    #     outfilename = '%sBOCs.csv' % (self.resultsFileStem)
    #     with open(outfilename, 'wb') as f:
    #         writer = csv.writer(f)
    #         headers = ['spending'] + self.regionNameList
    #         writer.writerow(headers)
    #         regionalOutcomes = []
    #         for region in range(self.numRegions):
    #             regionalBOC = self.regionalBOCs[region]
    #             regionalOutcomes.append(regionalBOC(spendingVec))
    #         columnLists = [spendingVec] + regionalOutcomes
    #         writer.writerows(zip(*columnLists))
    #
    #
    # def getTradeOffCurves(self):
    #     from numpy import linspace
    #     # if BOCs not generated, generate them
    #     if self.regionalBOCs == None:
    #         self.generateAllRegionsBOC()
    #     tradeOffCurves = {}
    #     spendingVec = linspace(0., self.nationalBudget, 1000)
    #     for region in range(0, self.numRegions):
    #         regionName = self.regionNameList[region]
    #         regionalBOC = self.regionalBOCs[region]
    #         # transform BOC
    #         currentSpending = self.currentRegionalBudgets[region]
    #         baselineOutcome = regionalBOC(currentSpending)
    #         outcomeVec = regionalBOC(spendingVec)
    #         regionalImprovement = baselineOutcome - outcomeVec
    #         if self.optimise == 'thrive':
    #             regionalImprovement = -regionalImprovement
    #         additionalSpending = spendingVec - currentSpending
    #         tradeOffCurves[regionName] = {}
    #         tradeOffCurves[regionName]['spending'] = additionalSpending
    #         tradeOffCurves[regionName]['outcome'] = regionalImprovement
    #     self.tradeOffCurves = tradeOffCurves
    #
    #
    # def plotTradeOffCurves(self):
    #     import plotting
    #     self.getTradeOffCurves()
    #     plotting.plotTradeOffCurves(self.tradeOffCurves, self.regionNameList, self.optimise)
    #
    #
    # def plotRegionalBOCs(self):
    #     import plotting
    #     plotting.plotRegionalBOCs(self.regionalBOCs, self.regionNameList, self.optimise)
    #
    #
    # def getTotalNationalBudget(self):
    #     import optimisation
    #     regionalBudgets = []
    #     for region in range(0, self.numRegions):
    #         thisSpreadsheet = self.regionSpreadsheetList[region]
    #         thisOptimisation = optimisation.Optimisation(thisSpreadsheet, self.numModelSteps, self.optimise,
    #                                                      'dummyFileName', 'dummyCostCurve')
    #         regionTotalBudget = thisOptimisation.getTotalInitialBudget()
    #         regionalBudgets.append(regionTotalBudget)
    #     nationalTotalBudget = sum(regionalBudgets)
    #     return nationalTotalBudget
    #
    #
    # def getCurrentRegionalBudgets(self, IYCF_cov_regional=None):
    #     import optimisation
    #     regionalBudgets = []
    #     for region in range(0, self.numRegions):
    #         thisSpreadsheet = self.regionSpreadsheetList[region]
    #         thisOptimisation = optimisation.Optimisation(thisSpreadsheet, self.numModelSteps, self.optimise,
    #                                                      'dummyFileName', 'dummyCurve')
    #         if IYCF_cov_regional is not None:
    #             covIYCF = IYCF_cov_regional[region]
    #             regionTotalBudget = thisOptimisation.getTotalInitialBudget(covIYCF)
    #         else:
    #             regionTotalBudget = thisOptimisation.getTotalInitialBudget()
    #         regionalBudgets.append(regionTotalBudget)
    #     return regionalBudgets


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
        # [fixedRegionalSpending, programatically optimised]
        # then will get additionalFunds
        # TODO: decide if want 2 and 4, since 2 just has additionalFunds=0
        self.allScenarios = {'Scenario 1': [True, True], 'Scenario 2': [False, True],
                          'Scenario 3': [True, False], 'Scenario 4': [False, True]}

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



