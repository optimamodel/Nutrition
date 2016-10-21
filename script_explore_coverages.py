# -*- coding: utf-8 -*-
"""
Created on Fri Oct 21 10:58:39 2016

@author: ruth
"""
# realised that plotting coverage at each time step (on the x axis) is redundant becasue the way we run the model we set coverage as constant 
import optimisation
import data 
import pickle
import helper
import costcov

costCov = costcov.Costcov()
helper = helper.Helper()
optimise = 'stunting'
numModelSteps = 180 
resultsFileStem = 'Results2016Sep21/'+optimise+'/national/Bangladesh'
cascadeValues = [0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 4.0]  
dataSpreadsheetName = 'input_spreadsheets/Bangladesh/2016Sept12/InputForCode_Bangladesh.xlsx'
spreadsheetData = data.readSpreadsheet(dataSpreadsheetName, helper.keyList)
    
finalCoverages = {}     
for cascade in cascadeValues: 
    print cascade
    finalCoverages[cascade] = {}
    # set up dictionary    
    for intervention in spreadsheetData.interventionList:
            finalCoverages[cascade][intervention] = []    
    
    thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem)
    filename = '%s_cascade_%s_%s.pkl'%(resultsFileStem, optimise, cascade)
    infile = open(filename, 'rb')
    allocation = pickle.load(infile)
    infile.close()  
    modelList = thisOptimisation.oneModelRunWithOutput(allocation)
    costCoverageInfo = thisOptimisation.getCostCoverageInfo() 
    
    for step in range(12, numModelSteps-1):
        targetPopSize = optimisation.getTargetPopSizeFromModelInstance(dataSpreadsheetName, helper.keyList, modelList[step])  
        for intervention in spreadsheetData.interventionList:
            finalCoverages[cascade][intervention].append(costCov.function(allocation[intervention], costCoverageInfo[intervention], targetPopSize[intervention]) / targetPopSize[intervention])

import matplotlib.pyplot as plt 
for cascade in cascadeValues:
    fig = plt.figure()
    ax = plt.subplot(111)    
    for intervention in spreadsheetData.interventionList:
        ax.plot(finalCoverages[cascade][intervention][:], label=intervention)
    plt.ylim(0,1)
    plt.title('cascade value:  ' + str(cascade))
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05),
          fancybox=True, shadow=True, ncol=5)    
    plt.show()            
            
            
            