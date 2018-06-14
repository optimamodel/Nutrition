import os
import pandas as pd
from multiprocessing import cpu_count
from numpy import array, append, linspace, nanargmax, zeros, nonzero, inf
from csv import writer, reader
from itertools import izip
from collections import OrderedDict
from datetime import date

# TODO: THIS CURRENTLY DOESNT WORK

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
        filename = os.path.join(self.newResultsDir, 'BOCs', objective, 'cPickles', region + '.csv')
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
            resultsPath = os.path.join(self.newResultsDir, 'BOCs', objective, 'cPickles')
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
        remainingFunds = copy.deepcopy(totalFunds)
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
            resultsDir = os.path.join(self.newResultsDir, 'cPickles')
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
        """collates all regional output from cPickle files
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
                filePath = os.path.join(self.newResultsDir, 'cPickles', '{}_{}_{}.pkl'.format(name, objective, 1))
                infile = open(filePath, 'rb')
                thisAllocation = cPickle.load(infile)
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
                filename = os.path.join(self.newResultsDir, 'cPickles', '{}_{}_{}.pkl'.format(region.name, objective, 1))
                infile = open(filename, 'rb')
                thisAllocation = cPickle.load(infile)
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