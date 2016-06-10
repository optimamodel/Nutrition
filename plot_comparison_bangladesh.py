
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
dataFilename = 'Input_LiST_%s.xlsx'%(country)
spreadsheetData = dataCode.getDataFromSpreadsheet(dataFilename, keyList)

startYear = 2016
numYears = 15
yearList =  list(range(startYear, startYear+numYears))

plotData = []
run=0

#------------------------------------------------------------------------    
# DEFAULT RUN WITH NO CHANGES TO INTERVENTIONS
nametag = "Baseline"
pickleFilename = '%s_Default.pkl'%(country)
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

#------------------------------------------------------------------------    
# INCREASE COVERAGE OF COMPLEMENTARY FEEDING BY 50%
percentageIncrease = 50
nametag = "Complementary feeding: increase coverage by %g%% points"%(percentageIncrease)
pickleFilename = '%s_CompFeed_P%i.pkl'%(country,percentageIncrease)
plotcolor = 'green'

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

#------------------------------------------------------------------------    
# INCREASE COVERAGE OF BREASTFEEDING FROM 61% to 90%
percentageIncrease = 29
nametag = "Breastfeeding: increase coverage by %g%% points"%(percentageIncrease)
pickleFilename = '%s_BreastFeed_P%i.pkl'%(country,percentageIncrease)
plotcolor = 'blue'

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

numRuns = run
#------------------------------------------------------------------------    
# READ FROM LIST OUTPUT
import pandas
df = pandas.read_excel("output_LiSTscenarios_bangladesh.xlsx", sheetname = 'total stunting')
scenarios = list(df['scenario'])
df = pandas.read_excel("output_LiSTscenarios_bangladesh.xlsx", sheetname = 'total stunting', index_col = [0])
stunting_LiST = {}
for scenario in scenarios:
    #stunting_LiST[scenario] = {}
    stunting_LiST[scenario] = []
    for year in yearList:
        #stunting_LiST[scenario][year] = df.loc[scenario, year]
        stunting_LiST[scenario].append(df.loc[scenario, year])

#------------------------------------------------------------------------    
# MAKE PLOTS
filenamePrefix = '%s_comparison'%(country)
#output.getCombinedPlots(run, plotData, startYear=2015, filenamePrefix=filenamePrefix, title=title, save=True)
#output.getCompareDeathsAverted(run, plotData, filenamePrefix=filenamePrefix, title=title, save=True)

import numpy as np
import matplotlib.pyplot as plt

# set up
modelList = plotData[0]["modelList"]
ageList = modelList[0].ages
numAges = len(ageList)
numMonths = len(modelList)
#numYears = int(len(modelList)/12)

totalPopU5 = {}
stuntPopU5 = {}
for iRun in range(numRuns):
    modelList = plotData[iRun]["modelList"]
    tag       = plotData[iRun]["tag"]
    # initialise
    totalPopU5[tag] = [0.]*numMonths
    stuntPopU5[tag] = [0.]*numMonths
    for mon in range(numMonths):
        model = modelList[mon]
        for age in range(numAges):
            ageName = ageList[age]
            total       = model.listOfAgeCompartments[age].getTotalPopulation()
            stuntFrac   = model.listOfAgeCompartments[age].getStuntedFraction()
            totalPopU5[tag][mon]    += total
            stuntPopU5[tag][mon]    += total*stuntFrac
# stunted fraction can't be added, so calculate from stuntPopU5 and totalPopU5 afterward
stuntFracU5monthly = {}
stuntFracU5annual  = {}
for iRun in range(numRuns):
    tag       = plotData[iRun]["tag"]
    stuntFracU5monthly[tag] = [0.]*numMonths
    stuntFracU5annual[tag]  = [0.]*numYears
    for m in range(numMonths):
        stuntFracU5monthly[tag][m] = 100. * stuntPopU5[tag][m] / totalPopU5[tag][m]
    for i in range(numYears):
        year = yearList[i]
        stuntFracU5annual[tag][i] = stuntFracU5monthly[tag][12*(year-startYear)]
            

# PLOTTING
skip = 2
yearPlotList =  list(range(startYear, startYear+numYears, skip))
#xTickList = list(range(0, 12*(numYears+1),    skip*12))
#xTickList = np.arange(numYears)
monthList = np.arange(numMonths)

tagList  = []
for iRun in range(numRuns):
    tag       = plotData[iRun]["tag"]
    tagList.append(tag)

# PLOT comparison of Stunted Fraction (everyone U5)
fig, ax = plt.subplots()
#ax.set_xticks(xTickList)
ax.set_xticklabels(yearPlotList)
ax.set_xlim([yearList[0], yearList[numYears-1]])
ax.set_ylim([35., 42.])
plt.ylabel('Stunted prevalence (all U5)')
plotList = []
for iRun in range(numRuns):
    tag       = plotData[iRun]["tag"]
    color     = plotData[iRun]["color"]
    plotObj,  = plt.plot(yearList, stuntFracU5annual[tag], linewidth=1.7,     color=color)
    plotMark, = plt.plot(yearList, stuntFracU5annual[tag], ms=19, marker='o', color=color)
    plotList.append(plotMark)
    
icolor=0
for scenario in scenarios:
    plotObj,  = plt.plot(yearList, stunting_LiST[scenario], linewidth=1.7,    )
    plotMark, = plt.plot(yearList, stunting_LiST[scenario], ms=21, marker='*',)
    plotList.append(plotMark)
    icolor += 1


for i in range(numRuns):
    tagList[i]   = "Optima: "+tagList[i]
for i in range(len(scenarios)):
    scenarios[i] = "LiST:   "+scenarios[i]
    
plt.legend(plotList, tagList+scenarios, loc = 'center left', bbox_to_anchor=(1,0.5))
plt.savefig("%s_stuntingPrevalence.png"%(filenamePrefix), bbox_inches='tight')
