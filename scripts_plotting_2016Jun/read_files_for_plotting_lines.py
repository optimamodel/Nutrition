# -*- coding: utf-8 -*-
"""
Created on Tue Jun 28 11:31:42 2016

@author: ruth
"""
import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(moduleDir)
import optimisation
import pickle
import numpy as np

# read the optimal budget allocations from file
filename = '../Results2016Jun/Bangladesh/deaths/v5/Bangladesh_cascade_deaths_v5_1.0.pkl'
infile = open(filename, 'rb')
deathsOptimumAllocation = pickle.load(infile)
infile.close()
filename = '../Results2016Jun/Bangladesh/stunting/v5/Bangladesh_cascade_stunting_v5_1.0.pkl'
infile = open(filename, 'rb')
stuntingOptimumAllocation = pickle.load(infile)
infile.close()


timestep = 1./12. 
numsteps = 180
ages = ["<1 month", "1-5 months", "6-11 months", "12-23 months", "24-59 months"]
birthOutcomes = ["Pre-term SGA", "Pre-term AGA", "Term SGA", "Term AGA"]
wastingList = ["normal", "mild", "moderate", "high"]
stuntingList = ["normal", "mild", "moderate", "high"]
breastfeedingList = ["exclusive", "predominant", "partial", "none"]
keyList = [ages, birthOutcomes, wastingList, stuntingList, breastfeedingList]
ageGroupSpans = [1., 5., 6., 12., 36.] # number of months in each age group
agingRateList = [1./1., 1./5., 1./6., 1./12., 1./36.] # fraction of people aging out per MONTH (WARNING use ageSpans to define this)
numModelSteps = 180

# NATIONAL
dataSpreadsheetName = '../input_spreadsheets/Bangladesh/InputForCode_Bangladesh.xlsx'
thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, timestep, numModelSteps, ages, birthOutcomes, wastingList, stuntingList, breastfeedingList, ageGroupSpans, agingRateList)
initialAllocation = thisOptimisation.getInitialAllocationDictionary()

# run models and save output 
baseline = thisOptimisation.oneModelRunWithOutput(initialAllocation)
optimiseDeaths = thisOptimisation.oneModelRunWithOutput(deathsOptimumAllocation)
optimiseStunting = thisOptimisation.oneModelRunWithOutput(stuntingOptimumAllocation)

# GET Y AXIS FOR NUMBER OF DEATHS
numberOfDeaths_baseline = []
numberOfDeaths_optimiseDeaths = []
numberOfDeaths_optimiseStunting = []
numberOfDeaths_baseline.append(baseline[0].getTotalCumulativeDeaths())
numberOfDeaths_optimiseDeaths.append(optimiseDeaths[0].getTotalCumulativeDeaths())
numberOfDeaths_optimiseStunting.append(optimiseStunting[0].getTotalCumulativeDeaths())
# do this way due to weird differences in array([]) output
for model in range(1, 13):
    difference = baseline[model].getTotalCumulativeDeaths() - baseline[model - 1].getTotalCumulativeDeaths()
    numberOfDeaths_baseline.append(difference)
    
    difference = optimiseDeaths[model].getTotalCumulativeDeaths() - optimiseDeaths[model - 1].getTotalCumulativeDeaths()
    numberOfDeaths_optimiseDeaths.append(difference)    
    
    difference = optimiseStunting[model].getTotalCumulativeDeaths() - optimiseStunting[model - 1].getTotalCumulativeDeaths()
    numberOfDeaths_optimiseStunting.append(difference) 
for model in range(13, len(baseline)):
    difference = baseline[model].getTotalCumulativeDeaths()[0] - baseline[model - 1].getTotalCumulativeDeaths()[0]
    numberOfDeaths_baseline.append(difference) 
    
    difference = optimiseDeaths[model].getTotalCumulativeDeaths()[0] - optimiseDeaths[model - 1].getTotalCumulativeDeaths()[0]
    numberOfDeaths_optimiseDeaths.append(difference)    
    
    difference = optimiseStunting[model].getTotalCumulativeDeaths()[0] - optimiseStunting[model - 1].getTotalCumulativeDeaths()[0]
    numberOfDeaths_optimiseStunting.append(difference) 

numberOfDeaths_baseline[12] = numberOfDeaths_baseline[12][0]
numberOfDeaths_optimiseDeaths[12] = numberOfDeaths_optimiseDeaths[12][0]
numberOfDeaths_optimiseStunting[12] = numberOfDeaths_optimiseStunting[12][0]


# GET Y AXIS FOR FRACTION OF CHILDREN STUNTED
stuntingPrev_baseline = []
stuntingPrev_optimiseDeaths = []
stuntingPrev_optimiseStunting = []
for model in range(0, len(baseline)):
    stuntingPrev_baseline.append(baseline[model].getTotalStuntedFraction())
    stuntingPrev_optimiseDeaths.append(optimiseDeaths[model].getTotalStuntedFraction())
    stuntingPrev_optimiseStunting.append(optimiseStunting[model].getTotalStuntedFraction())
    
# GET Y AXIS FOR NUMBER AGING OUT STUNTED
agingOutStunted_baseline = []
agingOutStunted_optimiseDeaths = []
agingOutStunted_optimiseStunting = []
agingOutStunted_baseline.append(baseline[0].getCumulativeAgingOutStunted())
agingOutStunted_optimiseDeaths.append(optimiseDeaths[0].getCumulativeAgingOutStunted())
agingOutStunted_optimiseStunting.append(optimiseStunting[0].getCumulativeAgingOutStunted())
for model in range(1, len(baseline)):
    difference = baseline[model].getCumulativeAgingOutStunted() - baseline[model - 1].getCumulativeAgingOutStunted()    
    agingOutStunted_baseline.append(difference)
    difference = optimiseDeaths[model].getCumulativeAgingOutStunted() - optimiseDeaths[model - 1].getCumulativeAgingOutStunted() 
    agingOutStunted_optimiseDeaths.append(difference)
    difference = optimiseStunting[model].getCumulativeAgingOutStunted() - optimiseStunting[model - 1].getCumulativeAgingOutStunted() 
    agingOutStunted_optimiseStunting.append(difference)    


# MAKE THESE YEARLY
# DEATHS
numberOfDeaths_baselineYearly = []
numberOfDeaths_optimiseDeathsYearly = []
numberOfDeaths_optimiseStuntingYearly = []
numYears = len(baseline)/12
for i in range(0, numYears):
    step = i*12
    numberOfDeaths_baselineYearly.append( sum(numberOfDeaths_baseline[step:(12+step)]) )
    numberOfDeaths_optimiseDeathsYearly.append( sum(numberOfDeaths_optimiseDeaths[step:(12+step)]) )
    numberOfDeaths_optimiseStuntingYearly.append( sum(numberOfDeaths_optimiseStunting[step:(12+step)]) )
    
# STUNTING PREV
stuntingPrev_baselineYearly = []
stuntingPrev_optimiseDeathsYearly = []
stuntingPrev_optimiseStuntingYearly = []  
for i in range(0, numYears):
    step = i*12
    stuntingPrev_baselineYearly.append( np.average(stuntingPrev_baseline[step:(12+step)]) )
    stuntingPrev_optimiseDeathsYearly.append( np.average(stuntingPrev_optimiseDeaths[step:(12+step)]) )
    stuntingPrev_optimiseStuntingYearly.append( np.average(stuntingPrev_optimiseStunting[step:(12+step)]) )
    
# AGING OUT STUNTED
agingOutStunted_baselineYearly = []
agingOutStunted_optimiseDeathsYearly = []
agingOutStunted_optimiseStuntingYearly = []
numYears = len(baseline)/12
for i in range(0, 1):
    step = i*12
    agingOutStunted_baselineYearly.append( sum(agingOutStunted_baseline[step:(12+step)]) )
    agingOutStunted_optimiseDeathsYearly.append( sum(agingOutStunted_optimiseDeaths[step:(12+step)]) )
    agingOutStunted_optimiseStuntingYearly.append( sum(agingOutStunted_optimiseStunting[step:(12+step)]) ) 

for i in range(1, numYears):
    step = i*12
    agingOutStunted_baselineYearly.append( sum(agingOutStunted_baseline[step:(12+step)])[0] )
    agingOutStunted_optimiseDeathsYearly.append( sum(agingOutStunted_optimiseDeaths[step:(12+step)])[0] )
    agingOutStunted_optimiseStuntingYearly.append( sum(agingOutStunted_optimiseStunting[step:(12+step)])[0] )    
    