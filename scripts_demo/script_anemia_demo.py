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
spreadsheet = rootpath + 'input_spreadsheets/Bangladesh/2017Jan/InputForCode_Bangladesh.xlsx'
spreadsheetData = data.readSpreadsheet(spreadsheet, helper.keyList)
coverageList = np.arange(0,1,0.1)

# set all coverages to zero    
zeroCoverages = {}    
for i in range(0, len(spreadsheetData.interventionList)):
    intervention = spreadsheetData.interventionList[i]
    zeroCoverages[intervention] = 0

#  PREGNANT WOMEN 
interventionList = ['Antenatal micronutrient supplementation', 'IPTp']
pregnantFraction = {}
pregnantNumber = {}
for intervention in interventionList:
    pregnantFraction[intervention] = []
    pregnantNumber[intervention] = []
    for coverage in coverageList:

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
    plt.ylabel('anemia frac pregnant')
    plt.legend()
    plt.show()          