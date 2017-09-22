# -*- coding: utf-8 -*-
"""
Created on Thu Sep 21 15:08:03 2017

@author: ruth
"""

rootpath = '../'

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)

import data
from copy import deepcopy as dcp
import helper
import csv 
helper = helper.Helper()

def runModelGivenCoverage(intervention, coverage, spreadsheetData, zeroCoverages, outcome):
    numModelSteps = 14     
    model, derived, params = helper.setupModelDerivedParameters(spreadsheetData)
    # run the model for one year before updating coverages  
    timestepsPre = 1
    for t in range(timestepsPre):
        model.moveModelOneYear()  
    # set coverage    
    theseCoverages = dcp(zeroCoverages)  
    theseCoverages[intervention] = coverage
    if 'IFAS' in intervention:
        interventionMalaria = intervention + ' (malaria area)'
        theseCoverages[interventionMalaria] = coverage
    # update coverages after 1 year 
    model.updateCoverages(theseCoverages)
    # run the model for the remaining timesteps
    for t in range(numModelSteps - timestepsPre):
        model.moveModelOneYear()
    # return outcome
    return model.getOutcome(outcome)

spreadsheet = rootpath + 'input_spreadsheets/Bangladesh/2017Aug/InputForCode_Bangladesh.xlsx'
spreadsheetData = data.readSpreadsheet(spreadsheet, helper.keyList)
malariaFracList = [0.1, 0.5, 0.7, 1.0]
poorFracList = [0.1, 0.36, 0.7]
IPTpFracList = [0.0, 0.5, 0.9]
bedNetList = [0.0, 0.5, 0.9]
# set all coverages to zero    
zeroCoverages = {}    
for i in range(0, len(spreadsheetData.interventionList)):
    intervention = spreadsheetData.interventionList[i]
    zeroCoverages[intervention] = 0.


#  WOMEN OF REPRODUCTIVE AGE
fracAnemic = {}
interventionList = ['IFAS poor: school', 'IFAS poor: community', 'IFAS poor: hospital', 'IFAS not poor: school', 'IFAS not poor: community', 'IFAS not poor: hospital', 'IFAS not poor: retailer']
for intervention in interventionList:
    fracAnemic[intervention] = []
    for poor in poorFracList:
        thisData = dcp(spreadsheetData) 
        thisData.demographics['fraction food insecure (default poor)'] = poor
        thisCov = dcp(zeroCoverages)
        thisCov['Long-lasting insecticide-treated bednets'] = 0.95
        thisOutcome = runModelGivenCoverage(intervention, 0.95, thisData, thisCov, 'anemia frac WRA')
        fracAnemic[intervention].append(thisOutcome)
# put into csv
outfilename = 'WRA.csv'
header1 = ['fraction poor'] + poorFracList
header2 = ['intervention']
with open(outfilename, "wb") as f:
    writer = csv.writer(f)
    writer.writerow(header1)
    writer.writerow(header2)
    for intervention in interventionList:
        writer.writerow([intervention] + fracAnemic[intervention])   
        
        
#   PREGNANT WOMEN
fracAnemic = {}
interventionList = ['Multiple micronutrient supplementation', 'Multiple micronutrient supplementation (malaria area)', 'Iron and folic acid supplementation for pregnant women', 'Iron and folic acid supplementation for pregnant women (malaria area)']
for intervention in interventionList:
    fracAnemic[intervention] = {}
    for malaria in malariaFracList:
        fracAnemic[intervention][malaria] = []
        for cov in IPTpFracList:
            thisData = dcp(spreadsheetData) 
            thisData.demographics['fraction at risk of malaria'] = malaria
            thisData.fracExposedMalaria = malaria
            thisCov = dcp(zeroCoverages)
            thisCov['IPTp'] = cov
            thisOutcome = runModelGivenCoverage(intervention, 0.95, thisData, thisCov, 'anemia frac pregnant')
            fracAnemic[intervention][malaria].append(thisOutcome)        
# put into csv
outfilename = 'PW.csv'
header1 = ['IPTp coverage'] + IPTpFracList
header2 = ['intervention']
with open(outfilename, "wb") as f:
    writer = csv.writer(f)
    for malaria in malariaFracList:
        writer.writerow(['malaria frac', malaria])
        writer.writerow(header1)
        writer.writerow(header2)
        for intervention in interventionList:
            writer.writerow([intervention] + fracAnemic[intervention][malaria])
        
        
        
    
# CHILDREN
fracAnemic = {}
interventionList = ['Public provision of complementary foods with iron', 'Public provision of complementary foods with iron (malaria area)', 'Sprinkles', 'Sprinkles (malaria area)']
for intervention in interventionList:
    fracAnemic[intervention] = {}
    for malaria in malariaFracList:
        fracAnemic[intervention][malaria] = []
        for cov in bedNetList:
            thisData = dcp(spreadsheetData) 
            thisData.demographics['fraction at risk of malaria'] = malaria
            thisData.fracExposedMalaria = malaria
            thisCov = dcp(zeroCoverages)
            thisCov['Long-lasting insecticide-treated bednets'] = cov
            thisOutcome = runModelGivenCoverage(intervention, 0.95, thisData, thisCov, 'anemia frac children')
            fracAnemic[intervention][malaria].append(thisOutcome)        
# put into csv
outfilename = 'children.csv'
header1 = ['bed net coverage'] + bedNetList
header2 = ['intervention']
with open(outfilename, "wb") as f:
    writer = csv.writer(f)
    for malaria in malariaFracList:
        writer.writerow(['malaria frac', malaria])
        writer.writerow(header1)
        writer.writerow(header2)
        for intervention in interventionList:
            writer.writerow([intervention] + fracAnemic[intervention][malaria])
        



    
    