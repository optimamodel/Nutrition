# -*- coding: utf-8 -*-
"""
Created on Thu Dec 21 15:30:44 2017

@author: ruth
"""

rootpath = '../'

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)

import data
import helper
import csv
from copy import deepcopy as dcp
thisHelper = helper.Helper()
spreadsheet = rootpath + 'input_spreadsheets/Bangladesh/2017Nov/InputForCode_Bangladesh.xlsx'
thisData = data.readSpreadsheet(spreadsheet, thisHelper.keyList)
m,d,p = thisHelper.setupModelDerivedParameters(thisData)
numSteps = 13

def getRowForBundledInterventions(name, thisBundle, ref_cov):
    covDict = dcp(ref_cov)
    for intervention in thisBundle:
        covDict[intervention] = 0.95    
    m,d,p = thisHelper.setupModelDerivedParameters(thisData)
    m.moveModelOneYear()
    m.updateCoverages(covDict)
    for i in range(numSteps):
        m.moveModelOneYear()
    row = [name, m.getOutcome('thrive'), m.getOutcome('stunting prev'), m.getTotalCumulativeDeathsChildren(),  m.getTotalCumulativeDeathsPW(), m.listOfAgeCompartments[0].getCumulativeDeaths(), m.cumulativeBirths, m.getOutcome('anemia frac pregnant'), m.getOutcome('anemia frac WRA'), m.getOutcome('anemia frac children'), m.getOutcome('wasting_prev'), m.getOutcome('MAM_prev'), m.getOutcome('SAM_prev')]
    return row

header = ['scenario', 'thrive', 'stunting prev', 'deaths: child', 'deaths: PW', 'deaths: neonatal', 'cumulative births', 'anemia: PW', 'anemia: WRA', 'anemia: children', 'wasting: all', 'wasting: MAM', 'wasting: SAM']   

# make lists of intervention bundles
fortificationInterventions = ['IFA fortification of wheat flour', 'IFA fortification of maize', 'IFA fortification of rice', 'Iron and iodine fortification of salt']
allIFAS = []
for intervention in thisData.interventionCompleteList:
    if 'IFAS' in intervention:
        allIFAS.append(intervention)
wastingInterventions = ['Treatment of MAM', 'Treatment of SAM']  
leaveAtBaselineCov = ['IPTp', 'Long-lasting insecticide-treated bednets', 'Family Planning']
for intervention in thisData.interventionCompleteList:
    if 'WASH' in intervention:
        leaveAtBaselineCov.append(intervention)
PPCF_iron = ['Public provision of complementary foods with iron', 'Public provision of complementary foods with iron (malaria area)']
sprinkles = ['Sprinkles', 'Sprinkles (malaria area)']
MMS = ['Multiple micronutrient supplementation (malaria area)', 'Multiple micronutrient supplementation']
IFAS_PW = ['Iron and folic acid supplementation for pregnant women (malaria area)', 'Iron and folic acid supplementation for pregnant women']
school = ['IFAS poor: school', 'IFAS not poor: school', 'IFAS poor: school (malaria area)', 'IFAS not poor: school (malaria area)']
hospital = ['IFAS poor: hospital', 'IFAS not poor: hospital', 'IFAS poor: hospital (malaria area)', 'IFAS not poor: hospital (malaria area)']
community = ['IFAS poor: community', 'IFAS not poor: community', 'IFAS poor: community (malaria area)', 'IFAS not poor: community (malaria area)']
retailer = ['IFAS not poor: retailer', 'IFAS not poor: retailer (malaria area)']
removeThese = PPCF_iron + sprinkles + MMS + IFAS_PW + school + hospital + community + retailer


# make a zero dictionary
zero_cov = {}
for intervention in thisData.interventionCompleteList:
    if intervention in leaveAtBaselineCov:
        zero_cov[intervention] = thisData.coverage[intervention]
    else:    
        zero_cov[intervention] = 0.0
    
rows = []  
rows2 = []  
    
# run for zero coverage
m,d,p = thisHelper.setupModelDerivedParameters(thisData)
m.moveModelOneYear()
m.updateCoverages(zero_cov)
for i in range(numSteps):
    m.moveModelOneYear()
row1 = ['Reference', m.getOutcome('thrive'), m.getOutcome('stunting prev'), m.getTotalCumulativeDeathsChildren(),  m.getTotalCumulativeDeathsPW(), m.listOfAgeCompartments[0].getCumulativeDeaths(), m.cumulativeBirths, m.getOutcome('anemia frac pregnant'), m.getOutcome('anemia frac WRA'), m.getOutcome('anemia frac children'), m.getOutcome('wasting_prev'), m.getOutcome('MAM_prev'), m.getOutcome('SAM_prev')]
rows.append(row1)
rows2.append(row1)

#remove some interventions from complete list
newInterventionList = dcp(thisData.interventionCompleteList)
for intervention in thisData.interventionCompleteList:
    if intervention in removeThese:
        newInterventionList.remove(intervention)
    if 'with bed nets' in intervention:
        newInterventionList.remove(intervention)


for intervention in newInterventionList:
    m,d,p = thisHelper.setupModelDerivedParameters(thisData)
    m.moveModelOneYear()
    covDict = dcp(zero_cov)
    covDict[intervention] = 0.95
    m.updateCoverages(covDict)
    for i in range(numSteps):
        m.moveModelOneYear()
    row = [intervention + ' 95%', m.getOutcome('thrive'), m.getOutcome('stunting prev'), m.getTotalCumulativeDeathsChildren(),  m.getTotalCumulativeDeathsPW(), m.listOfAgeCompartments[0].getCumulativeDeaths(), m.cumulativeBirths, m.getOutcome('anemia frac pregnant'), m.getOutcome('anemia frac WRA'), m.getOutcome('anemia frac children'), m.getOutcome('wasting_prev'), m.getOutcome('MAM_prev'), m.getOutcome('SAM_prev')]
    rows.append(row)
    
# fortification bundle
row = getRowForBundledInterventions('all fortification 95%', fortificationInterventions, zero_cov)
rows.append(row)

# IFAS bundle
row = getRowForBundledInterventions('all IFAS 95%', allIFAS, zero_cov)
rows.append(row)

# wasting bundle
row = getRowForBundledInterventions('MAM + SAM 95%', wastingInterventions, zero_cov)
rows.append(row)

# PPCF + iron bundle
row = getRowForBundledInterventions('Public provision of complementary foods with iron 95%',PPCF_iron , zero_cov)
rows.append(row)

# sprinkles
row = getRowForBundledInterventions('Sprinkles 95%', sprinkles, zero_cov)
rows.append(row)

# MMS
row = getRowForBundledInterventions('Multiple micronutrient supplementation 95%', MMS, zero_cov)
rows.append(row)

# IFAS PW
row = getRowForBundledInterventions('Iron and folic acid supplementation for pregnant women 95%', IFAS_PW, zero_cov)
rows.append(row)

# school
row = getRowForBundledInterventions('IFAS: school 95%',school , zero_cov)
rows.append(row)

# community
row = getRowForBundledInterventions('IFAS: community 95%', community, zero_cov)
rows.append(row)

# hospital
row = getRowForBundledInterventions('IFAS: hospital 95%', hospital, zero_cov)
rows.append(row)

# retailer
row = getRowForBundledInterventions('IFAS: retailer 95%', retailer, zero_cov)
rows.append(row)



    
    
# also get % difference  
for row in rows:      
    rowVals = row[1:]        
    rowPercent = [row[0]]
    i = 1        
    for val in rowVals:
        percentChange = (val - row1[i]) / row1[i]
        i += 1
        rowPercent.append(percentChange)
    rows2.append(rowPercent)    
            
        
    
    
print 'writing file...'    
filename = 'demo_all_interventions_absolute.csv'
with open(filename, 'wb') as f:
    w = csv.writer(f)
    w.writerow(header)
    for row in rows:
        w.writerow(row)
        
    
print 'writing file 2 ...'    
filename = 'demo_all_interventions_percent_change.csv'
with open(filename, 'wb') as f:
    w = csv.writer(f)
    w.writerow(header)
    for row in rows2:
        w.writerow(row)        