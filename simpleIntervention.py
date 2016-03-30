# -*- coding: utf-8 -*-
"""
Created on Tue Mar 29 16:14:56 2016

@author: ruth
"""

import pickle as pickle
import output as output

file1 = open('noIntervention.pkl', 'rb')
# read the model output from no interventions
none = []
while 1:
    try:
        none.append(pickle.load(file1))
    except (EOFError):
        break
file1.close()

file2 = open('someIntervention.pkl', 'rb')
# read the model output with simple intervention
some = []
while 1:
    try:
        some.append(pickle.load(file2))
    except (EOFError):
        break
file2.close()

file3 = open('extremeIntervention.pkl', 'rb')
# read the model output with simple intervention
extreme = []
while 1:
    try:
        extreme.append(pickle.load(file3))
    except (EOFError):
        break
file3.close()



output.getPopSizeByAgePlot(none, "none")
output.getPopSizeByAgePlot(some, "some")
output.getPopSizeByAgePlot(extreme, "extreme")

output.getCumulativeDeathsByAgePlot(none, "none")
output.getCumulativeDeathsByAgePlot(some, "some")
output.getCumulativeDeathsByAgePlot(extreme, "extreme")

output.getNumStuntedByAgePlot(none, "none")
output.getNumStuntedByAgePlot(some, "some")
output.getNumStuntedByAgePlot(extreme, "extreme")

output.getStuntedPercent(none, "none")
output.getStuntedPercent(some, "some")
output.getStuntedPercent(extreme, "extreme")