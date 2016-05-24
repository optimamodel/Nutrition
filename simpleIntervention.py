# -*- coding: utf-8 -*-
"""
Created on Tue Mar 29 16:14:56 2016

@author: ruth
"""

import pickle as pickle
import output as output

file1 = open('testDefault.pkl', 'rb')
# read the model output from no interventions
default = []
while 1:
    try:
        default.append(pickle.load(file1))
    except (EOFError):
        break
file1.close()

file2 = open('test_Intervention_M30.pkl', 'rb')
# read the model output with simple intervention
test_m30 = []
while 1:
    try:
        test_m30.append(pickle.load(file2))
    except (EOFError):
        break
file2.close()

file3 = open('test_Intervention_P30.pkl', 'rb')
# read the model output with simple intervention
test_p30 = []
while 1:
    try:
        test_p30.append(pickle.load(file3))
    except (EOFError):
        break
file3.close()


output.getPopSizeByAgePlot(default, "default")
output.getPopSizeByAgePlot(test_m30, "test_m30")

output.getPopAndStuntedSizePlot(default, "default")
output.getPopAndStuntedSizePlot(test_m30, "test_m30")

output.getCumulativeDeathsByAgePlot(default, "default")
output.getCumulativeDeathsByAgePlot(test_m30, "test_m30")

output.getNumStuntedByAgePlot(default, "default")
output.getNumStuntedByAgePlot(test_m30, "test_m30")

output.getStuntedPercent(default, "default")
output.getStuntedPercent(test_m30, "test_m30")



plotData = []
run=0
plotData.append({})
plotData[run]["modelList"] = test_m30
plotData[run]["tag"] = "decreased coverage by 30\%"
plotData[run]["color"] = 'red'
run += 1
plotData.append({})
plotData[run]["modelList"] = default
plotData[run]["tag"] = "default"
plotData[run]["color"] = 'grey'
run += 1
plotData.append({})
plotData[run]["modelList"] = test_p30
plotData[run]["tag"] = "increased coverage by 30\%"
plotData[run]["color"] = 'blue'
run += 1
output.getCombinedPlots(run, plotData)
