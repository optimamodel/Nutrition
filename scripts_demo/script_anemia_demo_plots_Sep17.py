# -*- coding: utf-8 -*-
"""
Created on Tue Jun 13 16:02:51 2017

@author: ruth
"""
rootpath = '../'

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)

import data
from copy import deepcopy as dcp
import helper
import matplotlib.pyplot as plt
import numpy as np
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
    # update coverages after 1 year 
    model.updateCoverages(theseCoverages)
    # run the model for the remaining timesteps
    for t in range(numModelSteps - timestepsPre):
        model.moveModelOneYear()
    # return outcome
    return model.getOutcome(outcome)


spreadsheet = rootpath + 'input_spreadsheets/Bangladesh/2017Aug/InputForCode_Bangladesh.xlsx'
spreadsheetData = data.readSpreadsheet(spreadsheet, helper.keyList)
coverageList = np.arange(0, 1.1, 0.2)
malariaFracList = [0.0, 0.5, 0.7, 1.0]

# set all coverages to zero    
zeroCoverages = {}    
for i in range(0, len(spreadsheetData.interventionList)):
    intervention = spreadsheetData.interventionList[i]
    zeroCoverages[intervention] = 0.
   
    

#    
#
###  PREGNANT WOMEN 
#interventionList = ['Multiple micronutrient supplementation', 'Multiple micronutrient supplementation (malaria area)', 'Iron and folic acid supplementation for pregnant women', 'Iron and folic acid supplementation for pregnant women (malaria area)', 'IPTp']
#
#for malaria in malariaFracList:
#    print 'malaria:  ', malaria
#    thisData = dcp(spreadsheetData) 
#    thisData.demographics['fraction at risk of malaria'] = malaria
#    thisData.fracExposedMalaria = malaria
#    fracAnemicPreg = {}
#    for intervention in interventionList:
#        fracAnemicPreg[intervention] = []
#        for coverage in coverageList:
#            thisCov = dcp(zeroCoverages)
#            if 'IPTp' not in intervention:
#                thisCov['IPTp'] = 0.5
#            thisOutcome = runModelGivenCoverage(intervention, coverage, thisData, thisCov, 'anemia frac pregnant')
#            fracAnemicPreg[intervention].append(thisOutcome)
#        # plot for this intervention
#        plt.plot(coverageList, fracAnemicPreg[intervention], label = intervention)
#    plt.xlabel('coverage')
#    plt.ylabel('anemia prevalence pregnant women')
#    plt.ylim([0,1])
#    plt.legend(loc = 'upper center', bbox_to_anchor=(0.5, -0.15), ncol=1, fancybox=True, shadow=True)
#    plt.show()  
    
    
##  WOMEN OF REPRODUCTIVE AGE
#interventionList = ['IFAS poor: school', 'IFAS poor: community', 'IFAS poor: hospital', 'IFAS not poor: school', 'IFAS not poor: community', 'IFAS not poor: hospital', 'IFAS not poor: retailer', 'IFAS poor: school (malaria area)', 'IFAS poor: community (malaria area)', 'IFAS poor: hospital (malaria area)', 'IFAS not poor: school (malaria area)', 'IFAS not poor: community (malaria area)', 'IFAS not poor: hospital (malaria area)', 'IFAS not poor: retailer (malaria area)']
#for malaria in malariaFracList:
#    print 'malaria:  ', malaria
#    thisData = dcp(spreadsheetData) 
#    thisData.demographics['fraction at risk of malaria'] = malaria
#    thisData.fracExposedMalaria = malaria
#    fracAnemic = {}
#    for intervention in interventionList:
#        fracAnemic[intervention] = []
#        for coverage in coverageList:
#            thisCov = dcp(zeroCoverages)
#            thisCov['Long-lasting insecticide-treated bednets'] = 0.5
#            thisOutcome = runModelGivenCoverage(intervention, coverage, thisData, thisCov, 'anemia frac WRA')
#            fracAnemic[intervention].append(thisOutcome)
#        # plot for this intervention
#        plt.plot(coverageList, fracAnemic[intervention], label = intervention)
#    plt.xlabel('coverage')
#    plt.ylabel('anemia prevalence women of reproductive age')
#    plt.ylim([0,1])
#    plt.legend(loc = 'upper center', bbox_to_anchor=(0.5, -0.15), ncol=1, fancybox=True, shadow=True)
#    plt.show()  


## CHILDREN 
#interventionList = ['Public provision of complementary foods with iron', 'Public provision of complementary foods with iron (malaria area)', 'Sprinkles', 'Sprinkles (malaria area)']
#for malaria in malariaFracList:
#    print 'malaria:  ', malaria
#    thisData = dcp(spreadsheetData) 
#    thisData.demographics['fraction at risk of malaria'] = malaria
#    thisData.fracExposedMalaria = malaria
#    fracAnemic = {}
#    for intervention in interventionList:
#        fracAnemic[intervention] = []
#        for coverage in coverageList:
#            thisCov = dcp(zeroCoverages)
#            thisCov['Long-lasting insecticide-treated bednets'] = 0.5
#            thisOutcome = runModelGivenCoverage(intervention, coverage, thisData, thisCov, 'anemia frac children')
#            fracAnemic[intervention].append(thisOutcome)
#        # plot for this intervention
#        plt.plot(coverageList, fracAnemic[intervention], label = intervention)
#    plt.xlabel('coverage')
#    plt.ylabel('anemia prevalence children')
#    plt.ylim([0.2,0.8])
#    plt.legend(loc = 'upper center', bbox_to_anchor=(0.5, -0.15), ncol=1, fancybox=True, shadow=True)
#    plt.show()  



# GENERAL POPULATION
subsistenceList = [0, 0.3, 0.5, 0.7]
interventionList = ['Iron fortification of wheat flour', 'Iron fortification of maize', 'Iron fortification of rice', 'Iron and iodine fortification of salt']
for frac in subsistenceList:
    print 'frac:  ', frac
    thisData = dcp(spreadsheetData) 
    thisData.demographics['fraction of subsistence farming'] = frac
    fracAnemic = {}
    for intervention in interventionList:
        fracAnemic[intervention] = []
        for coverage in coverageList:
            thisCov = dcp(zeroCoverages)
            thisOutcome = runModelGivenCoverage(intervention, coverage, thisData, thisCov, 'anemia frac everyone')
            fracAnemic[intervention].append(thisOutcome)
        # plot for this intervention
        plt.plot(coverageList, fracAnemic[intervention], label = intervention)
    plt.xlabel('coverage')
    plt.ylabel('anemia prevalence general population')
    plt.ylim([0.3,0.5])
    plt.legend(loc = 'upper center', bbox_to_anchor=(0.5, -0.15), ncol=1, fancybox=True, shadow=True)
    plt.show()  