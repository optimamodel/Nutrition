# -*- coding: utf-8 -*-
"""
Created on Mon Jul 25 12:25:36 2016

@author: ruth

This is an example script of how to use the optimisation class to generate and harvest results.
Use as a reference, do not edit.
"""

import optimisation

dataSpreadsheetName = '../input_spreadsheets/Bangladesh/InputForCode_Bangladesh.xlsx'
numModelSteps = 24 #180
MCSampleSize = 25
cascadeValues = [0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 4.0]
optimise = 'stunting'  

# this is the location of the optimisation results per region (to be generated or harvested)
resultsFileStem = '../ResultsExampleParallel/'+optimise+'/national/Bangladesh'

# check athena and then specify how many cores you are going to use (this translates into the number of jobs as we assume 1 core per job)
# this is only needed if you plan to run in parallel
numCores = 8

# instantiate an optimisation object
thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem)

# use it to genarate geospatial cascades if they're not already there (these will be stored in the resultsFileStem location)
thisOptimisation.performParallelCascadeOptimisation(MCSampleSize, cascadeValues, numCores)

# perform one optimisation of the curent budget
# the output file will be (resultsFileStem):
# resultsFileStem = ../ResultsExampleParallel/'+optimise+'/national/Bangladesh.pkl
thisOptimisation.performSingleOptimisation(MCSampleSize)

# perform one optimisation with any given total budget 
# (this example uses getInitialAllocationDictionary() to get
# the current spending as an example, but it could be any
# e.g. read a budget from a file)
# the output file will be (resultsFileStem + filename): 
# ../ResultsExampleParallel/'+optimise+'/national/Bangladesh_example_given_budget.pkl
totalBudget = thisOptimisation.getInitialAllocationDictionary()
filename = 'example_given_budget'
thisOptimisation.performSingleOptimisationForGivenTotalBudget(MCSampleSize, totalBudget, filename)

# run the model for a given starting budget 
# output can be used to access time series qualities of the model run
modelOutput = thisOptimisation.oneModelRunWithOutput(totalBudget)







