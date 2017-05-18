# -*- coding: utf-8 -*-
"""
Created on Thu May 18 11:51:19 2017

@author: ruth
"""
import matplotlib.pyplot as plt
import numpy as np
from copy import deepcopy as dcp
import helper
import data
helper = helper.Helper()

numModelSteps = 180
spreadsheet = 'input_spreadsheets/Bangladesh/2016Oct/inputForCode_Bangladesh.xlsx'
thisData = data.readSpreadsheet(spreadsheet, helper.keyList)
x_coverage = np.arange(0, 1.0, 0.05)#0.01)

for intervention in ['Breastfeeding promotion','Complementary feeding education']:
    y_outcome = []    
    for thisCoverage in x_coverage:
        # get model object
        model, derived, params = helper.setupModelConstantsParameters(thisData)
        timestepsPre = 12
        for t in range(timestepsPre):
            model.moveOneTimeStep() 
        # set initial coverage then change specific coverage
        coverage = dcp(thisData.coverage)    
        coverage[intervention] = thisCoverage  
        # update coverages after 1 year   
        model.updateCoverages(coverage)
        for t in range(numModelSteps - timestepsPre):
            model.moveOneTimeStep()
        y_outcome.append(model.getOutcome('thrive'))
    # plot for this intervention
    plt.plot(x_coverage, y_outcome)
    plt.xlabel('coverage')
    plt.ylabel('number thriving')
    plt.title(intervention)
    plt.show()    
    print intervention
    print x_coverage
    print y_outcome




   
