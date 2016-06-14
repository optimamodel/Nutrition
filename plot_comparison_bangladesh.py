
# -*- coding: utf-8 -*-
"""
Created on Wed June 01 2016

@author: madhurakilledar
"""

import output as output
import pickle as pickle
import data as dataCode

country = 'Bangladesh'

startYear = 2016
numYears = 15
yearList =  list(range(startYear, startYear+numYears))


#------------------------------------------------------------------------    
# GATHER OPTIMA OUTPUT

def addToPlotData(plotData,run,pickleFilename,nametag,plotcolor):
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
    print "finished reading %s"%(nametag)

plotData = []
run=0
#-------------------------------
# Default Baseline run
nametag = "Baseline"
pickleFilename = '%s_Default.pkl'%(country)
plotcolor = 'grey'
addToPlotData(plotData,run,pickleFilename,nametag,plotcolor)
run += 1
#-------------------------------
# Increase coverage of Complementary feeding
percentageIncrease = 50
#nametag = "scale-up complementary feeding: ++ %g%% points"%(percentageIncrease)
nametag = "Scale-up complementary feeding"
pickleFilename = '%s_CompFeed_P%i.pkl'%(country,percentageIncrease)
plotcolor = 'green'
addToPlotData(plotData,run,pickleFilename,nametag,plotcolor)
run += 1
#-------------------------------
# Increase coverage of breastfeeding
percentageIncrease = 29
nametag = "Breastfeeding: ++ %g%% points"%(percentageIncrease)
nametag = "Scale-up breastfeeding"
pickleFilename = '%s_BreastFeed_P%i.pkl'%(country,percentageIncrease)
plotcolor = 'blue'
addToPlotData(plotData,run,pickleFilename,nametag,plotcolor)
run += 1

numRuns = run


#------------------------------------------------------------------------    
# GATHER LiST OUTPUT
fileName_LiST = "output_LiSTscenarios_%s.xlsx"%(country)
import pandas
df = pandas.read_excel(fileName_LiST, sheetname = 'total stunting')
scenarios = list(df['scenario'])
# stunting prevalence
df = pandas.read_excel(fileName_LiST, sheetname = 'total stunting', index_col = [0])
stunting_LiST = {}
for scenario in scenarios:
    print "reading LiST for %s"%(scenario)
    stunting_LiST[scenario] = []
    for year in yearList:
        stunting_LiST[scenario].append(df.loc[scenario, year])
# deaths each year
df = pandas.read_excel(fileName_LiST, sheetname = 'deaths', index_col = [0])
deaths_LiST = {}
for scenario in scenarios:
    print "reading LiST for %s"%(scenario)
    deaths_LiST[scenario] = []
    for year in yearList:
        deaths_LiST[scenario].append(df.loc[scenario, year])


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
cumulDeathsU5 = {}
for iRun in range(numRuns):
    modelList = plotData[iRun]["modelList"]
    tag       = plotData[iRun]["tag"]
    # initialise
    totalPopU5[tag]    = [0.]*numMonths
    stuntPopU5[tag]    = [0.]*numMonths
    cumulDeathsU5[tag] = [0.]*numMonths
    for mon in range(numMonths):
        model = modelList[mon]
        for age in range(numAges):
            ageName = ageList[age]
            total       = model.listOfAgeCompartments[age].getTotalPopulation()
            stuntFrac   = model.listOfAgeCompartments[age].getStuntedFraction()
            cumulDeaths = model.listOfAgeCompartments[age].getCumulativeDeaths()
            totalPopU5[tag][mon]    += total
            stuntPopU5[tag][mon]    += total*stuntFrac
            cumulDeathsU5[tag][mon] += cumulDeaths
# stunted fraction can't be added, so calculate from stuntPopU5 and totalPopU5 afterward
stuntFracU5monthly = {}
stuntFracU5annual  = {}
deathsU5annual     = {}
for iRun in range(numRuns):
    tag = plotData[iRun]["tag"]
    stuntFracU5monthly[tag] = [0.]*numMonths
    stuntFracU5annual[tag]  = [0.]*numYears
    deathsU5annual[tag]     = [0.]*numYears
    for m in range(numMonths):
        stuntFracU5monthly[tag][m] = 100. * stuntPopU5[tag][m] / totalPopU5[tag][m]
    for i in range(numYears):
        thisYear  = yearList[i]
        thisMonth = 12*(thisYear-startYear)
        stuntFracU5annual[tag][i] = stuntFracU5monthly[tag][thisMonth]
    deathsU5annual[tag][0]    = cumulDeathsU5[tag][12*1-1]
    for i in range(1,numYears):
        thisYear = yearList[i]
        endMonthLast = 12*(thisYear-startYear)  -1
        endMonthThis = 12*(thisYear-startYear+1)-1
        deathsU5annual[tag][i] = cumulDeathsU5[tag][endMonthThis] - cumulDeathsU5[tag][endMonthLast]
            

# PLOTTING
print "plotting..."
skip = 2
yearPlotList =  list(range(startYear, startYear+numYears, skip))

# PLOT comparison of Stunted Fraction (everyone U5)
fig, ax = plt.subplots()
ax.set_xticklabels(yearPlotList)
ax.set_xlim([yearList[0], yearList[numYears-1]])
ax.set_ylim([35., 42.])
plt.ylabel('Percentage of children under 5 stunted')
plt.xlabel('Year')
# choose scenarios
plotRuns_Optima = [0,1]
plotRuns_LiST   = [0,2]
colorChoice     = ['grey','green']
# plot
plotList = []
tagList_Optima = []
tagList_LiST   = []
for i in range(2):
    iRun = plotRuns_Optima[i]
    tag       = plotData[iRun]["tag"]
    color     = plotData[iRun]["color"]
    plotObj,  = plt.plot(yearList, stuntFracU5annual[tag], linewidth=1.7,     color=colorChoice[i])
    plotMark, = plt.plot(yearList, stuntFracU5annual[tag], ms=17, marker='o', color=colorChoice[i])
    plotList.append(plotMark)
    tagList_Optima.append("Optima: "+tag)
for i in range(2):
    iRun = plotRuns_LiST[i]
    scenario = scenarios[iRun]
    plotObj,  = plt.plot(yearList, stunting_LiST[scenario], linewidth=1.7,    color=colorChoice[i])
    plotMark, = plt.plot(yearList, stunting_LiST[scenario], ms=21, marker='*',color=colorChoice[i])
    plotList.append(plotMark)
    tagList_Optima.append("LiST:   "+scenario)
tagList = tagList_Optima + tagList_LiST
plt.legend(plotList, tagList, loc = 'upper center', bbox_to_anchor=(0.5,-0.1))
plt.savefig("%s_stuntingPrevalence.png"%(filenamePrefix), bbox_inches='tight')



# PLOT comparison of Deaths (everyone U5)
fig, ax = plt.subplots()
ax.set_xticklabels(yearPlotList)
ax.set_xlim([yearList[0], yearList[numYears-1]])
ax.set_ylim([90000, 120000])
plt.ylabel('Number of deaths in children under 5')
plt.xlabel('Year')
# choose scenarios
plotRuns_Optima = [0,2]
plotRuns_LiST   = [0,1]
colorChoice     = ['grey','blue']
# plot
plotList = []
tagList_Optima = []
tagList_LiST   = []
for i in range(2):
    iRun = plotRuns_Optima[i]
    tag       = plotData[iRun]["tag"]
    color     = plotData[iRun]["color"]
    plotObj,  = plt.plot(yearList, deathsU5annual[tag], linewidth=1.7,     color=colorChoice[i])
    plotMark, = plt.plot(yearList, deathsU5annual[tag], ms=17, marker='o', color=colorChoice[i])
    plotList.append(plotMark)
    tagList_Optima.append("Optima: "+tag)
for i in range(2):
    iRun = plotRuns_LiST[i]
    scenario = scenarios[iRun]
    plotObj,  = plt.plot(yearList, deaths_LiST[scenario], linewidth=1.7,    color=colorChoice[i])
    plotMark, = plt.plot(yearList, deaths_LiST[scenario], ms=21, marker='*',color=colorChoice[i])
    plotList.append(plotMark)
    tagList_Optima.append("LiST:   "+scenario)
tagList = tagList_Optima + tagList_LiST
plt.legend(plotList, tagList, loc = 'upper center', bbox_to_anchor=(0.5,-0.1))
plt.savefig("%s_annualDeaths.png"%(filenamePrefix), bbox_inches='tight')
