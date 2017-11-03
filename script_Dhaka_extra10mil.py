# -*- coding: utf-8 -*-
"""
Created on Mon Dec  5 14:39:40 2016

@author: ruth
"""

import optimisation
import pickle
import csv

country = 'Bangladesh'
date = '2016Oct'
optimise = 'stunting'
haveFixedProgCosts = True
numModelSteps = 180
MCSampleSize = 25
spreadsheet = 'input_spreadsheets/' + country + '/' + date + '/subregionSpreadsheets/Dhaka.xlsx'
resultsFileStem = 'ResultsDhaka10mil/' +date+ '/' + optimise + '/'

# optimise with current budget plus $10 million
thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, optimise, resultsFileStem)
currentBudget = thisOptimisation.getTotalInitialBudget()
totalBudget = currentBudget + 10000000
filename = 'Dhaka_extra_10mil'
thisOptimisation.performSingleOptimisationForGivenTotalBudget(MCSampleSize, totalBudget, filename, haveFixedProgCosts)

# run model for the optimum allocation of the above
infile = open(resultsFileStem+'_'+filename+'.pkl', 'rb')
thisAllocation = pickle.load(infile)
infile.close()
modelOutput = thisOptimisation.oneModelRunWithOutput(thisAllocation)

numStuntCases = modelOutput[numModelSteps-1].getOutcome('stunting')

with open(resultsFileStem+filename + '.csv', "wb") as f:
    writer = csv.writer(f)
    writer.writerow([numStuntCases])

