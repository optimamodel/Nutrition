import os
import pso
import asd
import time
import cPickle as pickle
import pandas as pd
from copy import deepcopy as dcp
from multiprocessing import cpu_count
from numpy import array, append, linspace, nanargmax, zeros, nonzero, inf
from itertools import product
from scipy.interpolate import pchip
from csv import writer, reader
from itertools import izip
from collections import OrderedDict
from datetime import date
from nutrition import settings, data, program_info, populations, model, utils

def rescaleAllocation(totalBudget, allocation):
    new = sum(allocation)
    if new == 0:
        rescaledAllocation = dcp(allocation)
    else:
        scaleRatio = totalBudget / new
        rescaledAllocation = [x * scaleRatio for x in allocation]
    return rescaledAllocation

def _addFixedAllocations(allocations, fixedAllocations, indxList): # TODO: utils...
    """Assumes order is preserved from original list"""
    modified = dcp(allocations)
    for i, j in enumerate(indxList):
        modified[j] += fixedAllocations[i]
    return modified


def obj_func(allocation, obj, model, free, fixed, keep_inds, sign):
    thisModel = dcp(model)
    totalAllocations = fixed[:]
    # scale the allocation appropriately
    scaledAllocation = rescaleAllocation(free, allocation)
    programs = thisModel.prog_info.programs
    totalAllocations = _addFixedAllocations(totalAllocations, scaledAllocation, keep_inds)
    new_covs = []
    for i, program in enumerate(programs):
        new_covs.append( program.func(totalAllocations[i]) )
    thisModel.run_sim(new_covs, restr_cov=False)
    outcome = thisModel.get_outcome(obj) * sign
    return outcome

def make_optims(country, region, user_opts):
    demo_data, prog_data, default_params = data.get_data(country, region)
    optim_list = []
    # create all of the requested optimizations
    for opt in user_opts:
        # initialise pops and progs
        prog_info = program_info.ProgramInfo(opt.prog_set, prog_data, default_params)
        pops = populations.set_pops(demo_data, default_params)
        # set up optims
        optim = Optim(prog_info, pops, **opt.get_attr())
        optim_list.append(optim)
    return optim_list

def default_optims(project, key='default1', dorun=False):
    country = 'master'
    region = 'master'

    defaults = data.OptimOptsTest(key)
    opts = [utils.OptimOpts(**defaults.get_attr())]
    optim_list = make_optims(country, region, opts)
    project.add_optims(optim_list)
    if dorun:
        project.run_optims()

class Optim(object):
    def __init__(self, prog_info, pops, name, t, objs, mults, prog_set, active=True, parallel=True, num_runs=1,
                 add_funds=0, fix_curr=False, rem_curr=False, curve_type='linear', filter_progs=True,
                 maxiter=10, swarmsize=10, num_procs=None):
        self.name = name
        self.objs = objs
        self.mults = mults
        self.t = t
        self.prog_set = prog_set
        self.parallel = parallel
        self.num_cpus = cpu_count() if parallel else 1
        self.year_names = range(self.t[0], self.t[1] + 1)
        self.all_years = range(len(self.year_names))  # used to index lists
        self.num_runs = num_runs
        self.add_funds = add_funds
        self.fix_curr = fix_curr
        self.rem_curr = rem_curr if not fix_curr else False # can't remove if fixed
        self.curve_type = curve_type
        self.filter_progs = filter_progs
        self.maxiter = maxiter
        self.swarmsize = swarmsize

        self.prog_info = dcp(prog_info)
        self.pops = dcp(pops)
        self.model = model.Model(name, self.pops, self.prog_info, self.all_years)
        self.programs = self.model.prog_info.programs
        self.active = active

        self.optim_alloc = None
        self.BOCs = {}
        self.refs = None
        self.curr = None
        self.fixed = None
        self.free = None
        self.get_alloc(fix_curr)

    ######### SETUP ############

    def get_alloc(self, fix_curr):
        """
        Designed so that currentAllocations >= fixedAllocations >= referenceAllocations.
        referenceAllocations: these allocations cannot be reduced because it is impractical to do so.
        fixedAllocations: this is funding which cannot be reduced because of the user's wishes.
        currentAllocations: this is the total current funding (incl. reference & fixed allocations) determined by program initial coverage.
        :param fix_curr:
        :return:
        """
        self.refs = self.get_refs()
        self.curr = self.get_curr()
        self.fixed = self.get_fixed(fix_curr)
        self.free = self.get_free(fix_curr)

    def get_kwargs(self, obj, mult):
        kwargs = {'model': dcp(self.model),
                  'free': dcp(self.free) * mult,
                  'fixed': self.fixed[:],
                  'obj': obj,
                  'sign': utils.get_obj_sign(obj),
                  'keep_inds': self._filter_progs(obj)}
        return kwargs

    def get_refs(self):
        """
        Reference programs are not included in nutrition budgets, therefore these must be removed before future calculations.
        :return: 
        """
        referenceAllocations = []
        for program in self.programs:
            if program.reference:
                referenceAllocations.append(program.get_spending())
            else:
                referenceAllocations.append(0)
        return referenceAllocations

    def get_curr(self):
        allocations = []
        for program in self.programs:
            allocations.append(program.get_spending())
        return allocations

    def get_fixed(self, fix_curr):
        """
        Fixed allocations will contain reference allocations as well, for easy use in the objective function.
        Reference progs stored separately for ease of model output.
        :param fix_curr:
        :return:
        """
        if fix_curr:
            fixed = dcp(self.curr)
        else:
            fixed = dcp(self.refs)
        return fixed

    def get_free(self, fix_curr):
        """
        freeFunds = currentExpenditure + add_funds - fixedFunds (if not remove current funds)
        freeFunds = additional (if want to remove current funds)

        fixedFunds includes both reference programs as well as currentExpenditure, if the latter is to be fixed.
        I.e. if all of the currentExpenditure is fixed, freeFunds = add_funds.
        :return:
        """
        if self.rem_curr and fix_curr:
            raise Exception("::Error: Cannot remove current funds and fix current funds simultaneously::")
        elif self.rem_curr and (not fix_curr):  # this is additional to reference spending
            freeFunds = self.add_funds
        elif not self.rem_curr:
            freeFunds = sum(self.curr) - sum(self.fixed) + self.add_funds
        return freeFunds

    ######### OPTIMISATION ##########

    def run_optim(self):
        print 'Optimising for {}'.format(self.name)
        buds = self.check_budget()
        self.optim_alloc = utils.run_parallel(self.one_optim, product(self.objs, buds), self.num_cpus)

    def check_budget(self):
        """For 0 free funds, spending is equal to the fixed costs"""
        if 0 in self.mults:
            newBudgets = filter(lambda x: x > 0, self.mults)
            # output fixed spending
            for objective in self.objs:
                allocationDict = self.createDictionary(self.fixed)
                self.writeToPickle(allocationDict, 0, objective)
        else:
            newBudgets = self.mults
        return newBudgets

    @utils.trace_exception
    def one_optim(self, params):
        obj = params[0]
        mult = params[1]
        kwargs = self.get_kwargs(obj, mult)
        if kwargs['free'] != 0:
            num_progs = len(kwargs['keep_inds'])
            xmin = [0.] * num_progs
            xmax = [kwargs['free']] * num_progs # TODO: could make this cost of saturation.
            runOutputs = []
            for run in range(self.num_runs):
                now = time.time()
                x0, fopt = pso.pso(obj_func, xmin, xmax, kwargs=kwargs, maxiter=self.maxiter, swarmsize=self.swarmsize)
                x, fval, flag = asd.asd(obj_func, x0, args=kwargs, xmin=xmin, xmax=xmax, verbose=0)
                runOutputs.append((x, fval[-1]))
                self.printMessages(obj, mult, flag, now)
            bestAllocation = self.findBestAllocation(runOutputs)
            scaledAllocation = rescaleAllocation(kwargs['free'], bestAllocation)
            totalAllocation = _addFixedAllocations(self.fixed, scaledAllocation, kwargs['keep_inds'])
            bestAllocationDict = self.createDictionary(totalAllocation)
        else:
            # if no money to distribute, return the fixed costs
            bestAllocationDict = self.createDictionary(self.fixed)
        return bestAllocationDict

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

    def _filter_progs(self, obj):
        if self.filter_progs:
            threshold = 0.5
            newcov = 1.
            keep_inds = []
            # compare with 0 case
            zero_cov = [0 for prog in self.programs]
            zero_model = dcp(self.model)
            zero_model.run_sim(zero_cov, restr_cov=True)
            zero_out = zero_model.get_outcome(obj)
            for i, prog in enumerate(self.programs):
                thismodel = dcp(self.model)
                thiscov = dcp(zero_cov)
                thiscov[i] = newcov
                # scale up twin concurrently
                if prog.twin_ind:
                    thiscov[prog.twin_ind] = newcov
                thismodel.run_sim(thiscov)
                out = thismodel.get_outcome(obj)
                if abs((out - zero_out) / zero_out) * 100. > threshold:  # no impact
                    keep_inds.append(i)
                    if prog.twin_ind:
                        keep_inds.append(prog.twin_ind)
            return keep_inds
        else:
            return [i for i in range(len(self.programs))]

    def interpolateBOC(self, objective, spending, outcome):
        # need BOC for each objective in region
        # spending, outcome = self.getBOCvectors(objective)
        self.BOCs[objective] = pchip(spending, outcome, extrapolate=False)

    def getBOCvectors(self, objective, budgetMultiples):
        spending = array([])
        outcome = array([])
        for multiple in budgetMultiples:
            spending = append(spending, multiple * self.free)
            filePath = '{}/{}_{}_{}.pkl'.format(self.resultsDir, self.name, objective, multiple)
            f = open(filePath, 'rb')
            thisAllocation = pickle.load(f)
            f.close()
            output = self.oneModelRunWithOutput(thisAllocation).getOutcome(objective)
            outcome = append(outcome, output)
        return spending, outcome

    ########### FILE HANDLING ############
    # TODO: remove this, new results handling

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
        model.simulateScalar(newCoverages, restrictedCov=False)
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
            newCoverages[program.name] = program.costcov_func(allocations[program.name]) / program.unrestrictedPopSize
        return newCoverages

    def writeAllResults(self):
        currentSpending = self.createDictionary(self.curr)
        currentOutcome = self.getCurrentOutcome(currentSpending)
        referenceSpending = self.createDictionary(self.refs)
        referenceOutcome = self.getReferenceOutcome(referenceSpending)
        optimisedAllocations = self.readPickles()
        optimisedOutcomes = self.getOptimisedOutcomes(optimisedAllocations)
        currentAdditionalList = [a - b for a, b in zip(self.curr, self.refs)]
        currentAdditional = self.createDictionary(currentAdditionalList)
        optimisedAdditional = self.getOptimisedAdditional(optimisedAllocations)
        coverages = self.getOptimalCoverages(optimisedAllocations)
        self.writeOutcomesToCSV(referenceOutcome, currentOutcome, optimisedOutcomes)
        self.writeAllocationsToCSV(referenceSpending, currentAdditional, optimisedAdditional)
        self.writeCoveragesToCSV(coverages)

    def getOptimisedAdditional(self, optimised):
        fixedCostsDict = self.createDictionary(self.fixed)
        optimisedAdditional = {}
        for objective in self.objectives:
            optimisedAdditional[objective] = {}
            for multiple in self.budgetMultiples:
                add_funds = optimised[objective][multiple]
                optimisedAdditional[objective][multiple] = {}
                for programName in add_funds.iterkeys():
                    optimisedAdditional[objective][multiple][programName] = add_funds[programName] - \
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
                        (program.costcov_func(allocations[program.name]) / program.restrictedPopSize) * 100.)
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

    def setUpRegions(self, objective, fixCurrent, add_funds):
        regions = []
        for name in self.regionNames:
            fileInfo = [self.root, self.analysisType, name, '']
            resultsPath = os.path.join(self.newResultsDir, 'BOCs', objective, 'pickles')
            thisRegion = Optimisation(self.objectives, self.budgetMultiples, fileInfo, resultsPath=resultsPath,
                                      fixCurrentAllocations=fixCurrent, rem_curr=False,
                                      add_funds=add_funds, numYears=self.numYears, filterProgs=False)
            regions.append(thisRegion)
        return regions

    def optimiseScenarios(self):
        for scenario, options in self.scenarios.iteritems():
            fixBetween, fixWithin, replaceCurrent, add_funds = options
            formScenario = scenario.lower().replace(' ', '')
            self.newResultsDir = os.path.join(self.resultsDir, self.analysisType, formScenario,
                                              str(int(add_funds / 1e6)) + 'm')
            for objective in self.objectives:
                # first distribute funds between regions
                self.getRegionalBOCs(objective, fixWithin,
                                     add_funds)  # specifies if current funding is fixed within a region
                optimalDistribution = self.distributeFunds(objective, options)
                # optimise within each region
                regions = self.optimiseAllRegions(optimalDistribution, objective, options)
                self.collateAllResults(regions, objective)
                # self.getOptimalOutcomes(regions, objective)

    def getRegionalBOCs(self, objective, fixWithin, add_funds):
        print '...Generating BOCs... \n'
        regions = self.setUpRegions(objective, fixWithin, add_funds)
        jobs = self.getBOCjobs(regions, objective)
        maxRegions = int(50 / (len(self.budgetMultiples) - 1))
        runJobs(jobs, maxRegions)

    def interpolateBOCs(self, objective, fixBetween, add_funds):
        regions = self.setUpRegions(objective, fixBetween, add_funds)
        for region in regions:
            spending, outcome = self.readBOC(region.name, objective)
            region.interpolateBOC(objective, spending, outcome)
        self.writeBOCs(regions, objective)
        return regions

    def distributeFunds(self, objective, options):
        fixBetween = options[0]
        add_funds = options[-1]
        regions = self.interpolateBOCs(objective, fixBetween, add_funds)
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
        maxiters = int(1e6)

        for i in range(maxiters):
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
        fixBetween, fixWithin, removeCurrent, add_funds = options
        nationalFunds = self.getNationalCurrentSpending()
        numPoints = 10000
        costEffVecs = []
        spendingVec = []
        for region in regions:
            if fixBetween and not fixWithin:
                minSpending = sum(region.currentAllocations) - sum(region.referenceAllocations)
                maxSpending = minSpending + add_funds
            elif fixBetween and fixWithin:  # this is scenario 3, where the spending=0 corresponds to non-optimised current allocations
                minSpending = 0
                maxSpending = add_funds
            else:
                minSpending = 0
                maxSpending = nationalFunds + add_funds
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
        _fixBetween, fixWithin, replaceCurrent, add_funds = options
        budgetMultiple = [1]
        newRegions = []
        jobs = []
        for i, name in enumerate(self.regionNames):
            regionalFunds = optimisedSpending[i]
            resultsDir = os.path.join(self.newResultsDir, 'pickles')
            fileInfo = [self.root, self.analysisType, name, '']
            newOptim = Optimisation([objective], budgetMultiple, fileInfo, resultsPath=resultsDir,
                                    fixCurrentAllocations=fixWithin, rem_curr=replaceCurrent,
                                    add_funds=regionalFunds, numYears=self.numYears, filterProgs=False)
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
            region.add_funds / len(regions) + sum(region.currentAllocations) - sum(region.fixedAllocations) for
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
        # add_funds will be appended
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
