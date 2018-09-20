import sciris as sc
from optimization import Optim
import numpy as np
from scipy.interpolate import pchip
import utils

class Geospatial:
    def __init__(self, name=None, model_name=None, region_names=None, weights=None, mults=None, prog_set=None,
                 add_funds=0, fix_curr=False, active=True):
        """
        :param name: name of the optimization (string)
        :param region_names: names of the regions to be included (list of strings)
        :param weights: weights defining an objective function (odict). See documentation in optimization.Optim()
        :param mults: the multiples of flexible funding to be optimized
        :param prog_set:
        :param add_funds:
        :param fix_curr:
        """
        self.name = name
        self.model_name = model_name
        self.regions = region_names
        self.weights = utils.process_weights(weights)
        self.mults = [0, 0.01, 0.025, 0.04, 0.05, 0.075, 0.1, 0.2, 0.3, 0.6, 1] if mults is None else mults  # these multiples are in the interval (minFreeFunds, maxFreeFunds)
        self.prog_set = prog_set
        self.add_funds = add_funds # this is additional across all regions
        self.fix_curr = fix_curr # fix current program allocations within regions
        self.active = active

        self.scenarios = None # todo: could be option from the gui or in code, specified as an odict
        self.bocs = sc.odict() # todo: not sure if want this as attribute of this or Optim() class

    def make_regions(self):
        """ Create all the Optim objects requested """
        regions = []
        for name in self.regions:
            region = Optim(name=name, model_name=self.model_name, weights=self.weights, mults=self.mults,
                           prog_set=self.prog_set, active=self.active, add_funds=self.add_funds,
                           fix_curr=self.fix_curr)
            regions.append(region)
        return regions

    def get_bocs(self, regions):
        """ Genereates the budget outcome curves for each region
         :param regions: a list of Optim objects (list of lists) """
        # extract the regions, then the budgets.
        # use the names for the odict
        # for each budget, get the value using weights
        # interpolate
        # bocs should be
        # todo: would be nice not have baseline at all, shouldn't need it if including 0 point at fixed spending
        for name, results in regions.iteritems():
            spending = np.zeros(len(results))
            output = np.zeros(len(results))
            for i, res in enumerate(results):
                outs = res.model.get_output()
                val = np.inner(outs, self.weights)
                spending[i] = res.get_allocs()[:].sum()
                output[i] = val
            self.bocs[name] = pchip(spending, output, extrapolate=False)
        return


#
#
#     # todo: REQUIRED FUNCTIONALITY
#     # generate BOCs by running multiple optimization within regions
#         # will need to create optim objects (1 per region)
#         # combination of new and old funds
#     # distribute between regions
#     # optimize again within regions
#
#
#
#     def __init__(self, objectives, root, regionNames, numYears=None, costCurveType='linear'):
#         self.root = root
#         self.analysisType = 'regional'
#         thisDate = date.today().strftime('%Y%b%d')
#         self.resultsDir = os.path.join('results', thisDate)
#         self.objectives = objectives
#         self.budgetMultiples = [0, 0.01, 0.025, 0.04, 0.05, 0.075, 0.1, 0.2, 0.3, 0.6, 1]  # these multiples are in the interval (minFreeFunds, maxFreeFunds)
#         self.regionNames = regionNames
#         self.numYears = numYears
#         self.numRegions = len(regionNames)
#         budgetFilePath = os.path.join(self.root, 'data', 'optimizationBudgets.xlsx')
#         self.scenarios = BudgetScenarios(budgetFilePath).getScenarios()  # TODO: super ugly file-finding
#         self.BOCs = {}
#
#     def getNationalCurrentSpending(self):
#         nationalFunds = 0
#         for name in self.regionNames:
#             fileInfo = [self.root, self.analysisType, name, '']
#             thisRegion = Optimization([], [], fileInfo, fixCurrentAllocations=False, createResultsDir=False)
#             nationalFunds += thisRegion.freeFunds
#         return nationalFunds
#
#     def readBOC(self, region, objective):
#         filename = os.path.join(self.newResultsDir, 'BOCs', objective, 'cPickles', region + '.csv')
#         with open(filename, 'rb') as f:
#             regionalSpending = []
#             regionalOutcome = []
#             r = reader(f)
#             for row in r:
#                 regionalSpending.append(row[0])
#                 regionalOutcome.append(row[1])
#         # remove column headers
#         regionalSpending = array(regionalSpending[1:])
#         regionalOutcome = array(regionalOutcome[1:])
#         return regionalSpending, regionalOutcome
#
#     def writeBOCs(self, regions, objective):
#         filename = os.path.join(self.newResultsDir, 'BOCs', objective, 'BOCs.csv')
#         headers = ['spending'] + [region.name for region in regions]
#         minSpend = min(regions[0].BOCs[objective].x)
#         maxSpend = max(regions[0].BOCs[objective].x)
#         newSpending = linspace(minSpend, maxSpend, 2000)
#         regionalOutcomes = []
#         with open(filename, 'wb') as f:
#             w = writer(f)
#             w.writerow(headers)
#             for region in regions:
#                 thisBOC = region.BOCs[objective]
#                 interpolated = thisBOC(newSpending)
#                 regionalOutcomes.append(interpolated)
#             columnLists = [newSpending] + regionalOutcomes
#             w.writerows(zip(*columnLists))
#
#     def getBOCjobs(self, regions, objective):
#         jobs = []
#         for region in regions:
#             resultsPath = region.resultsDir
#             prc = Process(target=self.optimizeAndWrite, args=(region, objective, resultsPath))
#             jobs.append(prc)
#         return jobs
#
#     def optimizeAndWrite(self, region, objective, resultsPath):
#         region.optimize()
#         self.writeBudgetOutcome(region, objective, resultsPath)
#
#     def writeBudgetOutcome(self, region, objective, resultsPath):
#         spending, outcome = region.getBOCvectors(objective, self.budgetMultiples)
#         filename = os.path.join(resultsPath, region.name + '.csv')
#         with open(filename, 'wb') as f:
#             w = writer(f)
#             w.writerow(['spending', 'outcome'])
#             w.writerows(izip(spending, outcome))
#
#     def setUpRegions(self, objective, fixCurrent, add_funds):
#         regions = []
#         for name in self.regionNames:
#             fileInfo = [self.root, self.analysisType, name, '']
#             resultsPath = os.path.join(self.newResultsDir, 'BOCs', objective, 'cPickles')
#             thisRegion = Optimization(self.objectives, self.budgetMultiples, fileInfo, resultsPath=resultsPath,
#                                       fixCurrentAllocations=fixCurrent, rem_curr=False,
#                                       add_funds=add_funds, numYears=self.numYears, filterProgs=False)
#             regions.append(thisRegion)
#         return regions
#
#     def optimizeScenarios(self):
#         for scenario, options in self.scenarios.iteritems():
#             fixBetween, fixWithin, replaceCurrent, add_funds = options
#             formScenario = scenario.lower().replace(' ', '')
#             self.newResultsDir = os.path.join(self.resultsDir, self.analysisType, formScenario,
#                                               str(int(add_funds / 1e6)) + 'm')
#             for objective in self.objectives:
#                 # first distribute funds between regions
#                 self.getRegionalBOCs(objective, fixWithin,
#                                      add_funds)  # specifies if current funding is fixed within a region
#                 optimalDistribution = self.distributeFunds(objective, options)
#                 # optimize within each region
#                 regions = self.optimizeAllRegions(optimalDistribution, objective, options)
#                 self.collateAllResults(regions, objective)
#                 # self.getOptimalOutcomes(regions, objective)
#
#     def getRegionalBOCs(self, objective, fixWithin, add_funds):
#         print('...Generating BOCs... \n')
#         regions = self.setUpRegions(objective, fixWithin, add_funds)
#         jobs = self.getBOCjobs(regions, objective)
#         maxRegions = int(50 / (len(self.budgetMultiples) - 1))
#         runJobs(jobs, maxRegions)
#
#     def interpolateBOCs(self, objective, fixBetween, add_funds):
#         regions = self.setUpRegions(objective, fixBetween, add_funds)
#         for region in regions:
#             spending, outcome = self.readBOC(region.name, objective)
#             region.interpolateBOC(objective, spending, outcome)
#         self.writeBOCs(regions, objective)
#         return regions
#
#     def distributeFunds(self, objective, options):
#         fixBetween = options[0]
#         add_funds = options[-1]
#         regions = self.interpolateBOCs(objective, fixBetween, add_funds)
#         optimalDistribution = self.gridSearch(regions, objective, options)
#         return optimalDistribution
#
#     def writeRefAndCurrentAllocations(self, regions, filename):
#         sortedProgs = sorted([prog.name for prog in regions[0].programs.values()])
#         with open(filename, 'wb') as f:
#             w = writer(f)
#             w.writerow(['Reference'] + sortedProgs)
#             for region in regions:
#                 name = region.name
#                 refDict = region.createDictionary(region.referenceAllocations)
#                 sortedRef = OrderedDict(sorted(refDict.items())).values()
#                 w.writerow([name] + sortedRef)
#             w.writerow([])
#             w.writerow(['Current'] + sortedProgs)
#             for region in regions:
#                 name = region.name
#                 currentAdditional = [a - b for a, b in zip(region.currentAllocations, region.referenceAllocations)]
#                 currentAdditionalDict = region.createDictionary(currentAdditional)
#                 sortedCurrent = OrderedDict(sorted(currentAdditionalDict.items())).values()
#                 w.writerow([name] + sortedCurrent)
#             w.writerow([])
#
#     def gridSearch(self, regions, objective, options):
#         costEffVecs, spendingVec = self.getBOCcostEffectiveness(regions, objective, options)
#         totalFunds = self.getTotalFreeFunds(regions)
#         remainingFunds = copy.deepcopy(totalFunds)
#         regionalAllocations = zeros(len(regions))
#         percentBudgetSpent = 0.
#         maxiters = int(1e6)
#
#         for i in range(maxiters):
#             bestEff = -inf
#             bestRegion = None
#             for regionIdx in range(len(regions)):
#                 # find most effective spending in each region
#                 costEffThisRegion = costEffVecs[regionIdx]
#                 if len(costEffThisRegion):
#                     maxIdx = nanargmax(costEffThisRegion)
#                     maxEff = costEffThisRegion[maxIdx]
#                     if maxEff > bestEff:
#                         bestEff = maxEff
#                         bestEffIdx = maxIdx
#                         bestRegion = regionIdx
#             # once the most cost-effective spending is found, adjust all spending and outcome vectors, update available funds and regional allocation
#             if bestRegion is not None:
#                 fundsSpent = spendingVec[bestRegion][bestEffIdx]
#                 remainingFunds -= fundsSpent
#                 spendingVec[bestRegion] -= fundsSpent
#                 regionalAllocations[bestRegion] += fundsSpent
#                 # remove funds and derivatives at or below zero
#                 spendingVec[bestRegion] = spendingVec[bestRegion][bestEffIdx + 1:]
#                 costEffVecs[bestRegion] = costEffVecs[bestRegion][bestEffIdx + 1:]
#                 # ensure regional spending doesn't exceed remaining funds
#                 for regionIdx in range(self.numRegions):
#                     withinBudget = nonzero(spendingVec[regionIdx] <= remainingFunds)[0]
#                     spendingVec[regionIdx] = spendingVec[regionIdx][withinBudget]
#                     costEffVecs[regionIdx] = costEffVecs[regionIdx][withinBudget]
#                 newPercentBudgetSpent = (totalFunds - remainingFunds) / totalFunds * 100.
#                 if not (i % 100) or (newPercentBudgetSpent - percentBudgetSpent) > 1.:
#                     percentBudgetSpent = newPercentBudgetSpent
#             else:
#                 break  # nothing more to allocate
#
#         # scale to ensure correct budget
#         scaledRegionalAllocations = rescaleAllocation(totalFunds, regionalAllocations)
#         return scaledRegionalAllocations
#
#     def getBOCcostEffectiveness(self, regions, objective, options):
#         fixBetween, fixWithin, removeCurrent, add_funds = options
#         nationalFunds = self.getNationalCurrentSpending()
#         numPoints = 10000
#         costEffVecs = []
#         spendingVec = []
#         for region in regions:
#             if fixBetween and not fixWithin:
#                 minSpending = sum(region.currentAllocations) - sum(region.referenceAllocations)
#                 maxSpending = minSpending + add_funds
#             elif fixBetween and fixWithin:  # this is scenario 3, where the spending=0 corresponds to non-optimized current allocations
#                 minSpending = 0
#                 maxSpending = add_funds
#             else:
#                 minSpending = 0
#                 maxSpending = nationalFunds + add_funds
#             thisDeriv = region.BOCs[objective].derivative(nu=1)
#             regionalSpending = linspace(minSpending, maxSpending, numPoints)[1:]  # exclude 0 to avoid division error
#             adjustedSpending = regionalSpending - minSpending  # centers spending if current is fixed
#             spendingVec.append(adjustedSpending)
#             # use non-adjusted spending b/c we don't necessarily want to start at 0
#             costEffectiveness = thisDeriv(regionalSpending)  # needs to be neg if have decreasing func
#             costEffVecs.append(costEffectiveness)
#         return costEffVecs, spendingVec
#
#     def optimizeAllRegions(self, optimizedSpending, objective, options):
#         print('...Optimizing within regions... \n')
#         _fixBetween, fixWithin, replaceCurrent, add_funds = options
#         budgetMultiple = [1]
#         newRegions = []
#         jobs = []
#         for i, name in enumerate(self.regionNames):
#             regionalFunds = optimizedSpending[i]
#             resultsDir = os.path.join(self.newResultsDir, 'cPickles')
#             fileInfo = [self.root, self.analysisType, name, '']
#             newOptim = Optimization([objective], budgetMultiple, fileInfo, resultsPath=resultsDir,
#                                     fixCurrentAllocations=fixWithin, rem_curr=replaceCurrent,
#                                     add_funds=regionalFunds, numYears=self.numYears, filterProgs=False)
#             newRegions.append(newOptim)
#             p = Process(target=newOptim.optimize)
#             jobs.append(p)
#         runJobs(jobs, min(cpu_count(), 50))
#         return newRegions
#
#     def collateAllResults(self, regions, objective):
#         """collates all regional output from cPickle files
#         Uses append file method to avoid over-writing"""
#         filename = os.path.join(self.newResultsDir, 'regional_allocations_' + objective + '.csv')
#         # write the programs to row for each objective
#         self.writeRefAndCurrentAllocations(regions, filename)
#         sortedProgs = sorted([prog.name for prog in regions[0].programs.values()])
#         with open(filename, 'a') as f:
#             w = writer(f)
#             w.writerow([''] + sortedProgs)
#             for region in regions:
#                 name = region.name
#                 filePath = os.path.join(self.newResultsDir, 'cPickles', '{}_{}_{}.pkl'.format(name, objective, 1))
#                 infile = open(filePath, 'rb')
#                 thisAllocation = cPickle.load(infile)
#                 infile.close()
#                 allocations = OrderedDict(sorted(thisAllocation.items()))
#                 # remove fixed funds
#                 fixedAllocations = region.fixedAllocations
#                 fixedAllocationsDict = region.createDictionary(fixedAllocations)
#                 fixedAllocations = OrderedDict(sorted(fixedAllocationsDict.items())).values()
#                 optimizedAdditional = [a - b for a, b in zip(allocations.values(), fixedAllocations)]
#                 w.writerow([name] + optimizedAdditional)
#             w.writerow([])
#
#     def getOptimalOutcomes(self, regions, objective):
#         outcomes = ['total_stunted', 'wasting_prev', 'anaemia_prev_children', 'deaths_children', 'neonatal_deaths']
#         fileToWrite = os.path.join(self.newResultsDir, 'optimal_outcomes_{}.csv'.format(objective))
#         with open(fileToWrite, 'wb') as f:
#             w = writer(f)
#             w.writerow(['Region'] + outcomes)
#             for region in regions:
#                 filename = os.path.join(self.newResultsDir, 'cPickles', '{}_{}_{}.pkl'.format(region.name, objective, 1))
#                 infile = open(filename, 'rb')
#                 thisAllocation = cPickle.load(infile)
#                 infile.close()
#                 allOutputs = []
#                 thisModel = region.oneModelRunWithOutput(thisAllocation)
#                 for outcome in outcomes:
#                     allOutputs.append(thisModel.getOutcome(outcome))
#                 w.writerow([region.name] + allOutputs)
#
#     def getTotalFreeFunds(self, regions):
#         """ Need to wait the additional funds by number of regions so we don't have too much money"""
#         return sum(
#             region.add_funds / len(regions) + sum(region.currentAllocations) - sum(region.fixedAllocations) for
#             region in regions)
#
# class BudgetScenarios:
#     """
#     Descriptions of budget scenarios found in the corresponding .xlsx file
#     Need to specify:
#     - is current regional spending fixed
#     - is current allocation to be programatically optimized
#     - amount of additional funds, if any.
#
#     """
#
#     def __init__(self, filePath):
#         self.filePath = filePath
#         # [fixedBetweenRegions, fixedWithinRegion, replaceCurrent]
#         # add_funds will be appended
#         self.allScenarios = {'Scenario 1': [True, False, False],
#                              'Scenario 2': [False, False, True],
#                              'Scenario 3': [True, True, False]}
#
#     def getScenarios(self):
#         """
#         This information should be contained in a separate .xlsx file,
#         which details the current expenditure by region, and all the optimization scenarios.
#         :return:
#         """
#         thisSheet = pd.read_excel(self.filePath, 'Optimal funding scenario', index_col=[0])
#         thisSheet = thisSheet.drop(['Current spending description', 'Additional spending description'], 1)
#         scenarios = {}
#         for scenario, row in thisSheet.iterrows():
#             if pd.notnull(row[1]):
#                 scenarios[scenario] = self.allScenarios[scenario] + [row[0]]  # adding funds
#         return scenarios