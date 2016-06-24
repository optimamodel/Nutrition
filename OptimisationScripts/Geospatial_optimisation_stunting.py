# -*- coding: utf-8 -*-
"""
Created on Fri Jun 24 14:28:54 2016

@author: ruth
"""
import optimisation as optimisation

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
MCSampleSize = 25
optimise = 'stunting'

spreadsheet0 = 'InputForCode_Bangladesh.xlsx'
spreadsheet1 = 'InputForCode_Bangladesh.xlsx'
spreadsheet2 = 'InputForCode_Bangladesh.xlsx'
spreadsheet3 = 'InputForCode_Bangladesh.xlsx'
spreadsheet4 = 'InputForCode_Bangladesh.xlsx'
spreadsheet5 = 'InputForCode_Bangladesh.xlsx'
spreadsheet6 = 'InputForCode_Bangladesh.xlsx'
spreadsheetList = [spreadsheet0, spreadsheet1, spreadsheet2, spreadsheet3, spreadsheet4, spreadsheet5, spreadsheet6]

for i in range(0, len(spreadsheetList)):
    spreadsheet = spreadsheetList[i]
    thisOptimisation = optimisation.Optimisation(spreadsheet, timestep, numModelSteps, ages, birthOutcomes, wastingList, stuntingList, breastfeedingList, ageGroupSpans, agingRateList)
    filename = 'Bangladesh_geospatial_stunting_region_'+str(i)
    thisOptimisation.performSingleOptimisation(optimise, MCSampleSize, filename)


