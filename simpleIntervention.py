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

file2 = open('testZinc.pkl', 'rb')
# read the model output with simple intervention
zinc = []
while 1:
    try:
        zinc.append(pickle.load(file2))
    except (EOFError):
        break
file2.close()

"""
file3 = open('extremeIntervention.pkl', 'rb')
# read the model output with simple intervention
extreme = []
while 1:
    try:
        extreme.append(pickle.load(file3))
    except (EOFError):
        break
file3.close()
"""


output.getPopSizeByAgePlot(default, "default")
output.getPopSizeByAgePlot(zinc, "zinc")

output.getPopAndStuntedSizePlot(default, "default")
output.getPopAndStuntedSizePlot(zinc, "zinc")

output.getCumulativeDeathsByAgePlot(default, "default")
output.getCumulativeDeathsByAgePlot(zinc, "zinc")

output.getNumStuntedByAgePlot(default, "default")
output.getNumStuntedByAgePlot(zinc, "zinc")

output.getStuntedPercent(default, "default")
output.getStuntedPercent(zinc, "zinc")



plotData = []
plotData.append({})
plotData[0]["modelList"] = default
plotData[0]["tag"] = "default"
plotData[0]["color"] = 'grey'
plotData.append({})
plotData[1]["modelList"] = zinc
plotData[1]["tag"] = "increased Zinc"
plotData[1]["color"] = 'blue'
output.getCombinedPlots(2, plotData)
