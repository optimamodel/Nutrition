# -*- coding: utf-8 -*-
"""
Created on Wed Jun  8 13:58:29 2016

@author: ruth
"""
def returnAlphabeticalDictionary(dictionary):
    from collections import OrderedDict
    dictionaryOrdered = OrderedDict([])
    order = sorted(dictionary)
    for i in range(0, len(dictionary)):
        dictionaryOrdered[order[i]] = dictionary[order[i]]    
    return dictionaryOrdered 


def rescaleAllocation(totalBudget, allocation):
    scaleRatio = totalBudget / sum(allocation)
    rescaledAllocation = [x * scaleRatio for x in allocation]
    return rescaledAllocation


def runModelForNTimeSteps(timesteps, spreadsheetData, model, saveEachStep=False): # TODO: consider moving into optimisation class
    import helper
    from copy import deepcopy as dc
    helper = helper.Helper()
    modelList = []
    if model is None:   # instantiate a model
        model = helper.setupModelDerivedParameters(spreadsheetData)[0]
    for step in range(timesteps):
        model.moveModelOneYear()
        if saveEachStep:
            modelThisTimeStep = dc(model)
            modelList.append(modelThisTimeStep)
    return model, modelList


    
def objectiveFunction(allocation, costCurves, model, totalBudget, fixedCosts, costCoverageInfo, objective, numModelSteps, dataSpreadsheetName, data, timestepsPre):
    from copy import deepcopy as dcp
    from operator import add
    from numpy import maximum, minimum
    eps = 1.e-3 ## WARNING: using project non-specific eps
    modelThisRun = dcp(model)
    availableBudget = totalBudget - sum(fixedCosts)
    #make sure fixed costs do not exceed total budget
    if totalBudget < sum(fixedCosts):
        print "error: total budget is less than fixed costs"
        return
    # scale the allocation appropriately
    if sum(allocation) == 0:
        scaledAllocation = dcp(allocation)
    else:
        scaledAllocation = rescaleAllocation(availableBudget, allocation)
    # add the fixed costs to the scaled allocation of available budget
    scaledAllocation = map(add, scaledAllocation, fixedCosts)
    newCoverages = {}
    # get coverage for given allocation by intervention
    for i in range(0, len(data.interventionList)):
        intervention = data.interventionList[i]
        costCurveThisIntervention = costCurves[intervention]
        newCoverages[intervention] = maximum(costCurveThisIntervention(scaledAllocation[i]), eps)
        newCoverages[intervention] = minimum(newCoverages[intervention], 1.0)
    modelThisRun.updateCoverages(newCoverages)
    steps = numModelSteps - timestepsPre
    modelThisRun = runModelForNTimeSteps(steps, data, modelThisRun)[0]
    performanceMeasure = modelThisRun.getOutcome(objective)
    if objective == 'thrive':
        performanceMeasure = - performanceMeasure
    return performanceMeasure
    
def geospatialObjectiveFunction(spendingList, regionalBOCs, totalBudget, optimise):
    import pchip
    from copy import deepcopy as dcp
    numRegions = len(spendingList)
    if sum(spendingList) == 0:
        scaledSpendingList = dcp(spendingList)
    else:
        scaledSpendingList = rescaleAllocation(totalBudget, spendingList)
    outcomeList = []
    for region in range(0, numRegions):
        outcome = pchip.pchip(regionalBOCs['spending'][region], regionalBOCs['outcome'][region], scaledSpendingList[region], deriv = False, method='pchip')        
        outcomeList.append(outcome)
    nationalOutcome = sum(outcomeList)
    if optimise == 'thrive':
        nationalOutcome = - nationalOutcome
    return nationalOutcome    
    
def geospatialObjectiveFunctionExtraMoney(spendingList, regionalBOCs, currentRegionalSpendingList, extraMoney, optimise):
    import pchip
    from copy import deepcopy as dcp
    numRegions = len(spendingList)
    if sum(spendingList) == 0: 
        scaledSpendingList = dcp(spendingList)
    else:    
        scaledSpendingList = rescaleAllocation(extraMoney, spendingList)    
    outcomeList = []
    for region in range(0, numRegions):
        newTotalSpending = currentRegionalSpendingList[region] + scaledSpendingList[region]
        outcome = pchip.pchip(regionalBOCs['spending'][region], regionalBOCs['outcome'][region], newTotalSpending, deriv = False, method='pchip')        
        outcomeList.append(outcome)
    nationalOutcome = sum(outcomeList)
    if optimise == 'thrive':
        nationalOutcome = - nationalOutcome
    return nationalOutcome        

            
class OutputClass:
    def __init__(self, budgetBest, fval, exitflag, cleanOutputIterations, cleanOutputFuncCount, cleanOutputFvalVector, cleanOutputXVector):
        self.budgetBest = budgetBest
        self.fval = fval
        self.exitflag = exitflag
        self.cleanOutputIterations = cleanOutputIterations
        self.cleanOutputFuncCount = cleanOutputFuncCount
        self.cleanOutputFvalVector = cleanOutputFvalVector
        self.cleanOutputXVector = cleanOutputXVector      

class NotEnoughCoresError(Exception):
    "Not enough physical cores to parallelise for num objectives * num cascades"
    pass

class Optimisation:
    def __init__(self, cascadeValues, objectivesList, dataSpreadsheetName, resultsFileStem, country, costCurveType='standard',
                 parallel=False, numRuns=10, numModelSteps=14, haveFixedCosts=False, interventionsToRemove=None):
        import helper
        import data
        from multiprocessing import cpu_count
        self.cascadeValues = cascadeValues
        self.objectivesList = objectivesList
        self.country = country
        self.dataSpreadsheetName = dataSpreadsheetName
        self.numModelSteps = numModelSteps
        self.parallel = parallel
        self.numCPUs = cpu_count()
        self.numRuns = numRuns
        self.costCurveType = costCurveType
        self.helper = helper.Helper()
        self.data = data.readSpreadsheet(dataSpreadsheetName, self.helper.keyList, interventionsToRemove=interventionsToRemove)
        self.programList = self.data.interventionList
        self.timeSeries = None
        self.costCoverageInfo = self.getCostCoverageInfo()
        self.targetPopSize = self.getInitialTargetPopSize()
        self.inititalProgramAllocations = self.getTotalInitialAllocation()
        self.totalBudget = sum(self.inititalProgramAllocations)
        self.fixedCosts = self.getFixedCosts(haveFixedCosts, self.inititalProgramAllocations)
        self.timeStepsPre = 12
        self.model = runModelForNTimeSteps(self.timeStepsPre, self.data, model=None)[0]
        self.costCurves = self.generateCostCurves(self.model)
        self.kwargs = {'costCurves': self.costCurves, 'model': self.model, 'timestepsPre': self.timeStepsPre,
                'totalBudget': self.totalBudget, 'fixedCosts': self.fixedCosts, 'costCoverageInfo': self.costCoverageInfo,
                'numModelSteps': self.numModelSteps,
                'dataSpreadsheetName': self.dataSpreadsheetName, 'data': self.data}
        # check that results directory exists and if not then create it
        import os
        self.resultDirectories = {}
        for objective in self.objectivesList + ['results']:
            self.resultDirectories[objective] = resultsFileStem +'/'+objective
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
            for multiple in self.cascadeValues:
                self.runOptimisation(multiple, objective)

    def getJobs(self):
        from multiprocessing import Process
        jobs = []
        for objective in self.objectivesList:
            for multiple in self.cascadeValues:
                p = Process(target=self.runOptimisation, args=(multiple, objective))
                jobs.append(p)
        return jobs

    def runJobs(self, jobs):
        while jobs:
            thisRound = min(self.numCPUs, len(jobs))
            for process in range(thisRound):
                p = jobs[process]
                p.start()
            for process in range(thisRound): # this loop ensures process group waits
                p = jobs[process]
                p.join()
            jobs = jobs[thisRound:]
        return

    def runOptimisation(self, multiple, objective):
        from pyswarm import pso
        import asd as asd
        from copy import deepcopy as dcp
        kwargs = dcp(self.kwargs)
        kwargs['totalBudget'] *= multiple
        kwargs['objective'] = objective
        xmin = [0.] * len(self.programList)
        xmax = [kwargs['totalBudget']] * len(self.programList)
        runOutputs = []
        for run in range(self.numRuns):
            x0, fopt = pso(objectiveFunction, xmin, xmax, kwargs=kwargs, maxiter=20, swarmsize=200)
            print " "
            print "THIS IS RUN " + str(run)
            print "x0: " + str(fopt)
            budgetBest, fval, exitflag, output = asd.asd(objectiveFunction, x0, kwargs, xmin=xmin,
                                                         xmax=xmax, verbose=0)
            outputOneRun = OutputClass(budgetBest, fval, exitflag, output.iterations, output.funcCount, output.fval,
                                       output.x)
            runOutputs.append(outputOneRun)
        bestAllocation = self.findBestAllocation(runOutputs)
        scaledAllocation = self.adjustAllocation(bestAllocation, kwargs)
        bestAllocationDict = self.createDictionary(scaledAllocation, self.programList)
        self.writeToPickle(bestAllocationDict, multiple, objective)
        return

    def findBestAllocation(self, outputs):
        bestSample = max(outputs, key=lambda item: item.fval)
        return bestSample.budgetBest

    def adjustAllocation(self, bestOutput, kwargs):
        availableBudget = kwargs['totalBudget'] - sum(kwargs['fixedCosts'])
        scaledAllocation = rescaleAllocation(availableBudget, bestOutput)
        return scaledAllocation

    def createDictionary(self, values, keys):
        """Ensure keys and values have matching orders"""
        returnDict = {}
        for idx in range(len(keys)):
            key = keys[idx]
            returnDict[key] = values[idx]
        return returnDict



    ########### FILE HANDLING ############

    def writeToPickle(self, allocation, multiple, objective):
        import pickle
        fileName = self.resultDirectories[objective]+'/'+ self.country+'_cascade_'+str(objective)+'_'+str(multiple)+'.pkl'
        outfile = open(fileName, 'wb')
        pickle.dump(allocation, outfile)
        return

    def checkParallel(self, numCores, numCascades):
        terminate = False
        try:
            if numCascades * len(self.objectivesList) >  numCores:
                raise NotEnoughCoresError
        except NotEnoughCoresError:
            print "There aren't enough physical cores to parallelise (num objectives * num cascades) optimisations"
            terminate = True
        return terminate

    def readPickles(self):
        import pickle
        allocations = {}
        for objective in self.objectivesList:
            allocations[objective] = {}
            direc = self.resultDirectories[objective]
            for multiple in self.cascadeValues:
                filename = '%s/%s_cascade_%s_%s.pkl' % (direc, self.country, objective, str(multiple))
                f = open(filename, 'rb')
                allocations[objective][multiple] = pickle.load(f)
                f.close()
        return allocations

    def getOutcome(self, allocation, objective):
        modelList = self.oneModelRunWithOutput(allocation)
        outcome = modelList[-1].getOutcome(objective)
        return outcome

    def getOptimisedOutcomes(self, allocations):
        outcomes = {}
        for objective in self.objectivesList:
            outcomes[objective] = {}
            for multiple in self.cascadeValues:
                thisAllocation = allocations[objective][multiple]
                outcomes[objective][multiple] = self.getOutcome(thisAllocation, objective)
        return outcomes

    def getCurrentOutcome(self, currentSpending):
        currentOutcome = {}
        for objective in self.objectivesList:
            currentOutcome[objective] = {}
            currentOutcome[objective]['current'] = self.getOutcome(currentSpending, objective)
        return currentOutcome

    def getBaselineOutcome(self):
        zeroSpending = {program: 0 for program in self.programList}
        baseline = {}
        for objective in self.objectivesList:
            baseline[objective] = {}
            baseline[objective]['baseline'] = self.getOutcome(zeroSpending, objective)
        return baseline

    def writeAllResults(self):
        baselineOutcome = self.getBaselineOutcome()
        currentSpending = self.createDictionary(self.inititalProgramAllocations, self.programList)
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
        budgets =  ['baseline','current'] + self.cascadeValues
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
            w.writerow(sortedCurrent.keys())
            w.writerow(['current'])
            w.writerow(['']+ sortedCurrent.values())
            for objective in self.objectivesList:
                w.writerow([''])
                w.writerow([objective] + sorted(optimised[objective[0]][self.cascadeValues[0]].keys()))
                for multiple in self.cascadeValues:
                    allocation = OrderedDict(sorted(optimised[objective][multiple].items()))
                    w.writerow([multiple] + allocation.values())

    def getCoverages(self, allocations):
        newCoverages = {}
        for program in self.programList:
            costCurve = self.costCurves[program]
            newCoverages[program] = costCurve(allocations[program])
        return newCoverages



############# OLD CODE BELOW #############


    def performSingleOptimisation(self, MCSampleSize, haveFixedProgCosts):
        costCoverageInfo = self.getCostCoverageInfo()
        initialTargetPopSize = self.getInitialTargetPopSize()
        initialAllocation = getTotalInitialAllocation(self.data, costCoverageInfo, initialTargetPopSize)
        totalBudget = sum(initialAllocation)
        xmin = [0.] * len(initialAllocation)
        # set up and run the model prior to optimising
        fixedCosts = self.getFixedCosts(haveFixedProgCosts, initialAllocation)
        timestepsPre = 12
        model = runModelForNTimeSteps(timestepsPre, self.data, model=None)[0]
        # generate cost curves for each intervention
        costCurves = self.generateCostCurves(model)
        args = {'costCurves': costCurves, 'model': model, 'timestepsPre': timestepsPre,
                'totalBudget': totalBudget, 'fixedCosts': fixedCosts, 'costCoverageInfo': costCoverageInfo,
                'optimise': self.optimise, 'numModelSteps': self.numModelSteps,
                'dataSpreadsheetName': self.dataSpreadsheetName, 'data': self.data}
        self.runOnce(MCSampleSize, xmin, args, self.data.interventionList, totalBudget, self.resultsFileStem+'.pkl')
        
    def performSingleOptimisationForGivenTotalBudget(self, MCSampleSize, totalBudget, filename, haveFixedProgCosts):
        costCoverageInfo = self.getCostCoverageInfo()
        xmin = [0.] * len(self.data.interventionList)
        initialTargetPopSize = self.getInitialTargetPopSize() 
        initialAllocation = getTotalInitialAllocation(self.data, costCoverageInfo, initialTargetPopSize)
        fixedCosts = self.getFixedCosts(haveFixedProgCosts, initialAllocation)
        timestepsPre = 12
        # set up and run the model prior to optimising
        model = runModelForNTimeSteps(timestepsPre, self.data, model=None)[0]
        # generate cost curves for each intervention
        costCurves = self.generateCostCurves(model)
        args = {'costCurves': costCurves, 'model': model, 'timestepsPre': timestepsPre,
                'totalBudget': totalBudget, 'fixedCosts': fixedCosts, 'costCoverageInfo': costCoverageInfo,
                'optimise': self.optimise, 'numModelSteps': self.numModelSteps,
                'dataSpreadsheetName': self.dataSpreadsheetName, 'data': self.data}
        self.runOnce(MCSampleSize, xmin, args, self.data.interventionList, totalBudget, self.resultsFileStem+filename+'.pkl')

        
    def performCascadeOptimisation(self, MCSampleSize, cascadeValues, haveFixedProgCosts):
        timestepsPre = 12
        costCoverageInfo = self.getCostCoverageInfo()
        initialTargetPopSize = self.getInitialTargetPopSize()
        initialAllocation = getTotalInitialAllocation(self.data, costCoverageInfo, initialTargetPopSize)
        currentTotalBudget = sum(initialAllocation)
        xmin = [0.] * len(initialAllocation)
        # set fixed costs if you have them
        fixedCosts = self.getFixedCosts(haveFixedProgCosts, initialAllocation)
        # run the model prior to optimising
        model = runModelForNTimeSteps(timestepsPre, self.data, model=None)[0]
        # generate cost curves for each intervention
        costCurves = self.generateCostCurves(model)
        for cascade in cascadeValues:
            totalBudget = currentTotalBudget * cascade
            args = {'costCurves': costCurves, 'model': model, 'timestepsPre': timestepsPre,
                    'totalBudget':totalBudget, 'fixedCosts':fixedCosts, 'costCoverageInfo':costCoverageInfo,
                    'optimise':self.optimise, 'numModelSteps':self.numModelSteps,
                    'dataSpreadsheetName':self.dataSpreadsheetName, 'data':self.data}
            outFile = self.resultsFileStem+'_cascade_'+str(self.optimise)+'_'+str(cascade)+'.pkl'
            self.runOnce(MCSampleSize, xmin, args, self.data.interventionList, totalBudget, outFile)

    def cascadeParallelRunFunction(self, costCurves, model, timestepsPre, cascadeValue, currentTotalBudget, fixedCosts, spreadsheetData, costCoverageInfo, MCSampleSize, xmin):
        totalBudget = currentTotalBudget * cascadeValue
        geneticArgs = (costCurves, model, totalBudget, fixedCosts, costCoverageInfo,
                       self.optimise, self.numModelSteps, self.dataSpreadsheetName,
                       spreadsheetData, timestepsPre)
        asdArgs = {'costCurves': costCurves, 'model': model, 'timestepsPre': timestepsPre,
                'totalBudget': totalBudget, 'fixedCosts': fixedCosts, 'costCoverageInfo': costCoverageInfo,
                'optimise': self.optimise, 'numModelSteps': self.numModelSteps,
                'dataSpreadsheetName': self.dataSpreadsheetName, 'data': spreadsheetData}
        outFile = self.resultsFileStem+'_cascade_'+str(self.optimise)+'_'+str(cascadeValue)+'.pkl'
        self.runOnce(MCSampleSize, xmin, geneticArgs, asdArgs, spreadsheetData.interventionList, totalBudget, outFile)

    def performParallelCascadeOptimisation(self, MCSampleSize, cascadeValues, numCores, haveFixedProgCosts):
        from multiprocessing import Process
        xmin = [0.] * len(self.inititalProgramAllocations)
        timestepsPre = 12
        # set fixed costs if you have them
        fixedCosts = self.getFixedCosts(haveFixedProgCosts, self.inititalProgramAllocations)
        # check that you have enough cores and don't parallelise if you don't
        if numCores < len(cascadeValues):
            print "numCores is not enough"
        else:
            for value in cascadeValues:
                prc = Process(
                    target=self.cascadeParallelRunFunction,
                    args=(self.costCurves, self.model, timestepsPre, value, self.totalBudget, fixedCosts, self.data,
                            self.costCoverageInfo, MCSampleSize, xmin))
                prc.start()

        
    def performParallelSampling(self, MCSampleSize, haveFixedProgCosts, numRuns, filename):
        from multiprocessing import Process
        costCoverageInfo = self.getCostCoverageInfo()
        initialTargetPopSize = self.getInitialTargetPopSize()          
        initialAllocation = getTotalInitialAllocation(self.data, costCoverageInfo, initialTargetPopSize)
        currentTotalBudget = sum(initialAllocation)
        xmin = [0.] * len(initialAllocation)
        # set fixed costs if you have them
        fixedCosts = self.getFixedCosts(haveFixedProgCosts, initialAllocation) 
        runOnceArgs = {'totalBudget':currentTotalBudget, 'fixedCosts':fixedCosts, 'costCoverageInfo':costCoverageInfo,
                       'optimise':self.optimise, 'numModelSteps':self.numModelSteps, 'dataSpreadsheetName':self.dataSpreadsheetName, 'data':self.data}
        for i in range(numRuns):
            prc = Process(
                target=self.runOnceDumpFullOutputToFile, 
                args=(MCSampleSize, xmin, runOnceArgs, self.data.interventionList, currentTotalBudget, filename+"_"+str(i)))
            prc.start()    

    def performParallelCascadeOptimisationAlteredInterventionEffectiveness(self, MCSampleSize, cascadeValues, numCores, haveFixedProgCosts, intervention, effectiveness, savePlot):
        from multiprocessing import Process
        costCoverageInfo = self.getCostCoverageInfo()
        initialTargetPopSize = self.getInitialTargetPopSize()
        initialAllocation = getTotalInitialAllocation(self.data, costCoverageInfo, initialTargetPopSize)
        currentTotalBudget = sum(initialAllocation)
        xmin = [0.] * len(initialAllocation)
        timestepsPre = 12
        # set fixed costs if you have them
        fixedCosts = self.getFixedCosts(haveFixedProgCosts, initialAllocation)
        # alter mortality & incidence effectiveness
        for ageName in self.helper.keyList['ages']:
            self.data.effectivenessMortality[intervention][ageName]['Diarrhea'] *= effectiveness
            self.data.effectivenessIncidence[intervention][ageName]['Diarrhea'] *= effectiveness
        # set up and run the model prior to optimising
        model = runModelForNTimeSteps(timestepsPre, self.data, model=None)[0]
        # generate cost curves for each intervention
        if savePlot:
            resultsPath = self.resultsFileStem
        else:
            resultsPath = None
        costCurves = self.generateCostCurves(model, resultsFileStem=resultsPath, budget=currentTotalBudget, cascade=cascadeValues)
        # check that you have enough cores and don't parallelise if you don't
        if numCores < len(cascadeValues):
            print "numCores is not enough"
        else:
            for value in cascadeValues:
                prc = Process(
                    target=self.cascadeParallelRunFunction,
                    args=(costCurves, model, timestepsPre, value, currentTotalBudget, fixedCosts, self.data,
                            costCoverageInfo, MCSampleSize, xmin))
                prc.start()
        
    def getFixedCosts(self, haveFixedProgCosts, initialAllocation):
        from copy import deepcopy as dcp
        if haveFixedProgCosts:
            fixedCosts = dcp(initialAllocation)
        else:
            fixedCosts = [0.] * len(initialAllocation)
        return fixedCosts

    def getTotalInitialAllocation(self):
        import costcov
        costCov = costcov.Costcov()
        allocations = []
        for intervention in self.data.interventionList:
            coverageFraction = self.data.coverage[intervention]
            coverageNumber = coverageFraction * self.targetPopSize[intervention]
            spending = costCov.getSpending(coverageNumber, self.costCoverageInfo[intervention],
                                               self.targetPopSize[intervention])
            allocations.append(spending)
        return allocations
    
    def runOnce(self, MCSampleSize, xmin, geneticArgs, asdArgs, interventionList, totalBudget, filename):
        import asd as asd
        import pickle
        from operator import add
        from scipy.optimize import differential_evolution
        numInterventions = len(interventionList)
        scenarioMonteCarloOutput = []
        bounds = [(0., totalBudget)] * numInterventions
        xmax = [totalBudget] * numInterventions
        for r in range(0, MCSampleSize):
            result = differential_evolution(objectiveFunction, bounds=bounds,args=geneticArgs, maxiter=3, popsize=15, disp=True)
            proposalAllocation = result.x
            budgetBest, fval, exitflag, output = asd.asd(objectiveFunction, proposalAllocation, asdArgs, xmin = xmin, xmax=xmax, verbose = 1)
            outputOneRun = OutputClass(budgetBest, fval, exitflag, output.iterations, output.funcCount, output.fval, output.x)
            scenarioMonteCarloOutput.append(outputOneRun)
        # find the best
        bestSample = scenarioMonteCarloOutput[0]
        for sample in range(0, len(scenarioMonteCarloOutput)):
            if scenarioMonteCarloOutput[sample].fval < bestSample.fval:
                bestSample = scenarioMonteCarloOutput[sample]
        # scale it to available budget, add the fixed costs and make it a dictionary
        bestSampleBudget = bestSample.budgetBest
        availableBudget = totalBudget - sum(asdArgs['fixedCosts'])
        bestSampleBudgetScaled = rescaleAllocation(availableBudget, bestSampleBudget)
        bestSampleBudgetScaled = map(add, bestSampleBudgetScaled, asdArgs['fixedCosts'])
        bestSampleBudgetScaledDict = {}
        for i in range(0, len(interventionList)):
            intervention = interventionList[i]
            bestSampleBudgetScaledDict[intervention] = bestSampleBudgetScaled[i]
        # put it in a filex
        outfile = open(filename, 'wb')
        pickle.dump(bestSampleBudgetScaledDict, outfile)
        outfile.close()

    def getTargetPopSizeFromModelInstance(self, model):
        targetPopSize = {}
        keyList = self.helper.keyList
        for intervention in self.data.interventionCompleteList:
            targetPopSize[intervention] = 0.
            # children
            numAgeGroups = len(keyList['ages'])
            for iAge in range(numAgeGroups):
                ageName = keyList['ages'][iAge]
                if "IFAS" in intervention:
                    target = 0.
                else:
                    target = self.data.targetPopulation[intervention][ageName]
                targetPopSize[intervention] += target * model.listOfAgeCompartments[iAge].getTotalPopulation()
            # pregnant women
            numAgeGroups = len(keyList['pregnantWomenAges'])
            for iAge in range(numAgeGroups):
                ageName = keyList['pregnantWomenAges'][iAge]
                if "IFAS" in intervention:
                    target = 0.
                else:
                    target = self.data.targetPopulation[intervention][ageName]
                targetPopSize[intervention] += target * model.listOfPregnantWomenAgeCompartments[
                    iAge].getTotalPopulation()
            # women of reproductive age
            numAgeGroups = len(keyList['reproductiveAges'])
            for iAge in range(numAgeGroups):
                ageName = keyList['reproductiveAges'][iAge]
                if "IFAS" in intervention:
                    target = 0.
                else:
                    target = self.data.targetPopulation[intervention][ageName]
                targetPopSize[intervention] += target * model.listOfReproductiveAgeCompartments[
                    iAge].getTotalPopulation()
            # for food fortification set target population size as entire population
            if "fortification" in intervention:
                targetPopSize[intervention] = self.data.demographics['total population']
        # get IFAS target populations seperately
        fromModel = True
        targetPopSize.update(self.helper.setIFASTargetPopWRA(self.data, model, fromModel))
        return targetPopSize

    def runOnceDumpFullOutputToFile(self, MCSampleSize, xmin, args, interventionList, totalBudget, filename):        
        # Ruth wrote this function to aid in creating data for the Health Hack weekend        
        import asd as asd 
        import numpy as np
        from operator import add
        import csv
        numInterventions = len(interventionList)
        scaledOutputX = []
        fvalVector = []
        availableBudget = totalBudget - sum(args['fixedCosts'])
        for r in range(0, MCSampleSize):
            proposalAllocation = np.random.rand(numInterventions)
            budgetBest, fval, exitflag, output = asd.asd(objectiveFunction, proposalAllocation, args, xmin = xmin, verbose = 0) 
            # add each of the samples to the big vectors   
            for sample in range(len(output.fval)):
                scaledBudget = rescaleAllocation(availableBudget, output.x[sample])
                scaledBudget = map(add, scaledBudget, args['fixedCosts']) 
                scaledOutputX.append(scaledBudget)
                fvalVector.append(output.fval[sample])   
        # output samples to csv     
        outfilename = '%s.csv'%(filename)
        header = ['fval'] + interventionList
        rows = []
        for sample in range(len(fvalVector)):
            valArray = [fvalVector[sample]] + scaledOutputX[sample]
            rows.append(valArray)
        with open(outfilename, "wb") as f:
                writer = csv.writer(f)
                writer.writerow(header)
                writer.writerows(rows)
        
    def getInitialAllocationDictionary(self):
        costCoverageInfo = self.getCostCoverageInfo()
        targetPopSize = self.getInitialTargetPopSize()        
        initialAllocation = getTotalInitialAllocation(self.data, costCoverageInfo, targetPopSize)
        initialAllocationDictionary = {}
        for i in range(0, len(self.data.interventionList)):
            intervention = self.data.interventionList[i]
            initialAllocationDictionary[intervention] = initialAllocation[i]
        return initialAllocationDictionary 
        
    def getTotalInitialBudget(self):
        costCoverageInfo = self.getCostCoverageInfo()
        targetPopSize = self.getInitialTargetPopSize()        
        initialAllocation = getTotalInitialAllocation(self.data, costCoverageInfo, targetPopSize)
        return sum(initialAllocation)

    def generateCostCurves(self, model, resultsFileStem=None,
                           budget=None, cascade=None, scale=True):
        '''Generates & stores cost curves in dictionary by intervention.'''
        import costcov
        costCov = costcov.Costcov()
        targetPopSize = self.getTargetPopSizeFromModelInstance(model)
        costCurvesDict = {}
        for intervention in self.data.interventionList:
            costCurvesDict[intervention] = costCov.getCostCoverageCurve(self.costCoverageInfo[intervention],
                                                                        targetPopSize[intervention], self.costCurveType,
                                                                        intervention)
        if resultsFileStem is not None:  # save plot
            costCov.saveCurvesToPNG(costCurvesDict, self.costCurveType, self.data.interventionList, targetPopSize, resultsFileStem,
                                    budget, cascade, scale=scale)
        return costCurvesDict
        
        
    def oneModelRunWithOutput(self, allocationDictionary):
        model, modelList = runModelForNTimeSteps(self.timeStepsPre, self.data, model=None, saveEachStep=True)
        newCoverages = self.getCoverages(allocationDictionary)
        model.updateCoverages(newCoverages)
        steps = self.numModelSteps - self.timeStepsPre
        modelList += runModelForNTimeSteps(steps, self.data, model, saveEachStep=True)[1]
        return modelList
    
        
    def getCostCoverageInfo(self):
        from copy import deepcopy as dcp
        costCoverageInfo = {}
        for intervention in self.data.interventionList:
            costCoverageInfo[intervention] = {}
            costCoverageInfo[intervention]['unitcost']   = dcp(self.data.costSaturation[intervention]["unit cost"])
            costCoverageInfo[intervention]['saturation'] = dcp(self.data.costSaturation[intervention]["saturation coverage"])
        return costCoverageInfo
        
    def getInitialTargetPopSize(self):
        import helper
        thisHelper = helper.Helper()
        targetPopSize = {}
        for intervention in self.data.interventionCompleteList:
            targetPopSize[intervention] = 0.
            # children
            agePopSizes  = self.helper.makeAgePopSizes(self.data)
            numAgeGroups = len(self.helper.keyList['ages'])
            for iAge in range(numAgeGroups):
                ageName = self.helper.keyList['ages'][iAge]
                if "IFAS" in intervention:
                    target = 0.
                else:    
                    target = self.data.targetPopulation[intervention][ageName]
                targetPopSize[intervention] += target * agePopSizes[iAge]
            # pregnant women
            agePopSizes = self.helper.makePregnantWomenAgePopSizes(self.data)
            numAgeGroups = len(self.helper.keyList['pregnantWomenAges'])    
            for iAge in range(numAgeGroups):
                ageName = self.helper.keyList['pregnantWomenAges'][iAge] 
                if "IFAS" in intervention:
                    target = 0.
                else:    
                    target = self.data.targetPopulation[intervention][ageName]
                targetPopSize[intervention] += target * agePopSizes[iAge]
            # women of reproductive age
            agePopSizes = self.helper.makeWRAAgePopSizes(self.data)
            numAgeGroups = len(self.helper.keyList['reproductiveAges'])    
            for iAge in range(numAgeGroups):
                ageName = self.helper.keyList['reproductiveAges'][iAge] 
                if "IFAS" in intervention:
                    target = 0.
                else:
                    target = self.data.targetPopulation[intervention][ageName]
                targetPopSize[intervention] += target * agePopSizes[iAge]
            # for food fortification set target population size as entire population
            if "fortification" in intervention:
               targetPopSize[intervention] =  self.data.demographics['total population']
        #add IFAS intervention target pop sizes to dictionary  
        fromModel = False       
        targetPopSize.update(thisHelper.setIFASTargetPopWRA(self.data, "dummyModel", fromModel))
        return targetPopSize    
    
    
    def generateBOCVectors(self, regionNameList, cascadeValues, outcome):
        import pickle
        costCoverageInfo = self.getCostCoverageInfo()
        targetPopSize = self.getInitialTargetPopSize()
        initialAllocation = getTotalInitialAllocation(self.data, costCoverageInfo, targetPopSize)
        currentTotalBudget = sum(initialAllocation)            
        spendingVector = []        
        outcomeVector = []
        for cascade in cascadeValues:
            spendingVector.append(cascade * currentTotalBudget)
            filename = self.resultsFileStem + '_cascade_' + str(self.optimise) + '_' + str(cascade)+'.pkl'
            infile = open(filename, 'rb')
            thisAllocation = pickle.load(infile)
            infile.close()
            modelOutput = self.oneModelRunWithOutput(thisAllocation)
            outcomeVector.append(modelOutput[self.numModelSteps-1].getOutcome(outcome))
        return spendingVector, outcomeVector    
        
    def plotReallocation(self):
        from plotting import plotallocations 
        import pickle
        baselineAllocation = self.getInitialAllocationDictionary()
        filename = '%s_cascade_%s_1.0.pkl'%(self.resultsFileStem, self.optimise)
        infile = open(filename, 'rb')
        optimisedAllocation = pickle.load(infile)
        infile.close()
        # plot
        plotallocations(baselineAllocation,optimisedAllocation)    
        
    def getTimeSeries(self, outcomeOfInterest):
        import pickle
        from copy import deepcopy as dcp
        allocation = {}
        # Baseline
        allocation['baseline'] = self.getInitialAllocationDictionary()
        # read the optimal budget allocations from file
        filename = '%s_cascade_%s_1.0.pkl'%(self.resultsFileStem, self.optimise)
        infile = open(filename, 'rb')
        allocation[self.optimise] = pickle.load(infile)
        infile.close()
        scenarios = ['baseline', dcp(self.optimise)]
        # run models and save output 
        print "performing model runs to generate time series..."
        modelRun = {}
        for scenario in scenarios:
            modelRun[scenario] = self.oneModelRunWithOutput(allocation[scenario])
        # get y axis
        objective = {}    
        objectiveYearly = {}
        for scenario in scenarios:
            objective[scenario] = []
            objective[scenario].append(modelRun[scenario][0].getOutcome(outcomeOfInterest))
            for i in range(1, self.numModelSteps):
                difference = modelRun[scenario][i].getOutcome(outcomeOfInterest) - modelRun[scenario][i-1].getOutcome(outcomeOfInterest)
                objective[scenario].append(difference)
            # make it yearly
            numYears = self.numModelSteps/12
            objectiveYearly[scenario] = []
            for i in range(0, numYears):
                step = i*12
                objectiveYearly[scenario].append( sum(objective[scenario][step:12+step]) )
        years = range(2016, 2016 + numYears)
        self.timeSeries = {'years':years, 'objectiveYearly':objectiveYearly}
    
    def plotTimeSeries(self, outcomeOfInterest):
        from plotting import plotTimeSeries
        if self.timeSeries == None:
            self.getTimeSeries(outcomeOfInterest)
        title = self.optimise
        plotTimeSeries(self.timeSeries['years'], self.timeSeries['objectiveYearly']['baseline'], self.timeSeries['objectiveYearly'][self.optimise], title)

    def outputTimeSeriesToCSV(self, outcomeOfInterest):
        import csv
        # WARNING: MAKE A NEW Optimisation CLASS OBJECT FOR EACH outcomeOfInterest
        if self.timeSeries == None:
            self.getTimeSeries(outcomeOfInterest)   
        years = self.timeSeries['years']
        objectiveYearly = self.timeSeries['objectiveYearly']
        # write time series to csv    
        headings = ['Year', outcomeOfInterest+" (baseline)", outcomeOfInterest+" (min "+self.optimise+")"]
        rows = []
        for i in range(len(years)):
            year = years[i]
            valarray = [year, objectiveYearly['baseline'][i], objectiveYearly[self.optimise][i]]
            rows.append(valarray)
        rows.sort()                
        outfilename = '%s_annual_timeseries_%s_min_%s.csv'%(self.resultsFileStem, outcomeOfInterest, self.optimise)
        with open(outfilename, "wb") as f:
            writer = csv.writer(f)
            writer.writerow(headings)
            writer.writerows(rows)   
            
    def outputCascadeAndOutcomeToCSV(self, cascadeValues, outcomeOfInterest): # TODO: need to fix this, but maybe should start with 0.0 as the baseline value
            import csv
            import pickle
            from copy import deepcopy as dcp
            cascadeData = {}
            outcome = {}
            thisCascade = dcp(cascadeValues)
            for multiple in thisCascade:
                filename = '%s_cascade_%s_%s.pkl'%(self.resultsFileStem, self.optimise, str(multiple))
                infile = open(filename, 'rb')
                allocation = pickle.load(infile)
                cascadeData[multiple] = allocation
                infile.close()
                modelOutput = self.oneModelRunWithOutput(allocation)
                outcome[multiple] = modelOutput[self.numModelSteps-1].getOutcome(outcomeOfInterest)
            # write the cascade csv
            prognames = returnAlphabeticalDictionary(cascadeData[cascadeValues[0]]).keys()            
            prognames.insert(0, 'Multiple of current budget')
            rows = []
            for i in range(len(thisCascade)):
                allocationDict = cascadeData[cascadeValues[i]]                
                allocationDict = returnAlphabeticalDictionary(allocationDict)
                valarray = allocationDict.values()
                valarray.insert(0, thisCascade[i])
                rows.append(valarray)
            rows.sort()                
            outfilename = '%s_cascade_min_%s.csv'%(self.resultsFileStem, self.optimise)
            with open(outfilename, "wb") as f: # TODO: THIS WRITEs THE BUDGET CASCADE with allocations
                writer = csv.writer(f)
                writer.writerow(prognames)
                writer.writerows(rows)
            # write the outcome csv    
            headings = ['Multiple of current budget', outcomeOfInterest+" (min "+self.optimise+")"]
            rows = []
            for i in range(len(thisCascade)):
                multiple = thisCascade[i]
                valarray = [multiple, outcome[multiple]]
                rows.append(valarray)
            rows.sort()                
            outfilename = '%s_cascade_%s_outcome_min_%s.csv'%(self.resultsFileStem, outcomeOfInterest, self.optimise)
            with open(outfilename, "wb") as f:
                writer = csv.writer(f)
                writer.writerow(headings)
                writer.writerows(rows)
                
    def outputCurrentSpendingToCSV(self):
        import csv
        currentSpending = self.getInitialAllocationDictionary()
        currentSpending = returnAlphabeticalDictionary(currentSpending)
        for objective in self.objectivesList:
            outfilename = '%s_current_spending.csv'%(self.resultsFileStem[objective]) # TODO: change this for dictionary
            with open(outfilename, "wb") as f:
                    writer = csv.writer(f)
                    writer.writerow(currentSpending.keys())
                    writer.writerow(currentSpending.values())
             




class GeospatialOptimisation:
    def __init__(self, regionSpreadsheetList, regionNameList, numModelSteps, cascadeValues, optimise, resultsFileStem, costCurveType):
        self.regionSpreadsheetList = regionSpreadsheetList
        self.regionNameList = regionNameList
        self.numModelSteps = numModelSteps
        self.cascadeValues = cascadeValues
        self.optimise = optimise
        self.resultsFileStem = resultsFileStem
        self.costCurveType = costCurveType
        self.numRegions = len(regionSpreadsheetList)        
        self.regionalBOCs = None 
        self.tradeOffCurves = None
        self.postGATimeSeries = None
        # check that results directory exists and if not then create it
        import os
        if not os.path.exists(resultsFileStem):
            os.makedirs(resultsFileStem)        
        
    def generateAllRegionsBOC(self):
        print 'reading files to generate regional BOCs..'
        import optimisation
        import math
        from copy import deepcopy as dcp
        regionalBOCs = {}
        regionalBOCs['spending'] = []
        regionalBOCs['outcome'] = [] 
        totalNationalBudget = self.getTotalNationalBudget()
        for region in range(0, self.numRegions):
            print 'generating BOC for region: ', self.regionNameList[region]
            thisSpreadsheet = self.regionSpreadsheetList[region]
            filename = self.resultsFileStem + self.regionNameList[region]
            thisOptimisation = optimisation.Optimisation(thisSpreadsheet, self.numModelSteps, self.optimise, filename, 'dummyCostCurve')
            # if final cascade value is 'extreme' replace it with value we used to generate .pkl file
            thisCascade = dcp(self.cascadeValues)            
            if self.cascadeValues[-1] == 'extreme':
                regionalTotalBudget = thisOptimisation.getTotalInitialBudget()
                thisCascade[-1] = math.ceil(totalNationalBudget / regionalTotalBudget)            
            spending, outcome = thisOptimisation.generateBOCVectors(self.regionNameList, thisCascade, self.optimise)            
            regionalBOCs['spending'].append(spending)
            regionalBOCs['outcome'].append(outcome)
        print 'finished generating regional BOCs from files'    
        self.regionalBOCs = regionalBOCs    
        
    def outputRegionalBOCsFile(self, filename):
        import pickle 
        # if BOCs not generated, generate them
        if self.regionalBOCs == None:
            self.generateAllRegionsBOC()
        regionalBOCsReformat = {}
        for region in range(0, self.numRegions):
            regionName = self.regionNameList[region]
            regionalBOCsReformat[regionName] = {}
            for key in ['spending', 'outcome']:
                regionalBOCsReformat[regionName][key] = self.regionalBOCs[key][region]
        outfile = open(filename, 'wb')
        pickle.dump(regionalBOCsReformat, outfile)
        outfile.close()         
        
    def outputTradeOffCurves(self):
        #import pickle
        import csv
        if self.tradeOffCurves == None:
            self.getTradeOffCurves()
        #outfile = open(filename, 'wb')
        #pickle.dump(self.tradeOffCurves, outfile)
        #outfile.close()  
        outfilename = '%strade_off_curves.csv'%(self.resultsFileStem)    
        with open(outfilename, "wb") as f:        
            writer = csv.writer(f)            
            for region in range(self.numRegions):
                regionName = self.regionNameList[region]
                row1 = ['spending'] + self.tradeOffCurves[regionName]['spending']
                row2 = ['outcome'] + self.tradeOffCurves[regionName]['outcome']
                writer.writerow([regionName])
                writer.writerow(row1)
                writer.writerow(row2)
        
    def getTradeOffCurves(self):
        # if BOCs not generated, generate them
        if self.regionalBOCs == None:
            self.generateAllRegionsBOC()
        # get index for cascade value of 1.0
        i = 0
        for value in self.cascadeValues:
            if (value == 1.0):
                index = i
            i += 1    
        tradeOffCurves = {}
        for region in range(0, self.numRegions):
            regionName = self.regionNameList[region]
            currentSpending = self.regionalBOCs['spending'][region][index]
            currentOutcome = self.regionalBOCs['outcome'][region][index]
            tradeOffCurves[regionName] = {}
            spendDifference = []
            outcomeAverted = []            
            for i in range(len(self.cascadeValues)):
                spendDifference.append( self.regionalBOCs['spending'][region][i] - currentSpending )
                if self.optimise == 'thrive':
                    outcomeAverted.append( self.regionalBOCs['outcome'][region][i] - currentOutcome )
                else:
                    outcomeAverted.append( currentOutcome - self.regionalBOCs['outcome'][region][i]  )
            tradeOffCurves[regionName]['spending'] = spendDifference
            tradeOffCurves[regionName]['outcome'] = outcomeAverted
        self.tradeOffCurves = tradeOffCurves    
    
    def plotTradeOffCurves(self):
        import plotting
        self.getTradeOffCurves()
        plotting.plotTradeOffCurves(self.tradeOffCurves, self.regionNameList, self.optimise)     

    
    def plotRegionalBOCs(self):
        import plotting
        plotting.plotRegionalBOCs(self.regionalBOCs, self.regionNameList, self.optimise)
        
    def getTotalNationalBudget(self):
        import optimisation
        regionalBudgets = []
        for region in range(0, self.numRegions):
            thisSpreadsheet = self.regionSpreadsheetList[region]
            thisOptimisation = optimisation.Optimisation(thisSpreadsheet, self.numModelSteps, self.optimise, 'dummyFileName', 'dummyCostCurve')        
            regionTotalBudget = thisOptimisation.getTotalInitialBudget()
            regionalBudgets.append(regionTotalBudget)
        nationalTotalBudget = sum(regionalBudgets)
        return nationalTotalBudget
        
    def getCurrentRegionalBudgets(self):
        import optimisation
        regionalBudgets = []
        for region in range(0, self.numRegions):
            thisSpreadsheet = self.regionSpreadsheetList[region]
            thisOptimisation = optimisation.Optimisation(thisSpreadsheet, self.numModelSteps, self.optimise, 'dummyFileName', 'dummyCurve')        
            regionTotalBudget = thisOptimisation.getTotalInitialBudget()
            regionalBudgets.append(regionTotalBudget)
        return regionalBudgets    
    

    def generateResultsForGeospatialCascades(self, MCSampleSize):
        import optimisation  
        import math
        from copy import deepcopy as dcp
        totalNationalBudget = self.getTotalNationalBudget()
        for region in range(0, self.numRegions):
            regionName = self.regionNameList[region]
            spreadsheet = self.regionSpreadsheetList[region]
            filename = self.resultsFileStem + regionName
            thisOptimisation = optimisation.Optimisation(spreadsheet, self.numModelSteps, self.optimise, filename)
            thisCascade = dcp(self.cascadeValues)
            # if final cascade value is 'extreme' replace it with totalNationalBudget / current regional total budget
            if self.cascadeValues[-1] == 'extreme':
                regionalTotalBudget = thisOptimisation.getTotalInitialBudget()
                thisCascade[-1] = math.ceil(totalNationalBudget / regionalTotalBudget) # this becomes a file name so keep it as an integer
            thisOptimisation.performCascadeOptimisation(MCSampleSize, thisCascade)
            
    def generateParallelResultsForGeospatialCascades(self, numCores, MCSampleSize, haveFixedProgCosts, splitCascade):
        import optimisation  
        import math
        from copy import deepcopy as dcp
        from multiprocessing import Process
        numParallelCombinations = len(self.cascadeValues) * self.numRegions
        #  assume 1 core per combination and then
        # check that you've said you have enough and don't parallelise if you don't
        if numCores < numParallelCombinations:
            print "num cores is not enough"
        else:   
            totalNationalBudget = self.getTotalNationalBudget()
            for region in range(0, self.numRegions):
                regionName = self.regionNameList[region]
                spreadsheet = self.regionSpreadsheetList[region]
                filename = self.resultsFileStem + regionName
                thisOptimisation = optimisation.Optimisation(spreadsheet, self.numModelSteps, self.optimise, filename, self.costCurveType)
                subNumCores = len(self.cascadeValues)
                thisCascade = dcp(self.cascadeValues)
                # if final cascade value is 'extreme' replace it with totalNationalBudget / current regional total budget
                if self.cascadeValues[-1] == 'extreme':
                    regionalTotalBudget = thisOptimisation.getTotalInitialBudget()
                    thisCascade[-1] = math.ceil(totalNationalBudget / regionalTotalBudget) # this becomes a file name so keep it as an integer
                if splitCascade:    
                    thisOptimisation.performParallelCascadeOptimisation(MCSampleSize, thisCascade, subNumCores, haveFixedProgCosts)  
                else:
                    prc = Process(target=thisOptimisation.performCascadeOptimisation, args=(MCSampleSize, thisCascade, haveFixedProgCosts))
                    prc.start()
                
                

    def getOptimisedRegionalBudgetList(self, geoMCSampleSize):
        import asd
        import numpy as np
        xmin = [0.] * self.numRegions
        # if BOCs not generated, generate them
        if self.regionalBOCs == None:
            self.generateAllRegionsBOC()
        totalBudget = self.getTotalNationalBudget()
        scenarioMonteCarloOutput = []
        for r in range(0, geoMCSampleSize):
            proposalSpendingList = np.random.rand(self.numRegions)
            args = {'regionalBOCs':self.regionalBOCs, 'totalBudget':totalBudget, 'optimise':self.optimise}
            budgetBest, fval, exitflag, output = asd.asd(geospatialObjectiveFunction, proposalSpendingList, args, xmin = xmin, verbose = 2)  
            outputOneRun = OutputClass(budgetBest, fval, exitflag, output.iterations, output.funcCount, output.fval, output.x)        
            scenarioMonteCarloOutput.append(outputOneRun)         
        # find the best
        bestSample = scenarioMonteCarloOutput[0]
        for sample in range(0, len(scenarioMonteCarloOutput)):
            if scenarioMonteCarloOutput[sample].fval < bestSample.fval:
                bestSample = scenarioMonteCarloOutput[sample]
        bestSampleScaled = rescaleAllocation(totalBudget, bestSample.budgetBest)        
        optimisedRegionalBudgetList = bestSampleScaled  
        return optimisedRegionalBudgetList
        
    def getOptimisedRegionalBudgetListExtraMoney(self, geoMCSampleSize, extraMoney):
        import asd
        import numpy as np
        from operator import add
        xmin = [0.] * self.numRegions
        # if BOCs not generated, generate them
        if self.regionalBOCs == None:
            self.generateAllRegionsBOC()
        currentRegionalSpendingList = self.getCurrentRegionalBudgets()
        scenarioMonteCarloOutput = []
        for r in range(0, geoMCSampleSize):
            proposalSpendingList = np.random.rand(self.numRegions)
            args = {'regionalBOCs':self.regionalBOCs, 'currentRegionalSpendingList':currentRegionalSpendingList, 'extraMoney':extraMoney, 'optimise':self.optimise}
            budgetBest, fval, exitflag, output = asd.asd(geospatialObjectiveFunctionExtraMoney, proposalSpendingList, args, xmin = xmin, verbose = 2)  
            outputOneRun = OutputClass(budgetBest, fval, exitflag, output.iterations, output.funcCount, output.fval, output.x)        
            scenarioMonteCarloOutput.append(outputOneRun)         
        # find the best
        bestSample = scenarioMonteCarloOutput[0]
        for sample in range(0, len(scenarioMonteCarloOutput)):
            if scenarioMonteCarloOutput[sample].fval < bestSample.fval:
                bestSample = scenarioMonteCarloOutput[sample]
        bestSampleScaled = rescaleAllocation(extraMoney, bestSample.budgetBest) 
        # to get the total optimised regional budgets add the optimised allocation of the extra money to the regional baseline amounts
        optimisedRegionalBudgetList = map(add, bestSampleScaled, currentRegionalSpendingList)
        return optimisedRegionalBudgetList    
        
    def performGeospatialOptimisation(self, geoMCSampleSize, MCSampleSize, GAFile, haveFixedProgCosts):
        import optimisation  
        print 'beginning geospatial optimisation..'
        optimisedRegionalBudgetList = self.getOptimisedRegionalBudgetList(geoMCSampleSize)
        print 'finished geospatial optimisation'
        for region in range(0, self.numRegions):
            regionName = self.regionNameList[region]
            print 'optimising for individual region ', regionName
            thisSpreadsheet = self.regionSpreadsheetList[region]
            thisOptimisation = optimisation.Optimisation(thisSpreadsheet, self.numModelSteps, self.optimise, self.resultsFileStem, self.costCurveType) 
            thisBudget = optimisedRegionalBudgetList[region]
            thisOptimisation.performSingleOptimisationForGivenTotalBudget(MCSampleSize, thisBudget, GAFile+'_'+regionName, haveFixedProgCosts)
            
    def performParallelGeospatialOptimisation(self, geoMCSampleSize, MCSampleSize, GAFile, numCores, haveFixedProgCosts):
        import optimisation  
        from multiprocessing import Process
        print 'beginning geospatial optimisation..'
        optimisedRegionalBudgetList = self.getOptimisedRegionalBudgetList(geoMCSampleSize)
        print 'finished geospatial optimisation'
        if self.numRegions >numCores:
            print "not enough cores to parallelise"
        else:
            for region in range(0, self.numRegions):
                regionName = self.regionNameList[region]
                print 'optimising for individual region ', regionName
                thisSpreadsheet = self.regionSpreadsheetList[region]
                thisOptimisation = optimisation.Optimisation(thisSpreadsheet, self.numModelSteps, self.optimise, self.resultsFileStem, self.costCurveType)
                thisBudget = optimisedRegionalBudgetList[region]
                prc = Process(
                    target=thisOptimisation.performSingleOptimisationForGivenTotalBudget, 
                    args=(MCSampleSize, thisBudget, GAFile+'_'+regionName, haveFixedProgCosts))
                prc.start()
            prc.join()    
                
    def performParallelGeospatialOptimisationExtraMoney(self, geoMCSampleSize, MCSampleSize, GAFile, numCores, extraMoney, haveFixedProgCosts):
        # this optimisation keeps current regional spending the same and optimises only additional spending across regions        
        import optimisation  
        from multiprocessing import Process
        print 'beginning geospatial optimisation..'
        optimisedRegionalBudgetList = self.getOptimisedRegionalBudgetListExtraMoney(geoMCSampleSize, extraMoney)
        print 'finished geospatial optimisation'
        if self.numRegions >numCores:
            print "not enough cores to parallelise"
        else:    
            for region in range(0, self.numRegions):
                regionName = self.regionNameList[region]
                print 'optimising for individual region ', regionName
                thisSpreadsheet = self.regionSpreadsheetList[region]
                thisOptimisation = optimisation.Optimisation(thisSpreadsheet, self.numModelSteps, self.optimise, self.resultsFileStem) 
                thisBudget = optimisedRegionalBudgetList[region]
                prc = Process(
                    target=thisOptimisation.performSingleOptimisationForGivenTotalBudget, 
                    args=(MCSampleSize, thisBudget, GAFile+'_'+regionName, haveFixedProgCosts))
                prc.start()    
            prc.join()    
        
    def plotReallocationByRegion(self):
        from plotting import plotallocations 
        import pickle
        import optimisation
        geospatialAllocations = {}
        for iReg in range(self.numRegions):
            regionName = self.regionNameList[iReg]
            print regionName
            thisOptimisation = optimisation.Optimisation(self.regionSpreadsheetList[iReg], self.numModelSteps, self.optimise, 'dummyFilename', self.costCurveType)
            geospatialAllocations[regionName] = {}
            geospatialAllocations[regionName]['baseline'] = thisOptimisation.getInitialAllocationDictionary()
            filename = '%s%s_cascade_%s_1.0.pkl'%(self.resultsFileStem, regionName, self.optimise)
            infile = open(filename, 'rb')
            allocation = pickle.load(infile)
            geospatialAllocations[regionName][self.optimise] = allocation
            infile.close()
            # plot
            plotallocations(geospatialAllocations[regionName]['baseline'],geospatialAllocations[regionName][self.optimise])
            
    def plotPostGAReallocationByRegion(self, GAFile):
        from plotting import plotallocations 
        import pickle
        import optimisation
        geospatialAllocations = {}
        for iReg in range(self.numRegions):
            regionName = self.regionNameList[iReg]
            print regionName
            thisOptimisation = optimisation.Optimisation(self.regionSpreadsheetList[iReg], self.numModelSteps, self.optimise, 'dummyFilename', self.costCurveType)
            geospatialAllocations[regionName] = {}
            geospatialAllocations[regionName]['baseline'] = thisOptimisation.getInitialAllocationDictionary()
            filename = '%s%s_%s.pkl'%(self.resultsFileStem, GAFile, regionName)
            infile = open(filename, 'rb')
            allocation = pickle.load(infile)
            geospatialAllocations[regionName][self.optimise] = allocation
            infile.close()
            # plot
            plotallocations(geospatialAllocations[regionName]['baseline'],geospatialAllocations[regionName][self.optimise])       
            
    def getTimeSeriesPostGAReallocationByRegion(self, GAFile):    
        import pickle
        import optimisation
        from copy import deepcopy as dcp
        self.postGATimeSeries = {}
        numYears = self.numModelSteps/12
        years = range(2016, 2016 + numYears)
        for region in range(len(self.regionSpreadsheetList)):
            regionName = self.regionNameList[region]
            spreadsheet = self.regionSpreadsheetList[region]
            allocation = {}
            thisOptimisation = optimisation.Optimisation(spreadsheet, self.numModelSteps, self.optimise, 'dummyFile')
            # Baseline
            allocation['baseline'] = thisOptimisation.getInitialAllocationDictionary()
            # read the optimal budget allocations from file
            filename = '%s%s_%s.pkl'%(self.resultsFileStem, GAFile, regionName)
            infile = open(filename, 'rb')
            allocation[self.optimise] = pickle.load(infile)
            infile.close()
            scenarios = ['baseline', dcp(self.optimise)]
            # run models and save output 
            print "performing model runs to generate time series..."
            modelRun = {}
            for scenario in scenarios:
                modelRun[scenario] = thisOptimisation.oneModelRunWithOutput(allocation[scenario])
            # get y axis
            objective = {}    
            objectiveYearly = {}
            for scenario in scenarios:
                objective[scenario] = []
                objective[scenario].append(modelRun[scenario][0].getOutcome(self.optimise))
                for i in range(1, self.numModelSteps):
                    difference = modelRun[scenario][i].getOutcome(self.optimise) - modelRun[scenario][i-1].getOutcome(self.optimise)
                    objective[scenario].append(difference)
                # make it yearly
                objectiveYearly[scenario] = []
                for i in range(0, numYears):
                    step = i*12
                    objectiveYearly[scenario].append( sum(objective[scenario][step:12+step]) )
            self.postGATimeSeries[regionName] = {'years':years, 'objectiveYearly':objectiveYearly}
            
    
    def plotTimeSeriesPostGAReallocationByRegion(self, GAFile):
        from plotting import plotTimeSeries
        if self.postGATimeSeries == None:
            self.getTimeSeriesPostGAReallocationByRegion(GAFile)
        for region in range(len(self.regionSpreadsheetList)):
            regionName = self.regionNameList[region]    
            title = regionName + '  ' + self.optimise
            plotTimeSeries(self.postGATimeSeries[regionName]['years'], self.postGATimeSeries[regionName]['objectiveYearly']['baseline'], self.postGATimeSeries[regionName]['objectiveYearly'][self.optimise], title)

    def outputToCSVTimeSeriesPostGAReallocationByRegion(self, GAFile):
        import csv
        if self.postGATimeSeries == None:
            self.getTimeSeriesPostGAReallocationByRegion(GAFile)   
        for region in range(len(self.regionSpreadsheetList)):
            regionName = self.regionNameList[region]            
            
            years = self.postGATimeSeries[regionName]['years']
            objectiveYearly = self.postGATimeSeries[regionName]['objectiveYearly']
            # write time series to csv    
            headings = ['Year', self.optimise+" (baseline)", self.optimise+" (min "+self.optimise+")"]
            rows = []
            for i in range(len(years)):
                year = years[i]
                valarray = [year, objectiveYearly['baseline'][i], objectiveYearly[self.optimise][i]]
                rows.append(valarray)
            rows.sort()                
            outfilename = '%s%s_annual_timeseries_postGA_%s_min_%s.csv'%(self.resultsFileStem, regionName, self.optimise, self.optimise)
            with open(outfilename, "wb") as f:
                writer = csv.writer(f)
                writer.writerow(headings)
                writer.writerows(rows)           
        
        
    def outputRegionalCascadesAndOutcomeToCSV(self, outcomeOfInterest):
        from copy import deepcopy as dcp
        import math
        import optimisation
        totalNationalBudget = self.getTotalNationalBudget()
        for region in range(self.numRegions):
            regionName = self.regionNameList[region]
            print regionName
            thisSpreadsheet = self.regionSpreadsheetList[region]
            filename = self.resultsFileStem+regionName
            thisOptimisation = optimisation.Optimisation(thisSpreadsheet, self.numModelSteps, self.optimise, filename, self.costCurveType) 
            thisCascade = dcp(self.cascadeValues)      
            # if final cascade value is 'extreme' replace it with value we used to generate .pkl file
            if self.cascadeValues[-1] == 'extreme':
                regionalTotalBudget = thisOptimisation.getTotalInitialBudget()
                thisCascade[-1] = math.ceil(totalNationalBudget / regionalTotalBudget)            
            thisOptimisation.outputCascadeAndOutcomeToCSV(thisCascade, outcomeOfInterest)
        
    def outputRegionalCurrentSpendingToCSV(self):
        import optimisation
        for region in range(self.numRegions):
            regionName = self.regionNameList[region]
            thisSpreadsheet = self.regionSpreadsheetList[region]
            filename = self.resultsFileStem+regionName
            thisOptimisation = optimisation.Optimisation(thisSpreadsheet, self.numModelSteps, self.optimise, filename, self.costCurveType)    
            thisOptimisation.outputCurrentSpendingToCSV()
        
        
    def outputRegionalPostGAOptimisedSpendingToCSV(self, GAFile):
        import pickle
        import csv
        for iReg in range(self.numRegions):
            regionName = self.regionNameList[iReg]
            filename = '%s%s_%s.pkl'%(self.resultsFileStem, GAFile, regionName)
            infile = open(filename, 'rb')
            allocation = pickle.load(infile)
            infile.close()
            allocation = returnAlphabeticalDictionary(allocation)
            outfilename = '%s%s_optimised_spending.csv'%(self.resultsFileStem, regionName)
            with open(outfilename, "wb") as f:
                    writer = csv.writer(f)
                    writer.writerow(allocation.keys())
                    writer.writerow(allocation.values())  
                    
    def outputRegionalTimeSeriesToCSV(self, outcomeOfInterest):
        import optimisation
        for region in range(self.numRegions):
            regionName = self.regionNameList[region]
            thisSpreadsheet = self.regionSpreadsheetList[region]
            filename = self.resultsFileStem+regionName
            thisOptimisation = optimisation.Optimisation(thisSpreadsheet, self.numModelSteps, self.optimise, filename)   
            thisOptimisation.outputTimeSeriesToCSV(outcomeOfInterest)
                    

                   