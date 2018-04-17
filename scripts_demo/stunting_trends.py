# -*- coding: utf-8 -*-
"""
Created on Thu Jun 29 15:39:54 2017

@author: ruth
"""

rootpath = '../'

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)

from nutrition import data
from old_files import helper
import matplotlib.pyplot as plt
helper = helper.Helper()

numModelSteps = 15 
spreadsheet = rootpath + 'input_spreadsheets/Bangladesh/2017Jan/InputForCode_Bangladesh.xlsx'
spreadsheetData = data.readSpreadsheet(spreadsheet, helper.keyList)
model, derived, params = helper.setupModelDerivedParameters(spreadsheetData)

stuntPrev = []
stuntPrev.append(model.getOutcome('stunting prev'))
#stuntPrev.append(model.listOfAgeCompartments[0].getStuntedFraction())
# run the model for the num timesteps
for t in range(numModelSteps):
    model.moveOneTimeStep()
    stuntPrev.append(model.getOutcome('stunting prev'))
    #stuntPrev.append(model.listOfAgeCompartments[0].getStuntedFraction())

years = range(2015, 2031)

# plot
plt.plot(years, stuntPrev)
plt.xlabel('year')
plt.ylabel('stunting prevalence')
plt.ylim((0,1))
plt.legend(loc='lower left')
plt.show()          