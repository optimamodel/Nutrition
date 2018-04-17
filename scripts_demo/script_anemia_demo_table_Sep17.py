# -*- coding: utf-8 -*-
"""
Created on Tue Sep 19 16:42:54 2017

@author: ruth
"""

rootpath = '../'

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)

from nutrition import data
from copy import deepcopy as dcp
from old_files import helper

helper = helper.Helper()

def runModelGivenCoverage(intervention, coverage, spreadsheetData, zeroCoverages):
    interventionsCombine = ['Public provision of complementary foods with iron', 'Sprinkles', 'Multiple micronutrient supplementation', 'Iron and folic acid supplementation for pregnant women']    
    numModelSteps = 14     
    model, derived, params = helper.setupModelDerivedParameters(spreadsheetData)
    # run the model for one year before updating coverages  
    timestepsPre = 1
    for t in range(timestepsPre):
        model.moveModelOneYear()  
    # set coverage    
    theseCoverages = dcp(zeroCoverages)  
    theseCoverages[intervention] = coverage
    # scale up malaria area part of IFAS interventions also    
    if 'IFAS' in intervention:
        interventionMalaria = intervention + ' (malaria area)'
        theseCoverages[interventionMalaria] = coverage
    if 'IFAS' in intervention and 'retailer' not in intervention:
        if 'poor' in intervention:
            interventionNotPoor = intervention.replace('poor', 'not poor')
            interventionNotPoorMalaria = interventionNotPoor + ' (malaria area)'
            theseCoverages[interventionNotPoor] = coverage
            theseCoverages[interventionNotPoorMalaria] = coverage
    if any(this in intervention for this in interventionsCombine):
            interventionMalaria = intervention + ' (malaria area)'
            theseCoverages[interventionMalaria] = coverage
    # update coverages after 1 year 
    model.updateCoverages(theseCoverages)
    # run the model for the remaining timesteps
    for t in range(numModelSteps - timestepsPre):
        model.moveModelOneYear()
    # return outcome
    return model
    
    
spreadsheet = rootpath + 'input_spreadsheets/Bangladesh/2017Aug/InputForCode_Bangladesh.xlsx'
spreadsheetData = data.readSpreadsheet(spreadsheet, helper.keyList)

zeroCoverages = {}    
for i in range(0, len(spreadsheetData.interventionList)):
    intervention = spreadsheetData.interventionList[i]
    zeroCoverages[intervention] = 0.
# set bed nets and IPTp coverage to malaria prevalence so that constraints are met for certain interventions    
zeroCoverages['Long-lasting insecticide-treated bednets'] = 0.1
zeroCoverages['IPTp'] = 0.1 
coverage95 = 0.95   

# BASELINE (this is all interventions at zero)
baseline = []
baseline.append('Baseline')
numModelSteps = 14     
model = runModelGivenCoverage('IPTp', 0.0, spreadsheetData, zeroCoverages)
baseline.append(model.getOutcome('thrive')) 
baseline.append(model.getOutcome('deaths children')) 
baseline.append(model.getOutcome('deaths PW')) 
baseline.append(model.getOutcome('anemia frac pregnant')) 
baseline.append(model.getOutcome('anemia frac WRA')) 
baseline.append(model.getOutcome('anemia frac children'))   

# EVERYTHING ELSE
interventionsCombine = ['Public provision of complementary foods with iron', 'Sprinkles', 'Multiple micronutrient supplementation', 'Iron and folic acid supplementation for pregnant women']
output = {}    
for intervention in spreadsheetData.interventionList:
    #combining IFAS interventions in malaria and non-malaria areas, poor and not-poor    
    if 'IFAS' in intervention and 'malaria area' in intervention:
        continue
    if 'IFAS' in intervention and 'retailer' not in intervention:
        if 'not poor' in intervention:
            continue
    if any(this in intervention for this in interventionsCombine) and 'malaria area' in intervention:
        continue
        
    output[intervention] = []
    output[intervention].append(intervention)
    model = runModelGivenCoverage(intervention, coverage95, spreadsheetData, zeroCoverages)
    output[intervention].append(model.getOutcome('thrive'))
    output[intervention].append(model.getOutcome('deaths children'))
    output[intervention].append(model.getOutcome('deaths PW'))
    output[intervention].append(model.getOutcome('anemia frac pregnant'))
    output[intervention].append(model.getOutcome('anemia frac WRA'))
    output[intervention].append(model.getOutcome('anemia frac children'))
    
    
# ALL IFAS INTERVENTIONS AT 95%
allIFAS = []
allIFAS.append('all IFAS WRA')    
coverage = dcp(zeroCoverages)    
for intervention in spreadsheetData.interventionList:
    if 'IFAS' in intervention:
        coverage[intervention] = coverage95
numModelSteps = 14     
model, derived, params = helper.setupModelDerivedParameters(spreadsheetData)
model.moveModelOneYear()  
model.updateCoverages(coverage)
for t in range(numModelSteps - 1):
    model.moveModelOneYear()  
allIFAS.append(model.getOutcome('thrive')) 
allIFAS.append(model.getOutcome('deaths children')) 
allIFAS.append(model.getOutcome('deaths PW')) 
allIFAS.append(model.getOutcome('anemia frac pregnant')) 
allIFAS.append(model.getOutcome('anemia frac WRA')) 
allIFAS.append(model.getOutcome('anemia frac children')) 


# ALL FORTIFICATION INTERVENTIONS AT 95%
allfoodFort = []
allfoodFort.append('all food fortification')    
coverage = dcp(zeroCoverages)    
for intervention in spreadsheetData.interventionList:
    if 'fortification' in intervention:
        coverage[intervention] = coverage95
numModelSteps = 14     
model, derived, params = helper.setupModelDerivedParameters(spreadsheetData)
model.moveModelOneYear()  
model.updateCoverages(coverage)
for t in range(numModelSteps - 1):
    model.moveModelOneYear()  
allfoodFort.append(model.getOutcome('thrive')) 
allfoodFort.append(model.getOutcome('deaths children')) 
allfoodFort.append(model.getOutcome('deaths PW')) 
allfoodFort.append(model.getOutcome('anemia frac pregnant')) 
allfoodFort.append(model.getOutcome('anemia frac WRA')) 
allfoodFort.append(model.getOutcome('anemia frac children'))       
        
   
header = ['scenario', 'thrive','deaths children','deaths PW', 'anemia prev PW', 'anemia prev WRA', 'anemia prev children']   
import csv   
outfilename = 'anemia.csv'
with open(outfilename, "wb") as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerow(baseline)
    for intervention in spreadsheetData.interventionList:
        if 'IFAS' in intervention and 'malaria area' in intervention:
            continue
        if 'IFAS' and 'retailer' not in intervention:
            if 'not poor' in intervention:
                continue
        if any(this in intervention for this in interventionsCombine) and 'malaria area' in intervention:
            continue    
        writer.writerow(output[intervention])    
    writer.writerow(allIFAS)
    writer.writerow(allfoodFort)



    