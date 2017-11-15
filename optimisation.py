# -*- coding: utf-8 -*-
"""
Created on Wed Jun  8 13:58:29 2016

@author: ruth
"""

def tanzaniaConstraints(proposalSpendingList, totalBudget):
    import numpy as np
    numRegions = len(proposalSpendingList)
    newScaledSpendingList = [0] * numRegions
    regionIndexList1 = [6, 11, 7, 12, 17] # very low
    regionIndexList2 = [3, 26, 0, 10, 9, 23, 21, 24, 19, 1, 22]  # below $1m
    regionIndexList3 = [2, 4, 5, 8, 13, 14, 15, 16, 18, 20, 25, 27, 28, 29] #everything remaining
    # very low first $0-0.5m
    for region in regionIndexList1:
        newScaledSpendingList[region] = np.random.uniform(0.0, 500000)
    # now below $1m: ($0-2m)
    for region in regionIndexList2:
        newScaledSpendingList[region] = np.random.uniform(0.0, 2000000)
    # fill in the remaining regions 
    newTotalBudget = totalBudget - sum(newScaledSpendingList)    
    remainingRegions = len(regionIndexList3)
    unScaledList = np.random.rand(remainingRegions)
    scaledList = rescaleAllocation(newTotalBudget, unScaledList)
    i = 0
    for region in regionIndexList3:
        newScaledSpendingList[region] = scaledList[i]
        i += 1
    # don't need to unscale as scaleRatio will just be 1    
    return newScaledSpendingList    

def returnAlphabeticalDictionary(dictionary):
    from collections import OrderedDict
    dictionaryOrdered = OrderedDict([])
    order = sorted(dictionary)
    for i in range(0, len(dictionary)):
        dictionaryOrdered[order[i]] = dictionary[order[i]]    
    return dictionaryOrdered 

def getTotalInitialAllocation(data, costCoverageInfo, targetPopSize):
    import costcov
    from copy import deepcopy as dcp
    costCov = costcov.Costcov()
    allocation = []
    for intervention in data.interventionList:
        coverageFraction = dcp(data.coverage[intervention])
        coverageNumber = coverageFraction * targetPopSize[intervention]
        if coverageNumber == 0:
            spending = 0.
        else:
            spending = costCov.getSpending(coverageNumber, costCoverageInfo[intervention], targetPopSize[intervention])
        allocation.append(spending)
    return allocation

def rescaleAllocation(totalBudget, allocation):
    scaleRatio = totalBudget / sum(allocation)
    rescaledAllocation = [x * scaleRatio for x in allocation]
    return rescaledAllocation

def generateCostCurves(data, model, keyList, dataSpreadsheetName, costCoverageInfo, curveType, resultsFileStem=None, budget=None, cascade=None, scale=True):
    '''Generates & stores cost curves in dictionary by intervention.'''
    import costcov
    costCov = costcov.Costcov()
    targetPopSize = getTargetPopSizeFromModelInstance(dataSpreadsheetName, keyList, model)
    costCurvesDict = {}
    for i in range(0, len(data.interventionList)):
        intervention = data.interventionList[i]
        costCurvesDict[intervention] = costCov.getCostCoverageCurve(costCoverageInfo[intervention], targetPopSize[intervention], curveType, intervention)
    if resultsFileStem is not None: # save plot
        costCov.saveCurvesToPNG(costCurvesDict, curveType, data.interventionList, targetPopSize, resultsFileStem, budget, cascade, scale=scale)
    return costCurvesDict

def runModelForNTimeSteps(timesteps, spreadsheetData, model, saveEachStep=False):
    import helper
    from copy import deepcopy as dc
    helper = helper.Helper()
    modelList = []
    if model is None:   # instantiate a model
        model = helper.setupModelDerivedParameters(spreadsheetData)[0]
    # be careful when doing this for cascade- need deep copies
    thisModel = dc(model)    
    for step in range(timesteps):
        thisModel.moveOneTimeStep()
        if saveEachStep:
            modelThisTimeStep = dc(thisModel)
            modelList.append(modelThisTimeStep)
    return thisModel, modelList

def getTargetPopSizeFromModelInstance(dataSpreadsheetName, keyList, model):    
    import data 
    spreadsheetData = data.readSpreadsheet(dataSpreadsheetName, keyList)        
    numAgeGroups = len(keyList['ages'])
    targetPopSize = {}
    for intervention in spreadsheetData.interventionList:
        targetPopSize[intervention] = 0.
        for iAge in range(numAgeGroups):
            ageName = keyList['ages'][iAge]
            targetPopSize[intervention] += spreadsheetData.targetPopulation[intervention][ageName] * model.listOfAgeCompartments[iAge].getTotalPopulation()
        targetPopSize[intervention] += spreadsheetData.targetPopulation[intervention]['pregnant women'] * model.pregnantWomen.populationSize
    return targetPopSize    

    
def objectiveFunction(allocation, costCurves, model, totalBudget, fixedCosts, costCoverageInfo, optimise, numModelSteps, dataSpreadsheetName, data, timestepsPre):
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
    performanceMeasure = modelThisRun.getOutcome(optimise)
    if optimise == 'thrive':
        performanceMeasure = - performanceMeasure
    return performanceMeasure


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
    def __init__(self, dataSpreadsheetName, numModelSteps, optimise, resultsFileStem, costCurveType):
        import helper       
        self.dataSpreadsheetName = dataSpreadsheetName
        self.numModelSteps = numModelSteps
        self.optimise = optimise
        self.resultsFileStem = resultsFileStem
        self.costCurveType = costCurveType
        self.helper = helper.Helper()
        self.timeSeries = None
        # check that results directory exists and if not then create it
        import os
        if not os.path.exists(resultsFileStem):
            os.makedirs(resultsFileStem)
        
    def performSingleOptimisation(self, MCSampleSize, haveFixedProgCosts):
        import data 
        spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)        
        costCoverageInfo = self.getCostCoverageInfo()  
        initialTargetPopSize = self.getInitialTargetPopSize()
        initialAllocation = getTotalInitialAllocation(spreadsheetData, costCoverageInfo, initialTargetPopSize)
        totalBudget = sum(initialAllocation)
        xmin = [0.] * len(initialAllocation)
        #args = {'totalBudget':totalBudget, 'costCoverageInfo':costCoverageInfo, 'optimise':self.optimise, 'numModelSteps':self.numModelSteps, 'dataSpreadsheetName':self.dataSpreadsheetName, 'data':spreadsheetData}    
        # set up and run the model prior to optimising
        fixedCosts = self.getFixedCosts(haveFixedProgCosts, initialAllocation)
        timestepsPre = 12
        model = runModelForNTimeSteps(timestepsPre, spreadsheetData, model=None)[0]
        # generate cost curves for each intervention
        costCurves = generateCostCurves(spreadsheetData, model, self.helper.keyList, self.dataSpreadsheetName,
                                        costCoverageInfo, self.costCurveType)        
        args = {'costCurves': costCurves, 'model': model, 'timestepsPre': timestepsPre,
                'totalBudget': totalBudget, 'fixedCosts': fixedCosts, 'costCoverageInfo': costCoverageInfo,
                'optimise': self.optimise, 'numModelSteps': self.numModelSteps,
                'dataSpreadsheetName': self.dataSpreadsheetName, 'data': spreadsheetData}        
        self.runOnce(MCSampleSize, xmin, args, spreadsheetData.interventionList, totalBudget, self.resultsFileStem+'.pkl')
        
    def performSingleOptimisationForGivenTotalBudget(self, MCSampleSize, totalBudget, filename, haveFixedProgCosts):
        import data 
        spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)        
        costCoverageInfo = self.getCostCoverageInfo()  
        xmin = [0.] * len(spreadsheetData.interventionList)
        initialTargetPopSize = self.getInitialTargetPopSize() 
        initialAllocation = getTotalInitialAllocation(spreadsheetData, costCoverageInfo, initialTargetPopSize)
        fixedCosts = self.getFixedCosts(haveFixedProgCosts, initialAllocation)
        timestepsPre = 12
        # set up and run the model prior to optimising
        model = runModelForNTimeSteps(timestepsPre, spreadsheetData, model=None)[0]
        # generate cost curves for each intervention
        costCurves = generateCostCurves(spreadsheetData, model, self.helper.keyList, self.dataSpreadsheetName,
                                        costCoverageInfo, self.costCurveType)
        args = {'costCurves': costCurves, 'model': model, 'timestepsPre': timestepsPre,
                'totalBudget': totalBudget, 'fixedCosts': fixedCosts, 'costCoverageInfo': costCoverageInfo,
                'optimise': self.optimise, 'numModelSteps': self.numModelSteps,
                'dataSpreadsheetName': self.dataSpreadsheetName, 'data': spreadsheetData}
        self.runOnce(MCSampleSize, xmin, args, spreadsheetData.interventionList, totalBudget, self.resultsFileStem+filename+'.pkl')
        
    def performSingleOptimisationForGivenTotalBudgetIYCF(self, MCSampleSize, totalBudget, filename, haveFixedProgCosts, covIYCF):
        import data 
        spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)        
        costCoverageInfo = self.getCostCoverageInfo()  
        xmin = [0.] * len(spreadsheetData.interventionList)
        initialTargetPopSize = self.getInitialTargetPopSize() 
        initialAllocation = getTotalInitialAllocation(spreadsheetData, costCoverageInfo, initialTargetPopSize)
        fixedCosts = self.getFixedCosts(haveFixedProgCosts, initialAllocation)
        timestepsPre = 12
        # set up and run the model prior to optimising
        model = self.helper.setupModelDerivedParameters(spreadsheetData)[0]
        newCoverages = {'IYCF': covIYCF}
        model.updateCoverages(newCoverages)
        model = runModelForNTimeSteps(timestepsPre, spreadsheetData, model=model)[0]
        # generate cost curves for each intervention
        costCurves = generateCostCurves(spreadsheetData, model, self.helper.keyList, self.dataSpreadsheetName,
                                        costCoverageInfo, self.costCurveType)
        args = {'costCurves': costCurves, 'model': model, 'timestepsPre': timestepsPre,
                'totalBudget': totalBudget, 'fixedCosts': fixedCosts, 'costCoverageInfo': costCoverageInfo,
                'optimise': self.optimise, 'numModelSteps': self.numModelSteps,
                'dataSpreadsheetName': self.dataSpreadsheetName, 'data': spreadsheetData}
        self.runOnce(MCSampleSize, xmin, args, spreadsheetData.interventionList, totalBudget, self.resultsFileStem+filename+'.pkl')    

        
    def performCascadeOptimisation(self, MCSampleSize, cascadeValues, haveFixedProgCosts):
        import data
        spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)
        timestepsPre = 12
        costCoverageInfo = self.getCostCoverageInfo()
        initialTargetPopSize = self.getInitialTargetPopSize()
        initialAllocation = getTotalInitialAllocation(spreadsheetData, costCoverageInfo, initialTargetPopSize)
        currentTotalBudget = sum(initialAllocation)
        xmin = [0.] * len(initialAllocation)
        # set fixed costs if you have them
        fixedCosts = self.getFixedCosts(haveFixedProgCosts, initialAllocation)
        # run the model prior to optimising
        model = runModelForNTimeSteps(timestepsPre, spreadsheetData, model=None)[0]
        # generate cost curves for each intervention
        costCurves = generateCostCurves(spreadsheetData, model, self.helper.keyList, self.dataSpreadsheetName, costCoverageInfo,
                                        self.costCurveType)
        for cascade in cascadeValues:
            totalBudget = currentTotalBudget * cascade
            args = {'costCurves': costCurves, 'model': model, 'timestepsPre': timestepsPre,
                    'totalBudget':totalBudget, 'fixedCosts':fixedCosts, 'costCoverageInfo':costCoverageInfo,
                    'optimise':self.optimise, 'numModelSteps':self.numModelSteps,
                    'dataSpreadsheetName':self.dataSpreadsheetName, 'data':spreadsheetData}
            outFile = self.resultsFileStem+'_cascade_'+str(self.optimise)+'_'+str(cascade)+'.pkl'
            self.runOnce(MCSampleSize, xmin, args, spreadsheetData.interventionList, totalBudget, outFile)

    def cascadeParallelRunFunction(self, costCurves, model, timestepsPre, cascadeValue, currentTotalBudget, fixedCosts, spreadsheetData, costCoverageInfo, MCSampleSize, xmin):
        totalBudget = currentTotalBudget * cascadeValue
        args = {'costCurves': costCurves, 'model': model, 'timestepsPre': timestepsPre,
                'totalBudget': totalBudget, 'fixedCosts': fixedCosts, 'costCoverageInfo': costCoverageInfo,
                'optimise': self.optimise, 'numModelSteps': self.numModelSteps,
                'dataSpreadsheetName': self.dataSpreadsheetName, 'data': spreadsheetData}
        outFile = self.resultsFileStem+'_cascade_'+str(self.optimise)+'_'+str(cascadeValue)+'.pkl'
        self.runOnce(MCSampleSize, xmin, args, spreadsheetData.interventionList, totalBudget, outFile)

    def performParallelCascadeOptimisation(self, MCSampleSize, cascadeValues, numCores, haveFixedProgCosts):
        import data
        from multiprocessing import Process
        spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)
        costCoverageInfo = self.getCostCoverageInfo()
        initialTargetPopSize = self.getInitialTargetPopSize()
        initialAllocation = getTotalInitialAllocation(spreadsheetData, costCoverageInfo, initialTargetPopSize)
        currentTotalBudget = sum(initialAllocation)
        xmin = [0.] * len(initialAllocation)
        timestepsPre = 12
        # set fixed costs if you have them
        fixedCosts = self.getFixedCosts(haveFixedProgCosts, initialAllocation)
        # set up and run the model prior to optimising
        model = runModelForNTimeSteps(timestepsPre, spreadsheetData, model=None)[0]
        # generate cost curves for each intervention
        costCurves = generateCostCurves(spreadsheetData, model, self.helper.keyList, self.dataSpreadsheetName,
                                        costCoverageInfo, self.costCurveType)
        # check that you have enough cores and don't parallelise if you don't
        if numCores < len(cascadeValues):
            print "numCores is not enough"
        else:
            for value in cascadeValues:
                prc = Process(
                    target=self.cascadeParallelRunFunction,
                    args=(costCurves, model, timestepsPre, value, currentTotalBudget, fixedCosts, spreadsheetData,
                            costCoverageInfo, MCSampleSize, xmin))
                prc.start()
                
    def performParallelCascadeOptimisationCustomCoverage(self, MCSampleSize, cascadeValues, numCores, haveFixedProgCosts, customCoverage):
        # this function is for changing the coverages in the model from those in the spreadsheet
        # use this when you want derived calculated from spreadsheet values but then the model run from custom coverages
        import data
        from multiprocessing import Process
        spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)
        costCoverageInfo = self.getCostCoverageInfo()
        initialTargetPopSize = self.getInitialTargetPopSize()
        initialAllocation = getTotalInitialAllocation(spreadsheetData, costCoverageInfo, initialTargetPopSize)
        currentTotalBudget = sum(initialAllocation)
        xmin = [0.] * len(initialAllocation)
        timestepsPre = 12
        # set fixed costs if you have them
        fixedCosts = self.getFixedCosts(haveFixedProgCosts, initialAllocation)
        # set up and run the model prior to optimising
        model = self.helper.setupModelDerivedParameters(spreadsheetData)[0]
        model.updateCoverages(customCoverage)
        model = runModelForNTimeSteps(timestepsPre, spreadsheetData, model=model)[0]
        # generate cost curves for each intervention
        costCurves = generateCostCurves(spreadsheetData, model, self.helper.keyList, self.dataSpreadsheetName,
                                        costCoverageInfo, self.costCurveType)
        # check that you have enough cores and don't parallelise if you don't
        if numCores < len(cascadeValues):
            print "numCores is not enough"
        else:
            for value in cascadeValues:
                prc = Process(
                    target=self.cascadeParallelRunFunction,
                    args=(costCurves, model, timestepsPre, value, currentTotalBudget, fixedCosts, spreadsheetData,
                            costCoverageInfo, MCSampleSize, xmin))
                prc.start()            
        
    def performCascadeOptimisationCustomCoverageIYCF(self, MCSampleSize, cascadeValues, haveFixedProgCosts, customCoverageIYCF):
        import data
        spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)
        timestepsPre = 12
        costCoverageInfo = self.getCostCoverageInfo()
        initialTargetPopSize = self.getInitialTargetPopSize()
        initialAllocation = getTotalInitialAllocation(spreadsheetData, costCoverageInfo, initialTargetPopSize)
        currentTotalBudget = sum(initialAllocation)
        xmin = [0.] * len(initialAllocation)
        # set fixed costs if you have them
        fixedCosts = self.getFixedCosts(haveFixedProgCosts, initialAllocation)
        # set up and run the model prior to optimising
        model = self.helper.setupModelDerivedParameters(spreadsheetData)[0]
        model.updateCoverages(customCoverageIYCF)
        model = runModelForNTimeSteps(timestepsPre, spreadsheetData, model=model)[0]
        # generate cost curves for each intervention
        costCurves = generateCostCurves(spreadsheetData, model, self.helper.keyList, self.dataSpreadsheetName, costCoverageInfo,
                                        self.costCurveType)
        for cascade in cascadeValues:
            totalBudget = currentTotalBudget * cascade
            args = {'costCurves': costCurves, 'model': model, 'timestepsPre': timestepsPre,
                    'totalBudget':totalBudget, 'fixedCosts':fixedCosts, 'costCoverageInfo':costCoverageInfo,
                    'optimise':self.optimise, 'numModelSteps':self.numModelSteps,
                    'dataSpreadsheetName':self.dataSpreadsheetName, 'data':spreadsheetData}
            outFile = self.resultsFileStem+'_cascade_'+str(self.optimise)+'_'+str(cascade)+'.pkl'
            self.runOnce(MCSampleSize, xmin, args, spreadsheetData.interventionList, totalBudget, outFile)    
    
    def performParallelSampling(self, MCSampleSize, haveFixedProgCosts, numRuns, filename):
        import data 
        from multiprocessing import Process
        spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)        
        costCoverageInfo = self.getCostCoverageInfo()  
        initialTargetPopSize = self.getInitialTargetPopSize()          
        initialAllocation = getTotalInitialAllocation(spreadsheetData, costCoverageInfo, initialTargetPopSize)
        currentTotalBudget = sum(initialAllocation)
        xmin = [0.] * len(initialAllocation)
        # set fixed costs if you have them
        fixedCosts = self.getFixedCosts(haveFixedProgCosts, initialAllocation) 
        runOnceArgs = {'totalBudget':currentTotalBudget, 'fixedCosts':fixedCosts, 'costCoverageInfo':costCoverageInfo, 'optimise':self.optimise, 'numModelSteps':self.numModelSteps, 'dataSpreadsheetName':self.dataSpreadsheetName, 'data':spreadsheetData}
        for i in range(numRuns):
            prc = Process(
                target=self.runOnceDumpFullOutputToFile, 
                args=(MCSampleSize, xmin, runOnceArgs, spreadsheetData.interventionList, currentTotalBudget, filename+"_"+str(i)))
            prc.start()    

    def performParallelCascadeOptimisationAlteredInterventionEffectiveness(self, MCSampleSize, cascadeValues, numCores, haveFixedProgCosts, intervention, effectiveness, savePlot):
        import data
        from multiprocessing import Process
        spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)
        costCoverageInfo = self.getCostCoverageInfo()
        initialTargetPopSize = self.getInitialTargetPopSize()
        initialAllocation = getTotalInitialAllocation(spreadsheetData, costCoverageInfo, initialTargetPopSize)
        currentTotalBudget = sum(initialAllocation)
        xmin = [0.] * len(initialAllocation)
        timestepsPre = 12
        # set fixed costs if you have them
        fixedCosts = self.getFixedCosts(haveFixedProgCosts, initialAllocation)
        # alter mortality & incidence effectiveness
        for ageName in self.helper.keyList['ages']:
            spreadsheetData.effectivenessMortality[intervention][ageName]['Diarrhea'] *= effectiveness
            spreadsheetData.effectivenessIncidence[intervention][ageName]['Diarrhea'] *= effectiveness
        # set up and run the model prior to optimising
        model = runModelForNTimeSteps(timestepsPre, spreadsheetData, model=None)[0]
        # generate cost curves for each intervention
        if savePlot:
            resultsPath = self.resultsFileStem
        else:
            resultsPath = None
        costCurves = generateCostCurves(spreadsheetData, model, self.helper.keyList, self.dataSpreadsheetName,
                                        costCoverageInfo, self.costCurveType, resultsFileStem=resultsPath, budget=currentTotalBudget, cascade=cascadeValues)
        # check that you have enough cores and don't parallelise if you don't
        if numCores < len(cascadeValues):
            print "numCores is not enough"
        else:
            for value in cascadeValues:
                prc = Process(
                    target=self.cascadeParallelRunFunction,
                    args=(costCurves, model, timestepsPre, value, currentTotalBudget, fixedCosts, spreadsheetData,
                            costCoverageInfo, MCSampleSize, xmin))
                prc.start()
        
    def getFixedCosts(self, haveFixedProgCosts, initialAllocation):
        from copy import deepcopy as dcp
        if haveFixedProgCosts:
            fixedCosts = dcp(initialAllocation)
        else:
            fixedCosts = [0.] * len(initialAllocation)
        return fixedCosts    

    def runOnce(self, MCSampleSize, xmin, args, interventionList, totalBudget, filename):
        import asd as asd
        import pickle
        from numpy import random
        from operator import add
        numInterventions = len(interventionList)
        scenarioMonteCarloOutput = []
        for r in range(0, MCSampleSize):
            proposalAllocation = random.rand(numInterventions)
            budgetBest, fval, exitflag, output = asd.asd(objectiveFunction, proposalAllocation, args, xmin = xmin, verbose = 0)
            outputOneRun = OutputClass(budgetBest, fval, exitflag, output.iterations, output.funcCount, output.fval, output.x)
            scenarioMonteCarloOutput.append(outputOneRun)
        # find the best
        bestSample = scenarioMonteCarloOutput[0]
        for sample in range(0, len(scenarioMonteCarloOutput)):
            if scenarioMonteCarloOutput[sample].fval < bestSample.fval:
                bestSample = scenarioMonteCarloOutput[sample]
        # scale it to available budget, add the fixed costs and make it a dictionary
        bestSampleBudget = bestSample.budgetBest
        availableBudget = totalBudget - sum(args['fixedCosts'])
        bestSampleBudgetScaled = rescaleAllocation(availableBudget, bestSampleBudget)
        bestSampleBudgetScaled = map(add, bestSampleBudgetScaled, args['fixedCosts'])
        bestSampleBudgetScaledDict = {}
        for i in range(0, len(interventionList)):
            intervention = interventionList[i]
            bestSampleBudgetScaledDict[intervention] = bestSampleBudgetScaled[i]
        # put it in a file
        outfile = open(filename, 'wb')
        pickle.dump(bestSampleBudgetScaledDict, outfile)
        outfile.close()
        
    def runOnceDumpFullOutputToFile(self, MCSampleSize, xmin, args, interventionList, totalBudget, filename):        
        # Ruth wrote this function to aid in creating data for the Health Hack weekend        
        import asd as asd 
        from numpy import random
        from operator import add
        import csv
        numInterventions = len(interventionList)
        scaledOutputX = []
        fvalVector = []
        availableBudget = totalBudget - sum(args['fixedCosts'])
        for r in range(0, MCSampleSize):
            proposalAllocation = random.rand(numInterventions)
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
        import data 
        spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)        
        costCoverageInfo = self.getCostCoverageInfo()
        targetPopSize = self.getInitialTargetPopSize()        
        initialAllocation = getTotalInitialAllocation(spreadsheetData, costCoverageInfo, targetPopSize)        
        initialAllocationDictionary = {}
        for i in range(0, len(spreadsheetData.interventionList)):
            intervention = spreadsheetData.interventionList[i]
            initialAllocationDictionary[intervention] = initialAllocation[i]
        return initialAllocationDictionary 
        
    def getTotalInitialBudget(self, covIYCF = None):
        import data 
        spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)  
        if covIYCF is not None:        
            spreadsheetData.coverage['IYCF'] = covIYCF
        costCoverageInfo = self.getCostCoverageInfo()
        targetPopSize = self.getInitialTargetPopSize()        
        initialAllocation = getTotalInitialAllocation(spreadsheetData, costCoverageInfo, targetPopSize)        
        return sum(initialAllocation)     
        
    def oneModelRunWithOutput(self, allocationDictionary):
        import data
        from numpy import maximum
        eps = 1.e-3  ## WARNING: using project non-specific eps
        spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)
        costCoverageInfo = self.getCostCoverageInfo()
        timestepsPre = 12
        model, modelList = runModelForNTimeSteps(timestepsPre, spreadsheetData, model=None, saveEachStep=True)
        costCurves = generateCostCurves(spreadsheetData, model, self.helper.keyList, self.dataSpreadsheetName,
                                       costCoverageInfo, self.costCurveType)
        newCoverages = {}
        for i in range(0, len(spreadsheetData.interventionList)):
            intervention = spreadsheetData.interventionList[i]
            costCurveThisIntervention = costCurves[intervention]
            newCoverages[intervention] = maximum(costCurveThisIntervention(allocationDictionary[intervention]), eps)
        model.updateCoverages(newCoverages)
        steps = self.numModelSteps - timestepsPre
        modelList += runModelForNTimeSteps(steps, spreadsheetData, model, saveEachStep=True)[1]
        return modelList
        
    def oneModelRunWithOutputForFuture(self, allocationDictionary, model, spreadsheetData, costCurves, timestepsPre): # TODO: this is the way forward regarding this function for master (it is faster)
        from numpy import maximum
        eps = 1.e-3  ## WARNING: using project non-specific eps
        newCoverages = {}
        for intervention in spreadsheetData.interventionList:
            costCurveThisIntervention = costCurves[intervention]
            newCoverages[intervention] = maximum(costCurveThisIntervention(allocationDictionary[intervention]), eps)
        model.updateCoverages(newCoverages)
        steps = self.numModelSteps - timestepsPre
        lastmodelInstance = runModelForNTimeSteps(steps, spreadsheetData, model, saveEachStep=True)[0]
        return lastmodelInstance
        
    def oneModelRunWithOutputManuallyScaleIYCF(self, IYCF_cov):
        import data
        spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)
        model = self.helper.setupModelDerivedParameters(spreadsheetData)[0]
        newCoverages = {}        
        newCoverages['IYCF'] = IYCF_cov    
        model.updateCoverages(newCoverages)
        modelList = runModelForNTimeSteps(self.numModelSteps, spreadsheetData, model=model, saveEachStep=True)[1]
        return modelList    
        
        
    def oneModelRunWithOutputCustomCoverages(self, customCoverages):
        import data
        spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)
        model = self.helper.setupModelDerivedParameters(spreadsheetData)[0]        
        newCoverages = customCoverages    
        model.updateCoverages(newCoverages)
        modelList = runModelForNTimeSteps(self.numModelSteps, spreadsheetData, model=model, saveEachStep=True)[1]
        return modelList
        
    def oneModelRunWithOutputCustomOptimised(self, allocationDictionary, customCoverages):
        import data
        from numpy import maximum
        eps = 1.e-3  ## WARNING: using project non-specific eps
        timestepsPre = 12
        spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)
        model = self.helper.setupModelDerivedParameters(spreadsheetData)[0]
        newCoverages = customCoverages
        model.updateCoverages(newCoverages)
        modelList = runModelForNTimeSteps(timestepsPre, spreadsheetData, model=model, saveEachStep=True)[1]
        costCoverageInfo = self.getCostCoverageInfo()
        costCurves = generateCostCurves(spreadsheetData, model, self.helper.keyList, self.dataSpreadsheetName,
                                        costCoverageInfo, self.costCurveType)
        newCoverages = {}
        for i in range(0, len(spreadsheetData.interventionList)):
            intervention = spreadsheetData.interventionList[i]
            costCurveThisIntervention = costCurves[intervention]
            newCoverages[intervention] = maximum(costCurveThisIntervention(allocationDictionary[intervention]), eps)
        model.updateCoverages(newCoverages)
        steps = self.numModelSteps - timestepsPre
        modelList += runModelForNTimeSteps(steps, spreadsheetData, model, saveEachStep=True)[1]
        return modelList
        
        
    def getCostCoverageInfo(self):
        import data 
        from copy import deepcopy as dcp
        spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)        
        costCoverageInfo = {}
        for intervention in spreadsheetData.interventionList:
            costCoverageInfo[intervention] = {}
            costCoverageInfo[intervention]['unitcost']   = dcp(spreadsheetData.costSaturation[intervention]["unit cost"])
            costCoverageInfo[intervention]['saturation'] = dcp(spreadsheetData.costSaturation[intervention]["saturation coverage"])
        return costCoverageInfo
        
    def getInitialTargetPopSize(self):
        import data 
        spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)        
        mothers = self.helper.makePregnantWomen(spreadsheetData) 
        numAgeGroups = len(self.helper.keyList['ages'])
        agePopSizes  = self.helper.makeAgePopSizes(spreadsheetData)  
        targetPopSize = {}
        for intervention in spreadsheetData.interventionList:
            targetPopSize[intervention] = 0.
            for iAge in range(numAgeGroups):
                ageName = self.helper.keyList['ages'][iAge]
                targetPopSize[intervention] += spreadsheetData.targetPopulation[intervention][ageName] * agePopSizes[iAge]
            targetPopSize[intervention] += spreadsheetData.targetPopulation[intervention]['pregnant women'] * mothers.populationSize
        return targetPopSize    
    
    
    def generateBOCVectors(self, cascadeValues, outcome):
        #WARNING: HARD CODE: directly modified for Tanzania beline 1 - assumes spreadsheets included non-zero IYCF values        
        from copy import deepcopy as dcp
        import pickle
        import data
        from numpy import array
        spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)
        costCoverageInfo = self.getCostCoverageInfo()
        targetPopSize = self.getInitialTargetPopSize()
        initialAllocation = getTotalInitialAllocation(spreadsheetData, costCoverageInfo, targetPopSize) # TODO: may be able to remove these if saved as attribute
        currentTotalBudget = sum(initialAllocation)
        # get model instance and cost curves for this region
        timeStepsPre = 12
        # before model gets instantiated set coverage of IYCF to zero
        saveIYCF = dcp(spreadsheetData.coverage['IYCF'])
        spreadsheetData.coverage['IYCF'] = 0.0
        model = self.helper.setupModelDerivedParameters(spreadsheetData)[0]
        # now put the IYCF coverage back to what it was
        model.params.coverage['IYCF'] = saveIYCF
        model = runModelForNTimeSteps(timeStepsPre, spreadsheetData, model=model, saveEachStep=True)[0]
        costCurves = generateCostCurves(spreadsheetData, model, self.helper.keyList, self.dataSpreadsheetName,
                                        costCoverageInfo, self.costCurveType)
        spendingVector = []
        outcomeVector = []
        # get model outcome for each allocation
        for cascade in cascadeValues:
            thisModel = dcp(model)
            thisMultiple = cascade * currentTotalBudget
            spendingVector.append(thisMultiple)
            filename = self.resultsFileStem + '_cascade_' + str(self.optimise) + '_' + str(cascade)+'.pkl'
            infile = open(filename, 'rb')
            thisAllocation = pickle.load(infile)
            infile.close()
            modelThisAllocation = self.oneModelRunWithOutputForFuture(thisAllocation, thisModel, spreadsheetData,
                                                         costCurves, timeStepsPre)
            modelOutcome = modelThisAllocation.getOutcome(outcome)
            outcomeVector.append(modelOutcome)
        # order vectors and remove duplicates for pchip
        xyTuple = zip(spendingVector, outcomeVector)
        # remove duplicate tuples
        uniqueTuples = list(set(xyTuple))
        sortedTuples = sorted(uniqueTuples)
        xs = array([a for a, b in sortedTuples])
        ys = array([b for a, b in sortedTuples])
        spendingVector = dcp(xs)
        outcomeVector = dcp(ys)
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
            
    def outputCascadeAndOutcomeToCSV(self, cascadeValues, outcomeOfInterest, customCoverage = None):
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
                if customCoverage is None:
                    modelOutput = self.oneModelRunWithOutput(allocation)
                else:
                    # custom coverage is used to run for 12 months, then allocation is used to scale funding for remaining time steps
                    modelOutput = self.oneModelRunWithOutputCustomOptimised(allocation, customCoverage)
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
            with open(outfilename, "wb") as f:
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
        outfilename = '%s_current_spending.csv'%(self.resultsFileStem)
        with open(outfilename, "wb") as f:
                writer = csv.writer(f)
                writer.writerow(currentSpending.keys())
                writer.writerow(currentSpending.values())                
             

    def outputCostCurvesAsPNG(self, resultsFileStem, cascade, scale=True):
        import data
        spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)
        timestepsPre = 12
        costCoverageInfo = self.getCostCoverageInfo()
        # run the model 
        model = runModelForNTimeSteps(timestepsPre, spreadsheetData, model=None)[0]
        initialTargetPopSize = self.getInitialTargetPopSize()
        initialAllocation = getTotalInitialAllocation(spreadsheetData, costCoverageInfo, initialTargetPopSize)
        budget = sum(initialAllocation)
        # generate cost curves for each intervention
        generateCostCurves(spreadsheetData, model, self.helper.keyList, self.dataSpreadsheetName, costCoverageInfo,
                                        self.costCurveType, resultsFileStem, budget, cascade, scale)




class GeospatialOptimisation:
    def __init__(self, regionSpreadsheetList, regionNameList, numModelSteps, cascadeValues, optimise, resultsFileStem, costCurveType, BOCsFileStem, IYCF_cov_regional=None):
        self.regionSpreadsheetList = regionSpreadsheetList
        self.regionNameList = regionNameList
        self.numModelSteps = numModelSteps
        self.numRegions = len(regionSpreadsheetList)
        self.cascadeValues = cascadeValues
        self.optimise = optimise
        self.resultsFileStem = resultsFileStem
        self.BOCsFileStem = BOCsFileStem
        self.costCurveType = costCurveType
        self.currentRegionalBudgets = self.getCurrentRegionalBudgets(IYCF_cov_regional=IYCF_cov_regional)
        self.nationalBudget = sum(self.currentRegionalBudgets)
        self.numRegions = len(regionSpreadsheetList)        
        self.tradeOffCurves = None
        self.postGATimeSeries = None
        import os
        # check that results directory exists and if not then create it
        if not os.path.exists(resultsFileStem):
            os.makedirs(resultsFileStem)
        if BOCsFileStem is not None: # None when optimising regions independently
            self.checkForRegionalBOCs()

    def checkForRegionalBOCs(self):
        import os
        if os.path.exists(self.BOCsFileStem):
            BOCsList = [self.BOCsFileStem + region + '_BOC.csv' for region in self.regionNameList]
            if all([os.path.isfile(f) for f in BOCsList]): # all files must exist
                self.regionalBOCs = self.readRegionalBOCs()
            else:
                self.regionalBOCs = None
        else:
            os.makedirs(self.BOCsFileStem)
            self.regionalBOCs = None

    def readRegionalBOCs(self):
        import csv
        from numpy import array
        from scipy.interpolate import pchip
        # get BOC curve
        regionalBOCs = []
        for region in self.regionNameList:
            with open(self.BOCsFileStem + region + "_BOC.csv", 'rb') as f:
                regionalSpending = []
                regionalOutcome = []
                reader = csv.reader(f)
                for row in reader:
                    regionalSpending.append(row[0])
                    regionalOutcome.append(row[1])
            # remove column headers
            regionalSpending = array(regionalSpending[1:])
            regionalOutcome = array(regionalOutcome[1:])
            regionalBOCs.append(pchip(regionalSpending, regionalOutcome))
        return regionalBOCs

    def generateAllRegionsBOC(self): # TODO: there will be a problem here if (extraFunds + current) > (largestCascade * current)
        print 'reading files to generate regional BOCs..'
        import optimisation
        import math
        from copy import deepcopy as dcp
        from scipy.interpolate import pchip
        regionalBOCs = []
        for region in range(0, self.numRegions):
            print 'generating BOC for region: ', self.regionNameList[region]
            thisSpreadsheet = self.regionSpreadsheetList[region]
            filename = self.resultsFileStem + self.regionNameList[region]
            thisOptimisation = optimisation.Optimisation(thisSpreadsheet, self.numModelSteps, self.optimise, filename, 'dummyCostCurve')
            # if final cascade value is 'extreme' replace it with value we used to generate .pkl file
            thisCascade = dcp(self.cascadeValues)
            regionalTotalBudget = self.currentRegionalBudgets[region]
            if self.cascadeValues[-1] == 'extreme':
                thisCascade[-1] = math.ceil(self.nationalBudget / regionalTotalBudget)
            spending, outcome = thisOptimisation.generateBOCVectors(thisCascade, self.optimise)
            self.saveBOCcurves(spending, outcome, self.regionNameList[region]) # save so can directly optimise next time
            BOCthisRegion = pchip(spending, outcome)
            regionalBOCs.append(BOCthisRegion)
        print 'finished generating regional BOCs from files'
        self.regionalBOCs = regionalBOCs

    def saveBOCcurves(self, spending, outcome, regionName):
        import csv
        from itertools import izip
        with open(self.BOCsFileStem + regionName+'_BOC.csv', 'wb') as f:
            writer = csv.writer(f)
            writer.writerow(['spending', 'outcome'])
            writer.writerows(izip(spending, outcome))
        return

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
                spending = self.tradeOffCurves[regionName]['spending'].tolist()
                outcome = self.tradeOffCurves[regionName]['outcome'].tolist()
                row1 = ['spending'] + spending
                row2 = ['outcome'] + outcome
                writer.writerow([regionName])
                writer.writerow(row1)
                writer.writerow(row2)

    def outputBOCs(self):
        from numpy import linspace
        import csv
        if self.regionalBOCs == None:
            self.generateAllRegionsBOC()
        spendingVec = linspace(0., self.nationalBudget, 10000)
        outfilename = '%sBOCs.csv' % (self.resultsFileStem)
        with open(outfilename, 'wb') as f:
            writer = csv.writer(f)
            headers = ['spending'] + self.regionNameList
            writer.writerow(headers)
            regionalOutcomes = []
            for region in range(self.numRegions):
                regionalBOC = self.regionalBOCs[region]
                regionalOutcomes.append(regionalBOC(spendingVec))
            columnLists = [spendingVec] + regionalOutcomes
            writer.writerows(zip(*columnLists))


    def getTradeOffCurves(self):
        from numpy import linspace
        # if BOCs not generated, generate them
        if self.regionalBOCs == None:
            self.generateAllRegionsBOC()
        tradeOffCurves = {}
        spendingVec = linspace(0., self.nationalBudget, 1000)
        for region in range(0, self.numRegions):
            regionName = self.regionNameList[region]
            regionalBOC = self.regionalBOCs[region]
            # transform BOC
            currentSpending = self.currentRegionalBudgets[region]
            baselineOutcome = regionalBOC(currentSpending)
            outcomeVec = regionalBOC(spendingVec)
            regionalImprovement = baselineOutcome - outcomeVec
            if self.optimise == 'thrive':
                regionalImprovement = -regionalImprovement
            additionalSpending = spendingVec - currentSpending
            tradeOffCurves[regionName] = {}
            tradeOffCurves[regionName]['spending'] = additionalSpending
            tradeOffCurves[regionName]['outcome'] = regionalImprovement
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
        
    def getCurrentRegionalBudgets(self, IYCF_cov_regional = None):
        import optimisation
        regionalBudgets = []
        for region in range(0, self.numRegions):
            thisSpreadsheet = self.regionSpreadsheetList[region]
            thisOptimisation = optimisation.Optimisation(thisSpreadsheet, self.numModelSteps, self.optimise, 'dummyFileName', 'dummyCurve')   
            if IYCF_cov_regional is not None:            
                covIYCF = IYCF_cov_regional[region]
                regionTotalBudget = thisOptimisation.getTotalInitialBudget(covIYCF)
            else:
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
            
    def generateParallelResultsForGeospatialCascades(self, numCores, MCSampleSize, haveFixedProgCosts, splitCascade, regionCovIYCF):
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
            for region in range(0, self.numRegions):
                regionName = self.regionNameList[region]
                spreadsheet = self.regionSpreadsheetList[region]
                filename = self.resultsFileStem + regionName
                thisOptimisation = optimisation.Optimisation(spreadsheet, self.numModelSteps, self.optimise, filename, self.costCurveType)
                subNumCores = len(self.cascadeValues)
                thisCascade = dcp(self.cascadeValues)
                customCoveragesIYCF = {'IYCF':regionCovIYCF[region]}
                # if final cascade value is 'extreme' replace it with totalNationalBudget / current regional total budget
                if self.cascadeValues[-1] == 'extreme':
                    regionalBudget = self.currentRegionalBudgets[region]
                    thisCascade[-1] = math.ceil(self.nationalBudget / regionalBudget) # this becomes a file name so keep it as an integer
                if splitCascade:    
                    thisOptimisation.performParallelCascadeOptimisation(MCSampleSize, thisCascade, subNumCores, haveFixedProgCosts)  
                else:
                    prc = Process(target=thisOptimisation.performCascadeOptimisationCustomCoverageIYCF, args=(MCSampleSize, thisCascade, haveFixedProgCosts, customCoveragesIYCF))
                    prc.start()

    def getOptimisedRegionalBudgetList(self):
        """Allocates funds to regions by ranking derivatives of BOCs (grid search)"""
        if self.regionalBOCs == None:
            self.generateAllRegionsBOC()
        regionalAllocation = self.runGridSearch(self.currentRegionalBudgets)
        return regionalAllocation
        
    def getOptimisedRegionalBudgetListExtraMoney(self, extraMoney, IYCF_cov_regional):
        #WARNING: HARD CODE: directly modified for Tanzania to use the correct regional budgets which include IYCF
        # if BOCs not generated, generate them
        if self.regionalBOCs == None:
            self.generateAllRegionsBOC()
        theseCurrentRegionalBudgets = self.getCurrentRegionalBudgets(IYCF_cov_regional)
        regionalAllocationExtra = self.runGridSearch(theseCurrentRegionalBudgets, extraMoney)
        # add additional funds to current
        regionalAllocation = [sum(x) for x in zip(self.currentRegionalBudgets, regionalAllocationExtra)]
        return regionalAllocation

    def getBOCderivatives(self, currentRegionalSpending, extraFunds):
        from numpy import linspace
        numPoints = 2000
        spendingVec = []
        outcomeVec = []
        costEffVecs = []
        # calculate cost effectiveness vectors for each region
        for regionIdx in range(self.numRegions):
            if extraFunds: # only consider additional funds
                regionalMaxBudget = currentRegionalSpending[regionIdx] + extraFunds
                regionalMinBudget = currentRegionalSpending[regionIdx]
            else:
                regionalMaxBudget = sum(currentRegionalSpending)
                regionalMinBudget = 0.
            spending = linspace(regionalMinBudget, regionalMaxBudget, numPoints)
            spendingThisRegion = spending[1:] # exclude 0 to avoid division error
            adjustedRegionalSpending = spendingThisRegion - regionalMinBudget # centers spending if extra funds
            spendingVec.append(adjustedRegionalSpending)
            regionalBOC = self.regionalBOCs[regionIdx]
            outcomeThisRegion = regionalBOC(spendingThisRegion)
            outcomeVec.append(outcomeThisRegion)
            costEffThisRegion = outcomeThisRegion / spendingThisRegion
            costEffVecs.append(costEffThisRegion)
        return costEffVecs, spendingVec, outcomeVec

    def getOptimalOutcomeFromBOCs(self, allocations):
        nationalOutcome = 0.
        for regionIdx in range(self.numRegions):
            regionalBOC = self.regionalBOCs[regionIdx]
            regionalOutcome = regionalBOC(allocations[regionIdx])
            nationalOutcome += regionalOutcome
        return nationalOutcome

    def runGridSearch(self, currentRegionalSpending, extraFunds=None):
        """If specified, extraFunds is a scalar value which represents funds to be distributed on top of fixed current regional spending"""
        from numpy import zeros, inf, nonzero, argmax
        from copy import deepcopy as dcp
        costEffVecs, spendingVec, outcomeVec = self.getBOCderivatives(currentRegionalSpending, extraFunds=extraFunds)
        if extraFunds:
            totalBudget = extraFunds
        else:
            totalBudget = sum(currentRegionalSpending)
        maxIters = int(1e6) # loop should break before this is reached
        remainingFunds = dcp(totalBudget)
        regionalAllocations = zeros(self.numRegions)
        percentBudgetSpent = 0.

        for i in range(maxIters):
            # find the most cost-effective region to fund
            bestEff = -inf
            bestRegion = None
            for regionIdx in range(self.numRegions):
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
                newPercentBudgetSpent = (totalBudget - remainingFunds) / totalBudget * 100.
                if not(i%100) or (newPercentBudgetSpent - percentBudgetSpent) > 1.:
                    percentBudgetSpent = newPercentBudgetSpent
            else:
                break # nothing more to allocate

        # scale to ensure correct budget
        scaledRegionalAllocations = rescaleAllocation(totalBudget, regionalAllocations)
        return scaledRegionalAllocations
        
    def performGeospatialOptimisation(self, MCSampleSize, GAFile, haveFixedProgCosts):
        import optimisation  
        print 'beginning geospatial optimisation..'
        optimisedRegionalBudgetList = self.getOptimisedRegionalBudgetList()
        print 'finished geospatial optimisation'
        for region in range(0, self.numRegions):
            regionName = self.regionNameList[region]
            print 'optimising for individual region ', regionName
            thisSpreadsheet = self.regionSpreadsheetList[region]
            thisOptimisation = optimisation.Optimisation(thisSpreadsheet, self.numModelSteps, self.optimise, self.resultsFileStem, self.costCurveType) 
            thisBudget = optimisedRegionalBudgetList[region]
            thisOptimisation.performSingleOptimisationForGivenTotalBudget(MCSampleSize, thisBudget, GAFile+'_'+regionName, haveFixedProgCosts)
            
    def performParallelGeospatialOptimisation(self, MCSampleSize, GAFile, numCores, haveFixedProgCosts):
        import optimisation  
        from multiprocessing import Process
        print 'beginning geospatial optimisation..'
        optimisedRegionalBudgetList = self.getOptimisedRegionalBudgetList()
        print 'finished geospatial optimisation'
        print optimisedRegionalBudgetList
        if self.numRegions >numCores:
            print "not enough cores to parallelise"
        else:
            for region in range(self.numRegions):
                regionName = self.regionNameList[region]
                print 'optimising for individual region ', regionName
                thisSpreadsheet = self.regionSpreadsheetList[region]
                thisOptimisation = optimisation.Optimisation(thisSpreadsheet, self.numModelSteps, self.optimise, self.resultsFileStem, self.costCurveType)
                thisBudget = optimisedRegionalBudgetList[region]
                prc = Process(
                    target=thisOptimisation.performSingleOptimisationForGivenTotalBudget,
                    args=(MCSampleSize, thisBudget, GAFile+'_'+regionName, haveFixedProgCosts))
                prc.start()


    def performParallelGeospatialOptimisationExtraMoney(self, MCSampleSize, GAFile, numCores, extraMoney, haveFixedProgCosts, IYCF_cov_regional):
        # WARNING: HARD CODE: has been edited for Tanzania specifically
        # this optimisation keeps current regional spending the same and optimises only additional spending across regions        
        import optimisation  
        from multiprocessing import Process
        print 'beginning geospatial optimisation..'
        optimisedRegionalBudgetList = self.getOptimisedRegionalBudgetListExtraMoney(extraMoney, IYCF_cov_regional)
        print 'finished geospatial optimisation'
        if self.numRegions >numCores:
            print "not enough cores to parallelise"
        else:    
            for region in range(0, self.numRegions):
                regionName = self.regionNameList[region]
                print 'optimising for individual region ', regionName
                covIYCF = IYCF_cov_regional[region]
                thisSpreadsheet = self.regionSpreadsheetList[region]
                thisOptimisation = optimisation.Optimisation(thisSpreadsheet, self.numModelSteps, self.optimise, self.resultsFileStem, 'dummyCurveType')
                thisBudget = optimisedRegionalBudgetList[region]
                prc = Process(
                    target=thisOptimisation.performSingleOptimisationForGivenTotalBudgetIYCF, 
                    args=(MCSampleSize, thisBudget, GAFile+'_'+regionName, haveFixedProgCosts, covIYCF))
                prc.start()

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
        for region in range(self.numRegions):
            regionName = self.regionNameList[region]
            print regionName
            thisSpreadsheet = self.regionSpreadsheetList[region]
            filename = self.resultsFileStem+regionName
            thisOptimisation = optimisation.Optimisation(thisSpreadsheet, self.numModelSteps, self.optimise, filename, self.costCurveType) 
            thisCascade = dcp(self.cascadeValues)      
            # if final cascade value is 'extreme' replace it with value we used to generate .pkl file
            if self.cascadeValues[-1] == 'extreme':
                regionalBudget = self.currentRegionalBudgets[region]
                thisCascade[-1] = math.ceil(self.nationalBudget / regionalBudget)
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
                    

                   