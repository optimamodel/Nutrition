# -*- coding: utf-8 -*-
"""
Created on Mon Jul 11 17:54:47 2016

@author: ruth
"""

import optimisation

numModelSteps = 180
MCSampleSize = 1
geoMCSampleSize = 25
filenameStem = 'testGeoOutput'
cascadeValues = [0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 4.0]  
optimise = 'deaths'
spreadsheet0 = 'input_spreadsheets/Bangladesh/subregionSpreadsheets/Barisal.xlsx'
spreadsheet1 = 'input_spreadsheets/Bangladesh/subregionSpreadsheets/Chittagong.xlsx'
spreadsheet2 = 'input_spreadsheets/Bangladesh/subregionSpreadsheets/Dhaka.xlsx'
spreadsheet3 = 'input_spreadsheets/Bangladesh/subregionSpreadsheets/Khulna.xlsx'
spreadsheet4 = 'input_spreadsheets/Bangladesh/subregionSpreadsheets/Rajshahi.xlsx'
spreadsheet5 = 'input_spreadsheets/Bangladesh/subregionSpreadsheets/Rangpur.xlsx'
spreadsheet6 = 'input_spreadsheets/Bangladesh/subregionSpreadsheets/Sylhet.xlsx'
spreadsheetList = [spreadsheet0, spreadsheet1, spreadsheet2, spreadsheet3, spreadsheet4, spreadsheet5, spreadsheet6]

cascadeFilenameList = []
for region in range(0, len(spreadsheetList)):
    filename = 'Results2016Jun/Bangladesh/deaths/geospatial/v3/region' + str(region) + '_cascade_deaths_'
    cascadeFilenameList.append(filename)

geospatialOptimisation = optimisation.GeospatialOptimisation(spreadsheetList, cascadeFilenameList, numModelSteps, cascadeValues, optimise)
geospatialOptimisation.performGeospatialOptimisation(geoMCSampleSize, MCSampleSize, filenameStem)







#geospatialOptimisation = optimisation.GeospatialOptimisation(spreadsheetList, cascadeFilenameList, numModelSteps, cascadeValues, optimise)
#BOCDict = geospatialOptimisation.generateAllRegionsBOC()
#nationalBudget = geospatialOptimisation.getTotalNationalBudget()
#
#
#def geospatialObjectiveFunction(proposalSpendingList, regionalBOCs, totalBudget):
#    import pchip
#    numRegions = len(proposalSpendingList)
#    if sum(proposalSpendingList) == 0: 
#        scaledProposalSpendingList = proposalSpendingList
#    else:    
#        scaledProposalSpendingList = rescaleAllocation(totalBudget, proposalSpendingList)    
#    outcomeList = []
#    for region in range(0, numRegions):
#        outcome = pchip.pchip(regionalBOCs['spending'][region], regionalBOCs['outcome'][region], scaledProposalSpendingList[region], deriv = False, method='pchip')        
#        outcomeList.append(outcome)
#    nationalOutcome = sum(outcomeList)
#    return nationalOutcome  
#    
#def rescaleAllocation(totalBudget, proposalAllocation):
#    scaleRatio = totalBudget / sum(proposalAllocation)
#    rescaledAllocation = [x * scaleRatio for x in proposalAllocation]
#    return rescaledAllocation     
#    
#class OutputClass:
#    def __init__(self, budgetBest, fval, exitflag, cleanOutputIterations, cleanOutputFuncCount, cleanOutputFvalVector, cleanOutputXVector):
#        self.budgetBest = budgetBest
#        self.fval = fval
#        self.exitflag = exitflag
#        self.cleanOutputIterations = cleanOutputIterations
#        self.cleanOutputFuncCount = cleanOutputFuncCount
#        self.cleanOutputFvalVector = cleanOutputFvalVector
#        self.cleanOutputXVector = cleanOutputXVector      
#            
#
#regionalBOCs = BOCDict
#import asd
#import numpy as np
#xmin = [0.] * 7
#totalBudget = geospatialOptimisation.getTotalNationalBudget()
#scenarioMonteCarloOutput = []
#for r in range(0, 1):
#    proposalSpendingList = np.random.rand(7)
#    args = {'regionalBOCs':regionalBOCs, 'totalBudget':totalBudget}
#    budgetBest, fval, exitflag, output = asd.asd(geospatialObjectiveFunction, proposalSpendingList, args, xmin = xmin, verbose = 2)  
#    outputOneRun = OutputClass(budgetBest, fval, exitflag, output.iterations, output.funcCount, output.fval, output.x)        
#    scenarioMonteCarloOutput.append(outputOneRun)  
#    
## find the best
#bestSample = scenarioMonteCarloOutput[0]
#for sample in range(0, len(scenarioMonteCarloOutput)):
#    if scenarioMonteCarloOutput[sample].fval < bestSample.fval:
#        bestSample = scenarioMonteCarloOutput[sample]
#bestSampleScaled = rescaleAllocation(totalBudget, bestSample.budgetBest)        
#optimisedRegionalBudgetList = bestSampleScaled  
#
#filenameStem = 'testGeoOutput'
#import optimisation        
#for region in range(0, 7):
#    print region
#    filename = filenameStem + '_region_' + str(region) #filenameList[region]
#    thisSpreadsheet = spreadsheetList[region]
#    thisOptimisation = optimisation.Optimisation(thisSpreadsheet, numModelSteps) 
#    thisBudget = optimisedRegionalBudgetList[region]
#    thisOptimisation.performSingleOptimisationForGivenTotalBudget(optimise, MCSampleSize, filename, thisBudget)
#    
    