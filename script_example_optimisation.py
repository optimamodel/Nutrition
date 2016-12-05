# -*- coding: utf-8 -*-
"""
Created on Mon Jul 25 12:25:36 2016

@author: ruth

This is an example script of how to use the optimisation class to generate and harvest results.
Use as a reference, do not edit.
"""
# all the code is contained in the optimisation module (optimisation.py)
import optimisation

# information about the analysis
country = 'Bangladesh'
date = '2016Oct'

# the name of the spreadsheet containting the data
dataSpreadsheetName = 'input_spreadsheets/'+country+'/'+date+'/InputForCode_'+country+'.xlsx'

# how long to run the analysis for (1 step = 1 month)
numModelSteps = 180

# how many MC samples (chains of the optimisation) to run
MCSampleSize = 25

# the multiples of the current budget to run the budget cascade for 
cascadeValues = [0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 4.0]

# the objective of the optimisation
optimise = 'stunting'  

# this is the location of the optimisation results per region (to be generated or harvested)
resultsFileStem = 'Results/'+date+'/'+optimise+'/national/'+country

# check athena and then specify how many cores you are going to use (this translates into the number of jobs as we assume 1 core per job)
# this is only needed if you plan to run in parallel
numCores = 8

# this specifies if the current coverage of programs is fixed.  If True, only money above 100% of current spending will be optimised
haveFixedProgCosts = False

# instantiate an optimisation object
thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem)

# use it to genarate the cascade files if they're not already there (these will be stored in the resultsFileStem location)
# this example generates the cascade in parallel (e.g. on athena)
thisOptimisation.performParallelCascadeOptimisation(MCSampleSize, cascadeValues, numCores, haveFixedProgCosts)

# this example generates the cascade but not in parallel (eg on your laptop)
thisOptimisation.performCascadeOptimisation(MCSampleSize, cascadeValues, numCores, haveFixedProgCosts)

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
thisOptimisation.performSingleOptimisationForGivenTotalBudget(MCSampleSize, totalBudget, filename, haveFixedProgCosts)

# run the model for a given starting budget 
# output can be used to access time series qualities of the model run
modelOutput = thisOptimisation.oneModelRunWithOutput(totalBudget)

# using functions to generate output from the .pkl results files (harvesting results)
# if this is done in a separate script, the optimisation instance is setup as above

# make a csv containing the current spending 
thisOptimisation.outputCurrentSpendingToCSV() 
# output time-series to CSV (outcomeOfInterest doesn't have to be the same as optimise)
outcomeOfInterest = 'deaths'
thisOptimisation.outputTimeSeriesToCSV(outcomeOfInterest)

# output the spending cascade and the outcome cascade to csv 
thisOptimisation.outputCascadeAndOutcomeToCSV(cascadeValues, outcomeOfInterest)
    





