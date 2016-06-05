# -*- coding: utf-8 -*-
"""
Created on Wed June 01 2016

@author: madhurakilledar
"""

import output as output
import pickle as pickle
import data as dataCode

country = 'Bangladesh'

ages = ["<1 month", "1-5 months", "6-11 months", "12-23 months", "24-59 months"]
birthOutcomes = ["Pre-term SGA", "Pre-term AGA", "Term SGA", "Term AGA"]
wastingList = ["normal", "mild", "moderate", "high"]
stuntingList = ["normal", "mild", "moderate", "high"]
breastfeedingList = ["exclusive", "predominant", "partial", "none"]
keyList = [ages, birthOutcomes, wastingList, stuntingList, breastfeedingList]
dataFilename = 'InputForCode_%s.xlsx'%(country)
spreadsheetData = dataCode.getDataFromSpreadsheet(dataFilename, keyList)

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

percentageIncrease = 30
title = '%s: 2016-2030 \n Scale up interventions by %i%% points'%(country,percentageIncrease)
filenamePrefix = '%s_%i'%(country,percentageIncrease)

for ichoose in range(len(spreadsheetData.interventionList)):
    chosenIntervention = spreadsheetData.interventionList[ichoose]
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

#output.getCombinedPlots(run, plotData, filenamePrefix=filenamePrefix, title=title, save=True)
output.getCompareDeathsAverted(run, plotData, filenamePrefix=filenamePrefix, title=title, save=True)
