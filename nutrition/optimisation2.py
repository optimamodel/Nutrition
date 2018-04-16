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

def getTotalInitialAllocation(data, costCoverageInfo, targetPopSize):
    from old_files import costcov
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
    from old_files import costcov
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
    from old_files import helper
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

def getTargetPopSizeFromModelInstance(dataSpreadsheetName, keyList, model):    
    import data
    from old_files import helper
    thisHelper = helper.Helper()
    spreadsheetData = data.readSpreadsheet(dataSpreadsheetName, keyList)        
    targetPopSize = {}
    for intervention in spreadsheetData.interventionCompleteList:
        targetPopSize[intervention] = 0.
        # children
        numAgeGroups = len(keyList['ages'])
        for iAge in range(numAgeGroups):
            ageName = keyList['ages'][iAge]
            if "IFAS" in intervention:
                target = 0.
            else:
                target = spreadsheetData.targetPopulation[intervention][ageName]
            targetPopSize[intervention] += target * model.listOfAgeCompartments[iAge].getTotalPopulation()
        # pregnant women
        numAgeGroups = len(keyList['pregnantWomenAges'])    
        for iAge in range(numAgeGroups):
            ageName = keyList['pregnantWomenAges'][iAge]  
            if "IFAS" in intervention:
                target = 0.
            else:
                target = spreadsheetData.targetPopulation[intervention][ageName]
            targetPopSize[intervention] += target * model.listOfPregnantWomenAgeCompartments[iAge].getTotalPopulation()
        # women of reproductive age
        numAgeGroups = len(keyList['reproductiveAges'])    
        for iAge in range(numAgeGroups):
            ageName = keyList['reproductiveAges'][iAge]  
            if "IFAS" in intervention:
                target = 0.
            else:
                target = spreadsheetData.targetPopulation[intervention][ageName]
            targetPopSize[intervention] += target * model.listOfReproductiveAgeCompartments[iAge].getTotalPopulation()
        # for food fortification set target population size as entire population
        if "fortification" in intervention:
           targetPopSize[intervention] =  spreadsheetData.demographics['total population'] #TODO: consider changing to demographic projection rather than baseline value
    # get IFAS target populations seperately
    fromModel = True       
    targetPopSize.update(thisHelper.setIFASTargetPopWRA(spreadsheetData, model, fromModel))       
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


class Optimisation:
    def __init__(self, dataSpreadsheetName, numModelSteps, optimise, resultsFileStem, costCurveType):
        from old_files import helper
        self.dataSpreadsheetName = dataSpreadsheetName
        self.spreadsheetData = None
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
            
    def loadData(self):
        import data
        if self.spreadsheetData is None:
            self.spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)        
        
    def performSingleOptimisation(self, MCSampleSize, haveFixedProgCosts):
        import data
        if self.spreadsheetData is None:
            self.spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)        
        costCoverageInfo = self.getCostCoverageInfo()  
        initialTargetPopSize = self.getInitialTargetPopSize()
        initialAllocation = getTotalInitialAllocation(self.spreadsheetData, costCoverageInfo, initialTargetPopSize)
        totalBudget = sum(initialAllocation)
        xmin = [0.] * len(initialAllocation)
        # set up and run the model prior to optimising
        fixedCosts = self.getFixedCosts(haveFixedProgCosts, initialAllocation)
        timestepsPre = 12
        model = runModelForNTimeSteps(timestepsPre, self.spreadsheetData, model=None)[0]
        # generate cost curves for each intervention
        costCurves = generateCostCurves(self.spreadsheetData, model, self.helper.keyList, self.dataSpreadsheetName,
                                        costCoverageInfo, self.costCurveType)        
        args = {'costCurves': costCurves, 'model': model, 'timestepsPre': timestepsPre,
                'totalBudget': totalBudget, 'fixedCosts': fixedCosts, 'costCoverageInfo': costCoverageInfo,
                'optimise': self.optimise, 'numModelSteps': self.numModelSteps,
                'dataSpreadsheetName': self.dataSpreadsheetName, 'data': self.spreadsheetData}        
        self.runOnce(MCSampleSize, xmin, args, self.spreadsheetData.interventionList, totalBudget, self.resultsFileStem+'.pkl')
        
    def performSingleOptimisationForGivenTotalBudget(self, MCSampleSize, totalBudget, filename, haveFixedProgCosts):
        import data
        if self.spreadsheetData is None:
            self.spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)        
        costCoverageInfo = self.getCostCoverageInfo()  
        xmin = [0.] * len(self.spreadsheetData.interventionList)
        initialTargetPopSize = self.getInitialTargetPopSize() 
        initialAllocation = getTotalInitialAllocation(self.spreadsheetData, costCoverageInfo, initialTargetPopSize)
        fixedCosts = self.getFixedCosts(haveFixedProgCosts, initialAllocation)
        timestepsPre = 12
        # set up and run the model prior to optimising
        model = runModelForNTimeSteps(timestepsPre, self.spreadsheetData, model=None)[0]
        # generate cost curves for each intervention
        costCurves = generateCostCurves(self.spreadsheetData, model, self.helper.keyList, self.dataSpreadsheetName,
                                        costCoverageInfo, self.costCurveType)
        args = {'costCurves': costCurves, 'model': model, 'timestepsPre': timestepsPre,
                'totalBudget': totalBudget, 'fixedCosts': fixedCosts, 'costCoverageInfo': costCoverageInfo,
                'optimise': self.optimise, 'numModelSteps': self.numModelSteps,
                'dataSpreadsheetName': self.dataSpreadsheetName, 'data': self.spreadsheetData}
        self.runOnce(MCSampleSize, xmin, args, self.spreadsheetData.interventionList, totalBudget, self.resultsFileStem+filename+'.pkl')

        
    def performCascadeOptimisation(self, MCSampleSize, cascadeValues, haveFixedProgCosts):
        import data
        if self.spreadsheetData is None:
            self.spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)
        timestepsPre = 12
        costCoverageInfo = self.getCostCoverageInfo()
        initialTargetPopSize = self.getInitialTargetPopSize()
        initialAllocation = getTotalInitialAllocation(self.spreadsheetData, costCoverageInfo, initialTargetPopSize)
        currentTotalBudget = sum(initialAllocation)
        xmin = [0.] * len(initialAllocation)
        # set fixed costs if you have them
        fixedCosts = self.getFixedCosts(haveFixedProgCosts, initialAllocation)
        # run the model prior to optimising
        model = runModelForNTimeSteps(timestepsPre, self.spreadsheetData, model=None)[0]
        # generate cost curves for each intervention
        costCurves = generateCostCurves(self.spreadsheetData, model, self.helper.keyList, self.dataSpreadsheetName, costCoverageInfo,
                                        self.costCurveType)
        for cascade in cascadeValues:
            totalBudget = currentTotalBudget * cascade
            args = {'costCurves': costCurves, 'model': model, 'timestepsPre': timestepsPre,
                    'totalBudget':totalBudget, 'fixedCosts':fixedCosts, 'costCoverageInfo':costCoverageInfo,
                    'optimise':self.optimise, 'numModelSteps':self.numModelSteps,
                    'dataSpreadsheetName':self.dataSpreadsheetName, 'data':self.spreadsheetData}
            outFile = self.resultsFileStem+'_cascade_'+str(self.optimise)+'_'+str(cascade)+'.pkl'
            self.runOnce(MCSampleSize, xmin, args, self.spreadsheetData.interventionList, totalBudget, outFile)

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
        if self.spreadsheetData is None:
            self.spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)
        costCoverageInfo = self.getCostCoverageInfo()
        initialTargetPopSize = self.getInitialTargetPopSize()
        initialAllocation = getTotalInitialAllocation(self.spreadsheetData, costCoverageInfo, initialTargetPopSize)
        currentTotalBudget = sum(initialAllocation)
        xmin = [0.] * len(initialAllocation)
        timestepsPre = 12
        # set fixed costs if you have them
        fixedCosts = self.getFixedCosts(haveFixedProgCosts, initialAllocation)
        # set up and run the model prior to optimising
        model = runModelForNTimeSteps(timestepsPre, self.spreadsheetData, model=None)[0]
        # generate cost curves for each intervention
        costCurves = generateCostCurves(self.spreadsheetData, model, self.helper.keyList, self.dataSpreadsheetName,
                                        costCoverageInfo, self.costCurveType)
        # check that you have enough cores and don't parallelise if you don't
        if numCores < len(cascadeValues):
            print "numCores is not enough"
        else:
            for value in cascadeValues:
                prc = Process(
                    target=self.cascadeParallelRunFunction,
                    args=(costCurves, model, timestepsPre, value, currentTotalBudget, fixedCosts, self.spreadsheetData,
                            costCoverageInfo, MCSampleSize, xmin))
                prc.start()

        
    def performParallelSampling(self, MCSampleSize, haveFixedProgCosts, numRuns, filename):
        import data 
        from multiprocessing import Process
        if self.spreadsheetData is None:
            self.spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)        
        costCoverageInfo = self.getCostCoverageInfo()  
        initialTargetPopSize = self.getInitialTargetPopSize()          
        initialAllocation = getTotalInitialAllocation(self.spreadsheetData, costCoverageInfo, initialTargetPopSize)
        currentTotalBudget = sum(initialAllocation)
        xmin = [0.] * len(initialAllocation)
        # set fixed costs if you have them
        fixedCosts = self.getFixedCosts(haveFixedProgCosts, initialAllocation) 
        runOnceArgs = {'totalBudget':currentTotalBudget, 'fixedCosts':fixedCosts, 'costCoverageInfo':costCoverageInfo, 'optimise':self.optimise, 'numModelSteps':self.numModelSteps, 'dataSpreadsheetName':self.dataSpreadsheetName, 'data':self.spreadsheetData}
        for i in range(numRuns):
            prc = Process(
                target=self.runOnceDumpFullOutputToFile, 
                args=(MCSampleSize, xmin, runOnceArgs, self.spreadsheetData.interventionList, currentTotalBudget, filename+"_"+str(i)))
            prc.start()    

    def performParallelCascadeOptimisationAlteredInterventionEffectiveness(self, MCSampleSize, cascadeValues, numCores, haveFixedProgCosts, intervention, effectiveness, savePlot):
        import data
        from multiprocessing import Process
        if self.spreadsheetData is None:
            self.spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)
        costCoverageInfo = self.getCostCoverageInfo()
        initialTargetPopSize = self.getInitialTargetPopSize()
        initialAllocation = getTotalInitialAllocation(self.spreadsheetData, costCoverageInfo, initialTargetPopSize)
        currentTotalBudget = sum(initialAllocation)
        xmin = [0.] * len(initialAllocation)
        timestepsPre = 12
        # set fixed costs if you have them
        fixedCosts = self.getFixedCosts(haveFixedProgCosts, initialAllocation)
        # alter mortality & incidence effectiveness
        for ageName in self.helper.keyList['ages']:
            self.spreadsheetData.effectivenessMortality[intervention][ageName]['Diarrhea'] *= effectiveness
            self.spreadsheetData.effectivenessIncidence[intervention][ageName]['Diarrhea'] *= effectiveness
        # set up and run the model prior to optimising
        model = runModelForNTimeSteps(timestepsPre, self.spreadsheetData, model=None)[0]
        # generate cost curves for each intervention
        if savePlot:
            resultsPath = self.resultsFileStem
        else:
            resultsPath = None
        costCurves = generateCostCurves(self.spreadsheetData, model, self.helper.keyList, self.dataSpreadsheetName,
                                        costCoverageInfo, self.costCurveType, resultsFileStem=resultsPath, budget=currentTotalBudget, cascade=cascadeValues)
        # check that you have enough cores and don't parallelise if you don't
        if numCores < len(cascadeValues):
            print "numCores is not enough"
        else:
            for value in cascadeValues:
                prc = Process(
                    target=self.cascadeParallelRunFunction,
                    args=(costCurves, model, timestepsPre, value, currentTotalBudget, fixedCosts, self.spreadsheetData,
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
        import numpy as np
        from operator import add
        numInterventions = len(interventionList)
        scenarioMonteCarloOutput = []
        for r in range(0, MCSampleSize):
            proposalAllocation = np.random.rand(numInterventions)
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
        import data 
        if self.spreadsheetData is None:
            self.spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)        
        costCoverageInfo = self.getCostCoverageInfo()
        targetPopSize = self.getInitialTargetPopSize()        
        initialAllocation = getTotalInitialAllocation(self.spreadsheetData, costCoverageInfo, targetPopSize)        
        initialAllocationDictionary = {}
        for i in range(0, len(self.spreadsheetData.interventionList)):
            intervention = self.spreadsheetData.interventionList[i]
            initialAllocationDictionary[intervention] = initialAllocation[i]
        return initialAllocationDictionary 
        
    def getTotalInitialBudget(self):
        import data 
        if self.spreadsheetData is None:
            self.spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)        
        costCoverageInfo = self.getCostCoverageInfo()
        targetPopSize = self.getInitialTargetPopSize()        
        initialAllocation = getTotalInitialAllocation(self.spreadsheetData, costCoverageInfo, targetPopSize)        
        return sum(initialAllocation)     
        
        
        
    def oneModelRunWithOutput(self, allocationDictionary):
        import data
        from numpy import maximum
        eps = 1.e-3  ## WARNING: using project non-specific eps
        if self.spreadsheetData is None:
            self.spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)
        costCoverageInfo = self.getCostCoverageInfo()
        timestepsPre = 12
        model, modelList = runModelForNTimeSteps(timestepsPre, self.spreadsheetData, model=None, saveEachStep=True)
        costCurves = generateCostCurves(self.spreadsheetData, model, self.helper.keyList, self.dataSpreadsheetName,
                                       costCoverageInfo, self.costCurveType)
        newCoverages = {}
        for i in range(0, len(self.spreadsheetData.interventionList)):
            intervention = self.spreadsheetData.interventionList[i]
            costCurveThisIntervention = costCurves[intervention]
            newCoverages[intervention] = maximum(costCurveThisIntervention(allocationDictionary[intervention]), eps)
        model.updateCoverages(newCoverages)
        steps = self.numModelSteps - timestepsPre
        modelList += runModelForNTimeSteps(steps, self.spreadsheetData, model, saveEachStep=True)[1]
        return modelList
    
        
    def getCostCoverageInfo(self):
        import data 
        from copy import deepcopy as dcp
        if self.spreadsheetData is None:
            self.spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)        
        costCoverageInfo = {}
        for intervention in self.spreadsheetData.interventionList:
            costCoverageInfo[intervention] = {}
            costCoverageInfo[intervention]['unitcost']   = dcp(self.spreadsheetData.costSaturation[intervention]["unit cost"])
            costCoverageInfo[intervention]['saturation'] = dcp(self.spreadsheetData.costSaturation[intervention]["saturation coverage"])
        return costCoverageInfo
        
    def getInitialTargetPopSize(self):
        import data
        from old_files import helper
        thisHelper = helper.Helper()
        if self.spreadsheetData is None:
            self.spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)        
        targetPopSize = {}
        for intervention in self.spreadsheetData.interventionCompleteList:
            targetPopSize[intervention] = 0.
            # children
            agePopSizes  = self.helper.makeAgePopSizes(self.spreadsheetData)
            numAgeGroups = len(self.helper.keyList['ages'])
            for iAge in range(numAgeGroups):
                ageName = self.helper.keyList['ages'][iAge]
                if "IFAS" in intervention:
                    target = 0.
                else:    
                    target = self.spreadsheetData.targetPopulation[intervention][ageName]
                targetPopSize[intervention] += target * agePopSizes[iAge]
            # pregnant women
            agePopSizes = self.helper.makePregnantWomenAgePopSizes(self.spreadsheetData)
            numAgeGroups = len(self.helper.keyList['pregnantWomenAges'])    
            for iAge in range(numAgeGroups):
                ageName = self.helper.keyList['pregnantWomenAges'][iAge] 
                if "IFAS" in intervention:
                    target = 0.
                else:    
                    target = self.spreadsheetData.targetPopulation[intervention][ageName]
                targetPopSize[intervention] += target * agePopSizes[iAge]
            # women of reproductive age
            agePopSizes = self.helper.makeWRAAgePopSizes(self.spreadsheetData)
            numAgeGroups = len(self.helper.keyList['reproductiveAges'])    
            for iAge in range(numAgeGroups):
                ageName = self.helper.keyList['reproductiveAges'][iAge] 
                if "IFAS" in intervention:
                    target = 0.
                else:
                    target = self.spreadsheetData.targetPopulation[intervention][ageName]
                targetPopSize[intervention] += target * agePopSizes[iAge]
            # for food fortification set target population size as entire population
            if "fortification" in intervention:
               targetPopSize[intervention] =  self.spreadsheetData.demographics['total population'] #TODO: consider changing to demographic projection rather than baseline value    
        #add IFAS intervention target pop sizes to dictionary  
        fromModel = False       
        targetPopSize.update(thisHelper.setIFASTargetPopWRA(self.spreadsheetData, "dummyModel", fromModel))        
        return targetPopSize    
    
    
    def generateBOCVectors(self, regionNameList, cascadeValues, outcome):
        import pickle
        import data
        if self.spreadsheetData is None:
            self.spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList) 
        costCoverageInfo = self.getCostCoverageInfo()
        targetPopSize = self.getInitialTargetPopSize()
        initialAllocation = getTotalInitialAllocation(self.spreadsheetData, costCoverageInfo, targetPopSize)
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
            
    def outputCascadeAndOutcomeToCSV(self, cascadeValues, outcomeOfInterest):
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
        if self.spreadsheetData is None:
            self.spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)
        timestepsPre = 12
        costCoverageInfo = self.getCostCoverageInfo()
        # run the model 
        model = runModelForNTimeSteps(timestepsPre, self.spreadsheetData, model=None)[0]
        initialTargetPopSize = self.getInitialTargetPopSize()
        initialAllocation = getTotalInitialAllocation(self.spreadsheetData, costCoverageInfo, initialTargetPopSize)
        budget = sum(initialAllocation)
        # generate cost curves for each intervention
        generateCostCurves(self.spreadsheetData, model, self.helper.keyList, self.dataSpreadsheetName, costCoverageInfo,
                                        self.costCurveType, resultsFileStem, budget, cascade, scale)




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
                    

                   