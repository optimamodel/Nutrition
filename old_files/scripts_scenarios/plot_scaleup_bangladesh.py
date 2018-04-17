# -*- coding: utf-8 -*-
"""
Created on Wed June 01 2016

@author: madhurakilledar
"""

import pickle as pickle

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(moduleDir)
import data
from old_files import helper
import output

country = 'Bangladesh'

helper = helper.Helper()

dataFilename = '../input_spreadsheets/%s/InputForCode_%s.xlsx'%(country, country)
inputData = data.getDataFromSpreadsheet(dataFilename, helper.keyList)

plotData = []
run=0

pickleFilename = '%s_Default.pkl'%(country)
nametag = "Baseline"
plotcolor = 'grey'
file = open(pickleFilename, 'rb')
modelList = []
while 1:
    try:
        modelList.append(pickle.load(file))
    except (EOFError):
        break
file.close()
plotData.append({})
plotData[run]["modelList"] = modelList
plotData[run]["tag"] = nametag
plotData[run]["color"] = plotcolor
run += 1

percentageIncrease = 20
title = '%s: 2015-2030 \n Scale up interventions by %i%% points'%(country,percentageIncrease)
filenamePrefix = '%s_%i'%(country,percentageIncrease)

for ichoose in range(len(inputData.interventionList)):
    chosenIntervention = inputData.interventionList[ichoose]
    pickleFilename = '%s_Intervention%i_P%i.pkl'%(country,ichoose,percentageIncrease)
    nametag = chosenIntervention
    print "\n"+nametag

    fileX = open(pickleFilename, 'rb')
    # read the model output with simple intervention
    modelXList = []
    while 1:
        try:
            modelXList.append(pickle.load(fileX))
        except (EOFError):
            break
    fileX.close()
    plotData.append({})
    plotData[run]["modelList"] = modelXList
    plotData[run]["tag"] = nametag
    plotData[run]["color"] = (1.0-0.13*run, 1.0-0.3*abs(run-4), 0.0+0.13*run)
    run += 1

output.getCombinedPlots(run, plotData, startYear=2015, filenamePrefix=filenamePrefix, save=True)
output.getCompareDeathsAverted(run, plotData, filenamePrefix=filenamePrefix, title=title, save=True)
