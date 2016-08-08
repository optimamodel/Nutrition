# -*- coding: utf-8 -*-
"""
Created on Wed Jun  8 13:58:29 2016

@author: ruth
"""
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
            spending = costCov.inversefunction(coverageNumber, costCoverageInfo[intervention], targetPopSize[intervention])  
        allocation.append(spending)
    return allocation

def rescaleAllocation(totalBudget, allocation):
    scaleRatio = totalBudget / sum(allocation)
    rescaledAllocation = [x * scaleRatio for x in allocation]
    return rescaledAllocation 
    
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

    
def objectiveFunction(allocation, totalBudget, fixedCosts, costCoverageInfo, optimise, numModelSteps, dataSpreadsheetName, data):
    import helper 
    import costcov
    from copy import deepcopy as dcp
    from operator import add
    helper = helper.Helper()
    costCov = costcov.Costcov()
    model, derived, params = helper.setupModelConstantsParameters(data)
    availableBudget = totalBudget - sum(fixedCosts)
    #make sure fixed costs do not exceed total budget
    if totalBudget < fixedCosts:
        print "error: total budget is less than fixed costs"
        break
    # scale the asd allocation appropriately
    if sum(allocation) == 0: 
        scaledAllocation = dcp(allocation)
    else:    
        scaledAllocation = rescaleAllocation(availableBudget, allocation)
    # add the fixed costs to the scaled allocation of available budget
    scaledAllocation = map(add, scaledAllocation, fixedCosts)   
    # run the model
    timestepsPre = 12
    for t in range(timestepsPre):
        model.moveOneTimeStep()    
    # update coverages after 1 year   
    targetPopSize = getTargetPopSizeFromModelInstance(dataSpreadsheetName, helper.keyList, model)   
    newCoverages = {}    
    for i in range(0, len(data.interventionList)):
        intervention = data.interventionList[i]
        newCoverages[intervention] = costCov.function(scaledAllocation[i], costCoverageInfo[intervention], targetPopSize[intervention]) / targetPopSize[intervention]
    model.updateCoverages(newCoverages)
    for t in range(numModelSteps - timestepsPre):
        model.moveOneTimeStep()
    performanceMeasure = model.getOutcome(optimise)
    return performanceMeasure    
    
def geospatialObjectiveFunction(spendingList, regionalBOCs, totalBudget):
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
    return nationalOutcome    
    
def geospatialObjectiveFunctionExtraMoney(spendingList, regionalBOCs, currentRegionalSpendingList, extraMoney):
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
    def __init__(self, dataSpreadsheetName, numModelSteps, optimise, resultsFileStem):
        import helper       
        self.dataSpreadsheetName = dataSpreadsheetName
        self.numModelSteps = numModelSteps
        self.optimise = optimise
        self.resultsFileStem = resultsFileStem
        self.helper = helper.Helper()
        
    def performSingleOptimisation(self, MCSampleSize):
        import data 
        spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)        
        costCoverageInfo = self.getCostCoverageInfo()  
        initialTargetPopSize = self.getInitialTargetPopSize()
        initialAllocation = getTotalInitialAllocation(spreadsheetData, costCoverageInfo, initialTargetPopSize)
        totalBudget = sum(initialAllocation)
        xmin = [0.] * len(initialAllocation)
        args = {'totalBudget':totalBudget, 'costCoverageInfo':costCoverageInfo, 'optimise':self.optimise, 'numModelSteps':self.numModelSteps, 'dataSpreadsheetName':self.dataSpreadsheetName, 'data':spreadsheetData}    
        self.runOnce(MCSampleSize, xmin, args, spreadsheetData.interventionList, totalBudget, self.resultsFileStem+'.pkl')
        
    def performSingleOptimisationForGivenTotalBudget(self, MCSampleSize, totalBudget, filename):
        import data 
        spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)        
        costCoverageInfo = self.getCostCoverageInfo()  
        xmin = [0.] * len(spreadsheetData.interventionList)
        args = {'totalBudget':totalBudget, 'costCoverageInfo':costCoverageInfo, 'optimise':self.optimise, 'numModelSteps':self.numModelSteps, 'dataSpreadsheetName':self.dataSpreadsheetName, 'data':spreadsheetData}    
        self.runOnce(MCSampleSize, xmin, args, spreadsheetData.interventionList, totalBudget, self.resultsFileStem+filename+'.pkl')    
        
        
    def performCascadeOptimisation(self, MCSampleSize, cascadeValues):
        import data 
        spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)        
        costCoverageInfo = self.getCostCoverageInfo()  
        initialTargetPopSize = self.getInitialTargetPopSize()          
        initialAllocation = getTotalInitialAllocation(spreadsheetData, costCoverageInfo, initialTargetPopSize)
        currentTotalBudget = sum(initialAllocation)
        xmin = [0.] * len(initialAllocation)
        for cascade in cascadeValues:
            totalBudget = currentTotalBudget * cascade
            args = {'totalBudget':totalBudget, 'costCoverageInfo':costCoverageInfo, 'optimise':self.optimise, 'numModelSteps':self.numModelSteps, 'dataSpreadsheetName':self.dataSpreadsheetName, 'data':spreadsheetData}    
            self.runOnce(MCSampleSize, xmin, args, spreadsheetData.interventionList, totalBudget, self.resultsFileStem+'_cascade_'+str(self.optimise)+'_'+str(cascade)+'.pkl')    

    def cascadeParallelRunFunction(self, cascadeValue, currentTotalBudget, fixedCosts, spreadsheetData, costCoverageInfo, MCSampleSize, xmin):
        totalBudget = currentTotalBudget * cascadeValue
        args = {'totalBudget':totalBudget, 'fixedCosts':fixedCosts, 'costCoverageInfo':costCoverageInfo, 'optimise':self.optimise, 'numModelSteps':self.numModelSteps, 'dataSpreadsheetName':self.dataSpreadsheetName, 'data':spreadsheetData}    
        self.runOnce(MCSampleSize, xmin, args, spreadsheetData.interventionList, totalBudget, self.resultsFileStem+'_cascade_'+str(self.optimise)+'_'+str(cascadeValue)+'.pkl')                   
    
    
    def performParallelCascadeOptimisation(self, MCSampleSize, cascadeValues, numCores, haveFixedProgCosts):
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
        # check that you have enough cores and don't parallelise if you don't
        if numCores < len(cascadeValues):
            print "numCores is not enough"
        else:    
            for value in cascadeValues:
                prc = Process(
                    target=self.cascadeParallelRunFunction, 
                    args=(value, currentTotalBudget, fixedCosts, spreadsheetData, costCoverageInfo, MCSampleSize, xmin))
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
        # scale it and make a dictionary
        bestSampleBudget = bestSample.budgetBest
        bestSampleBudgetScaled = rescaleAllocation(totalBudget, bestSampleBudget)
        bestSampleBudgetScaledDict = {}
        for i in range(0, len(interventionList)):
            intervention = interventionList[i]
            bestSampleBudgetScaledDict[intervention] = bestSampleBudgetScaled[i]      
        # put it in a file    
        outfile = open(filename, 'wb')
        pickle.dump(bestSampleBudgetScaledDict, outfile)
        outfile.close()  
        
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
        
    def getTotalInitialBudget(self):
        import data 
        spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)        
        costCoverageInfo = self.getCostCoverageInfo()
        targetPopSize = self.getInitialTargetPopSize()        
        initialAllocation = getTotalInitialAllocation(spreadsheetData, costCoverageInfo, targetPopSize)        
        return sum(initialAllocation)     
        
        
        
    def oneModelRunWithOutput(self, allocationDictionary):
        import costcov
        import data
        from copy import deepcopy as dcp
        costCov = costcov.Costcov()
        spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList)
        model, derived, params = self.helper.setupModelConstantsParameters(spreadsheetData)
        costCoverageInfo = self.getCostCoverageInfo()
        # run the model
        modelList = []    
        timestepsPre = 12
        for t in range(timestepsPre):
            model.moveOneTimeStep()  
            modelThisTimeStep = dcp(model)
            modelList.append(modelThisTimeStep)
        # update coverages after 1 year    
        targetPopSize = getTargetPopSizeFromModelInstance(self.dataSpreadsheetName, self.helper.keyList, model)
        newCoverages = {}    
        for i in range(0, len(spreadsheetData.interventionList)):
            intervention = spreadsheetData.interventionList[i]
            newCoverages[intervention] = costCov.function(allocationDictionary[intervention], costCoverageInfo[intervention], targetPopSize[intervention]) / targetPopSize[intervention]
        model.updateCoverages(newCoverages)
        for t in range(self.numModelSteps - timestepsPre):
            model.moveOneTimeStep()
            modelThisTimeStep = dcp(model)
            modelList.append(modelThisTimeStep)
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
    
    
    def generateBOCVectors(self, regionNameList, cascadeValues, outcome):
        import pickle
        import data
        spreadsheetData = data.readSpreadsheet(self.dataSpreadsheetName, self.helper.keyList) 
        costCoverageInfo = self.getCostCoverageInfo()
        targetPopSize = self.getInitialTargetPopSize()
        initialAllocation = getTotalInitialAllocation(spreadsheetData, costCoverageInfo, targetPopSize)
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
        
    def plotTimeSeries(self):
        import pickle
        from plotting import plotTimeSeries
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
            objective[scenario].append(modelRun[scenario][0].getOutcome(self.optimise))
            for i in range(1, self.numModelSteps):
                difference = modelRun[scenario][i].getOutcome(self.optimise) - modelRun[scenario][i-1].getOutcome(self.optimise)
                objective[scenario].append(difference)
            # make it yearly
            numYears = self.numModelSteps/12
            objectiveYearly[scenario] = []
            for i in range(0, numYears):
                step = i*12
                objectiveYearly[scenario].append( sum(objective[scenario][step:12+step]) )
        title = self.optimise   
        years = range(2016, 2016 + numYears)
        plotTimeSeries(years, objectiveYearly['baseline'], objectiveYearly[self.optimise], title)
            



class GeospatialOptimisation:
    def __init__(self, regionSpreadsheetList, regionNameList, numModelSteps, cascadeValues, optimise, resultsFileStem):
        self.regionSpreadsheetList = regionSpreadsheetList
        self.regionNameList = regionNameList
        self.numModelSteps = numModelSteps
        self.cascadeValues = cascadeValues
        self.optimise = optimise
        self.resultsFileStem = resultsFileStem
        self.numRegions = len(regionSpreadsheetList)        
        self.regionalBOCs = None 
        self.tradeOffCurves = None
        
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
            thisOptimisation = optimisation.Optimisation(thisSpreadsheet, self.numModelSteps, self.optimise, filename)
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
        
    def outputTradeOffCurves(self, filename):
        import pickle
        self.getTradeOffCurves()
        outfile = open(filename, 'wb')
        pickle.dump(self.tradeOffCurves, outfile)
        outfile.close()  
        
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
            currentOucome = self.regionalBOCs['outcome'][region][index]
            tradeOffCurves[regionName] = {}
            spendDifference = []
            outcomeAverted = []            
            for i in range(len(self.cascadeValues)):
                spendDifference.append( self.regionalBOCs['spending'][region][i] - currentSpending )
                outcomeAverted.append( currentOucome - self.regionalBOCs['outcome'][region][i]  )
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
            thisOptimisation = optimisation.Optimisation(thisSpreadsheet, self.numModelSteps, self.optimise, 'dummyFileName')        
            regionTotalBudget = thisOptimisation.getTotalInitialBudget()
            regionalBudgets.append(regionTotalBudget)
        nationalTotalBudget = sum(regionalBudgets)
        return nationalTotalBudget
        
    def getCurrentRegionalBudgets(self):
        import optimisation
        regionalBudgets = []
        for region in range(0, self.numRegions):
            thisSpreadsheet = self.regionSpreadsheetList[region]
            thisOptimisation = optimisation.Optimisation(thisSpreadsheet, self.numModelSteps, self.optimise, 'dummyFileName')        
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
            
    def generateParallelResultsForGeospatialCascades(self, numCores, MCSampleSize, haveFixedProgCosts):
        import optimisation  
        import math
        from copy import deepcopy as dcp
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
                thisOptimisation = optimisation.Optimisation(spreadsheet, self.numModelSteps, self.optimise, filename)
                subNumCores = len(self.cascadeValues)
                thisCascade = dcp(self.cascadeValues)
                # if final cascade value is 'extreme' replace it with totalNationalBudget / current regional total budget
                if self.cascadeValues[-1] == 'extreme':
                    regionalTotalBudget = thisOptimisation.getTotalInitialBudget()
                    thisCascade[-1] = math.ceil(totalNationalBudget / regionalTotalBudget) # this becomes a file name so keep it as an integer
                thisOptimisation.performParallelCascadeOptimisation(MCSampleSize, thisCascade, subNumCores, haveFixedProgCosts)  
                
                

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
            args = {'regionalBOCs':self.regionalBOCs, 'totalBudget':totalBudget}
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
            args = {'regionalBOCs':self.regionalBOCs, 'currentRegionalSpendingList':currentRegionalSpendingList, 'extraMoney':extraMoney}
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
        
    def performGeospatialOptimisation(self, geoMCSampleSize, MCSampleSize, GAFile):
        import optimisation  
        print 'beginning geospatial optimisation..'
        optimisedRegionalBudgetList = self.getOptimisedRegionalBudgetList(geoMCSampleSize)
        print 'finished geospatial optimisation'
        for region in range(0, self.numRegions):
            regionName = self.regionNameList[region]
            print 'optimising for individual region ', regionName
            thisSpreadsheet = self.regionSpreadsheetList[region]
            thisOptimisation = optimisation.Optimisation(thisSpreadsheet, self.numModelSteps, self.optimise, self.resultsFileStem) 
            thisBudget = optimisedRegionalBudgetList[region]
            thisOptimisation.performSingleOptimisationForGivenTotalBudget(MCSampleSize, thisBudget, GAFile+'_'+regionName)
            
    def performParallelGeospatialOptimisation(self, geoMCSampleSize, MCSampleSize, GAFile, numCores):
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
                thisOptimisation = optimisation.Optimisation(thisSpreadsheet, self.numModelSteps, self.optimise, self.resultsFileStem) 
                thisBudget = optimisedRegionalBudgetList[region]
                prc = Process(
                    target=thisOptimisation.performSingleOptimisationForGivenTotalBudget, 
                    args=(MCSampleSize, thisBudget, GAFile+'_'+regionName))
                prc.start()
                
    def performParallelGeospatialOptimisationExtraMoney(self, geoMCSampleSize, MCSampleSize, GAFile, numCores, extraMoney):
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
                    args=(MCSampleSize, thisBudget, GAFile+'_'+regionName))
                prc.start()            
        
    def plotReallocationByRegion(self):
        from plotting import plotallocations 
        import pickle
        import optimisation
        geospatialAllocations = {}
        for iReg in range(self.numRegions):
            regionName = self.regionNameList[iReg]
            print regionName
            thisOptimisation = optimisation.Optimisation(self.regionSpreadsheetList[iReg], self.numModelSteps, self.optimise, 'dummyFilename')
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
            thisOptimisation = optimisation.Optimisation(self.regionSpreadsheetList[iReg], self.numModelSteps, self.optimise, 'dummyFilename')
            geospatialAllocations[regionName] = {}
            geospatialAllocations[regionName]['baseline'] = thisOptimisation.getInitialAllocationDictionary()
            filename = '%s%s_%s.pkl'%(self.resultsFileStem, GAFile, regionName)
            infile = open(filename, 'rb')
            allocation = pickle.load(infile)
            geospatialAllocations[regionName][self.optimise] = allocation
            infile.close()
            # plot
            plotallocations(geospatialAllocations[regionName]['baseline'],geospatialAllocations[regionName][self.optimise])       
            
    def plotTimeSeriesPostGAReallocationByRegion(self, GAFile):
        import pickle
        import optimisation
        from plotting import plotTimeSeries
        from copy import deepcopy as dcp
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
                numYears = self.numModelSteps/12
                objectiveYearly[scenario] = []
                for i in range(0, numYears):
                    step = i*12
                    objectiveYearly[scenario].append( sum(objective[scenario][step:12+step]) )
            title = regionName + '  ' + self.optimise   
            years = range(2016, 2016 + numYears)
            plotTimeSeries(years, objectiveYearly['baseline'], objectiveYearly[self.optimise], title)
        
        
        
        
        
        
        
        
        
        
