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


numModelSteps = 15 
spreadsheet = rootpath + 'input_spreadsheets/Bangladesh/2017Aug/InputForCode_Bangladesh.xlsx'
spreadsheetData = data.readSpreadsheet(spreadsheet, helper.keyList)
coverageList = np.arange(0, 1.1, 0.1)

# set all coverages to zero    
zeroCoverages = {}    
for i in range(0, len(spreadsheetData.interventionList)):
    intervention = spreadsheetData.interventionList[i]
    zeroCoverages[intervention] = 0

#  PREGNANT WOMEN 
interventionList = ['Balanced energy-protein supplementation', 'Multiple micronutrient supplementation', 'Multiple micronutrient supplementation (malaria area)', 'Iron and folic acid supplementation for pregnant women', 'Iron and folic acid supplementation for pregnant women (malaria area)', 'IPTp']
pregnantFraction = {}
for intervention in interventionList:
    pregnantFraction[intervention] = []
    for coverage in coverageList:
        print coverage
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
            model.moveOneTimeStep()
        # get outcome
        pregnantFraction[intervention].append(model.getOutcome('anemia frac pregnant'))
    # plot for this intervention
    plt.plot(coverageList, pregnantFraction[intervention], label = intervention)
    plt.xlabel('coverage')
    plt.ylabel('anemia prevalence pregnant women')
plt.legend(loc='lower left')
plt.show()          
  
    
    
##  WOMEN OF REPRODUCTIVE AGE
#interventionList = ['IFA poor: school', 'IFA poor: community', 'IFA poor: hospital', 'IFA not poor: school', 'IFA not poor: community', 'IFA not poor: hospital', 'IFA not poor: retailer']   
## modify coverages to simulation saturations for demo    
#coverageListList = [] 
#thisList = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]   
#coverageListList.append(thisList)
#thisList = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.7, 0.7, 0.7]   
#coverageListList.append(thisList)
#thisList = [0, 0.1, 0.2, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3]   
#coverageListList.append(thisList)
#thisList = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]   
#coverageListList.append(thisList)
#thisList = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]   
#coverageListList.append(thisList)
#thisList = [0, 0.1, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2]   
#coverageListList.append(thisList)
#thisList = [0, 0.1, 0.2, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3]   
#coverageListList.append(thisList)
#
#lineStyles = ['-', '-', '-', '--', '--', '--','--']
#colours = ['b', 'm', 'k', 'b', 'm', 'k', 'g']
#
#anemiaPrev = {}
#i = 0
#for intervention in interventionList:
#    anemiaPrev[intervention] = []
#    theseCoverages = coverageListList[i]
#    for coverage in theseCoverages:
#        model, derived, params = helper.setupModelDerivedParameters(spreadsheetData)
#        # run the model for one year before updating coverages  
#        timestepsPre = 1
#        for t in range(timestepsPre):
#            model.moveModelOneYear()  
#        # set coverage    
#        theseCoverages = dcp(zeroCoverages)  
#        theseCoverages[intervention] = coverage
#        # update coverages after 1 year     
#        model.updateCoverages(theseCoverages)
#        # run the model for the remaining timesteps
#        for t in range(numModelSteps - timestepsPre):
#            model.moveOneTimeStep()
#        # get outcome
#        anemiaPrev[intervention].append(model.getOutcome('anemia frac WRA'))
#    # plot for this intervention
#    plt.plot(coverageList, anemiaPrev[intervention], label = intervention, linestyle = lineStyles[i], color = colours[i])
#    plt.xlabel('coverage')
#    plt.ylabel('anemia prevalence WRA')
#    i += 1
#plt.legend(loc = 'upper center', bbox_to_anchor=(0.5, -0.15), ncol=7, fancybox=True, shadow=True) 
##plt.legend(loc='lower left')
#plt.show()              
#
#
##  FOOD FORTIFICATION
#
#interventionList = ['Food fortification maize', 'Food fortification rice', 'Food fortification wheat']
#coverageListList = [] 
#thisList = [0, 0.1, 0.2, 0.3, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4]   
#coverageListList.append(thisList)
#thisList = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.8, 0.8]   
#coverageListList.append(thisList)
#thisList = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.6, 0.6, 0.6, 0.6]   
#coverageListList.append(thisList)
#
#i = 0
#everyoneAnemicFraction = {}
#for intervention in interventionList:
#    everyoneAnemicFraction[intervention] = []
#    for coverage in coverageListList[i]:
#        model, derived, params = helper.setupModelDerivedParameters(spreadsheetData)
#        # run the model for one year before updating coverages  
#        timestepsPre = 1
#        for t in range(timestepsPre):
#            model.moveModelOneYear()  
#        # set coverage    
#        theseCoverages = dcp(zeroCoverages)  
#        theseCoverages[intervention] = coverage
#        # update coverages after 1 year     
#        model.updateCoverages(theseCoverages)
#        # run the model for the remaining timesteps
#        for t in range(numModelSteps - timestepsPre):
#            model.moveOneTimeStep()
#        # get outcome
#        everyoneAnemicFraction[intervention].append(model.getOutcome('anemia frac everyone'))
#    # plot for this intervention
#    plt.plot(coverageList, everyoneAnemicFraction[intervention], label = intervention)
#    plt.xlabel('coverage')
#    plt.ylabel('anemia prevalence everyone')
#    i += 1
#plt.legend(loc='lower left')
#plt.show()          
#   
#
#    