# -*- coding: utf-8 -*-
"""
Created on Fri May 13 10:51:12 2016

@author: ruth
"""
import pickle as pickle

pickleFilename = 'testDefault.pkl'
infile = open(pickleFilename, 'rb')
modelList = []
while 1:
    try:
        modelList.append(pickle.load(infile))
    except (EOFError):
        break
infile.close()


pickleFilename = 'testInterventions.pkl'
infile = open(pickleFilename, 'rb')
newModelList = []
while 1:
    try:
        newModelList.append(pickle.load(infile))
    except (EOFError):
        break
infile.close()



#output.getDeathsAverted(modelList, newModelList, '')
#
#plotData = []
#plotData.append({})
#plotData[0]["modelList"] = modelList
#plotData[0]["tag"] = 'no intervention'
#plotData[0]["color"] = 'grey'
#plotData.append({})
#plotData[1]["modelList"] = newModelList
#plotData[1]["tag"] = 'with intervention'
#plotData[1]["color"] = 'blue'
#output.getCombinedPlots(2, plotData)




import numpy as np
import matplotlib.pyplot as plt



font = {'family' : 'normal',
        'weight' : 'normal',
        'size'   : 10}

plt.rc('font', **font)




numYears = int(len(modelList)/12)
skip = 2
yearList =  list(range(2016, 2016+numYears+1, skip))#[2016]
x = np.arange(8)

fig, ax = plt.subplots()
ax.set_xticks(x)
ax.set_xticklabels(yearList)
ax.set_ylim([0, 40])
plt.ylabel('Stunted population fraction (all U5)')

noInt = [35, 35, 35, 35, 35, 35, 35, 35]
nowInt = [34.5, 34.5, 34.5, 34.5, 34.5, 34.5, 34.5, 34.5]
futureInt = [28, 28, 28, 28, 28, 28, 28, 28]

y1 = 35 + 0.5 * (np.exp(-x)-1)
y2 = 35 + 7 * (np.exp(-x)-1)

plt.plot(x, noInt, color = 'black', label = 'current baseline')
plt.plot(x, y1, color = 'blue', label = 'increase coverage for 2 interventions')
plt.plot(x, y2, color = 'red', linestyle='--', linewidth=2, label = 'increase coverage all interventions')
ax.legend(loc = 'lower right')
plt.show()



modelList2 = newModelList
fig, ax = plt.subplots()

finalIndex = len(modelList) - 1
deathsAvertedByAge=[]
for iAge in range(0, len(modelList[0].ages)):
    deathsAverted = modelList[finalIndex].listOfAgeCompartments[iAge].getCumulativeDeaths() - modelList2[finalIndex].listOfAgeCompartments[iAge].getCumulativeDeaths()
    deathsAvertedByAge.append(deathsAverted)

bars = []    
bars = deathsAvertedByAge[1:]
bars.append(np.sum(deathsAvertedByAge))
bars.append(9946)   
 
bar_labels = []
bar_labels = ['1-5', '6-11','12-23','24-59','1-59','1-59']
colors = ['b', 'b', 'b', 'b', 'b', 'r']
X = np.arange(6)
width = 0.5
ax.set_xticks(X )
ax.set_xticklabels(bar_labels)
plots = []
plots.append(ax.bar(X, bars, width, align='center', color=colors))
ax.set_ylabel('number of deaths averted')
ax.set_xlabel('age in months')
plt.show()    










