
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
nametag = "Baseline (BF 61%, CF 20.9%)"
pickleFilename = '%s_Default_forLiST.pkl'%(country)
plotcolor = 'grey'
addToPlotData(plotData,run,pickleFilename,nametag,plotcolor)
run += 1
#-------------------------------
# Increase coverage of breastfeeding
scenarios = [70, 80, 90]
for icov in range(len(scenarios)):
    BFcoverage = scenarios[icov]
    #percentageIncrease = 29
    nametag = "BF to %i%%"%(BFcoverage)
    pickleFilename = '%s_BreastFeed_P%i.pkl'%(country,BFcoverage)
    plotcolor = (0.1, 0.1, 1.0-0.15*icov)
    addToPlotData(plotData,run,pickleFilename,nametag,plotcolor)
    run += 1
#-------------------------------
# Increase coverage of Complementary feeding
scenarios = [30, 50, 70]
for icov in range(len(scenarios)):
    CFcoverage = scenarios[icov]
    #percentageIncrease = 50
    nametag = "CF to %i%%"%(CFcoverage)
    pickleFilename = '%s_CompFeed_P%i.pkl'%(country,CFcoverage)
    plotcolor = (0.1, 1.0-0.2*icov, 0.1)
    addToPlotData(plotData,run,pickleFilename,nametag,plotcolor)
    run += 1
#-------------------------------
# Increase coverage of breastfeeding AND complementary feeding
BFcoverage = 80
CFcoverage = 30
nametag = "BF to %i%%, CF to %i%%"%(BFcoverage,CFcoverage)
pickleFilename = '%s_BF%i_CF%i.pkl'%(country,BFcoverage,CFcoverage)
plotcolor = (0.7, 0.1, 0.1)
addToPlotData(plotData,run,pickleFilename,nametag,plotcolor)
run += 1


#-------------------------------

numRuns = run

#------------------------------------------------------------------------    
# GATHER LiST OUTPUT
filename_LiST = "scenarios_LiST_%s.xlsx"%(country)
import pandas
df = pandas.read_excel(filename_LiST, sheetname = 'deaths')
scenarios = list(df['scenario'])
# stunting prevalence
df = pandas.read_excel(filename_LiST, sheetname = 'stunting prevalence', index_col = [0])
stunting_LiST = {}
for scenario in scenarios:
    print "reading LiST for %s"%(scenario)
    stunting_LiST[scenario] = []
    for year in yearList:
        stunting_LiST[scenario].append(df.loc[scenario, year])
# deaths each year
df = pandas.read_excel(filename_LiST, sheetname = 'deaths', index_col = [0])
deaths_LiST = {}
for scenario in scenarios:
    print "reading LiST for %s"%(scenario)
    deaths_LiST[scenario] = []
    for year in yearList:
        deaths_LiST[scenario].append(df.loc[scenario, year])
# number stunted
df = pandas.read_excel(filename_LiST, sheetname = 'number stunted', index_col = [0])
stunted_LiST = {}
for scenario in scenarios:
    print "reading LiST for %s"%(scenario)
    stunted_LiST[scenario] = []
    for year in yearList:
        stunted_LiST[scenario].append(df.loc[scenario, year])
# deaths averted
scen_baseline = 'Baseline (BF 61%, CF 20.9%)'
deaths_baseline_LiST = deaths_LiST[scen_baseline]
deaths_averted_LiST = {}
deaths_averted_perc_LiST = {}
for scenario in scenarios[1:]:
    deaths_averted_LiST[scenario] = [0.]*numYears
    deaths_averted_perc_LiST[scenario] = [0.]*numYears
    for i in range(numYears):
        deaths_averted_LiST[scenario][i] = deaths_baseline_LiST[i] - deaths_LiST[scenario][i]
        deaths_averted_perc_LiST[scenario][i] = 100. * deaths_averted_LiST[scenario][i] / deaths_baseline_LiST[i]
# stunting cases averted
scen_baseline = 'Baseline (BF 61%, CF 20.9%)'
stunted_baseline_LiST = stunted_LiST[scen_baseline]
stunted_averted_LiST = {}
for scenario in scenarios[1:]:
    stunted_averted_LiST[scenario] = [0.]*numYears
    for i in range(numYears):
        stunted_averted_LiST[scenario][i] = stunted_baseline_LiST[i] - stunted_LiST[scenario][i]


#------------------------------------------------------------------------    
# COLLECT OPTIMA DATA INTO LISTS

# set up
modelList = plotData[0]["modelList"]
ageList = modelList[0].ages
numAges = len(ageList)
numMonths = len(modelList)
#numYears = int(len(modelList)/12)
# collect: total population, number stunted, cumulative deaths
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
# collect: prevalence of stunting and annual deaths
stuntFracU5monthly = {}
stuntFracU5annual  = {}
stuntPopU5annual   = {}
deathsU5annual     = {}
for iRun in range(numRuns):
    tag = plotData[iRun]["tag"]
    stuntFracU5monthly[tag] = [0.]*numMonths
    stuntFracU5annual[tag]  = [0.]*numYears
    stuntPopU5annual[tag]   = [0.]*numYears
    # stunted fraction can't be added, so calculate from stuntPopU5 and totalPopU5 afterward
    for m in range(numMonths):
        stuntFracU5monthly[tag][m] = 100. * stuntPopU5[tag][m] / totalPopU5[tag][m]
    for i in range(numYears):
        thisYear  = yearList[i]
        thisMonth = 12*(thisYear-startYear)
        stuntFracU5annual[tag][i] = stuntFracU5monthly[tag][thisMonth]
        stuntPopU5annual[tag][i]  = stuntPopU5[tag][thisMonth]
    # annual deaths
    deathsU5annual[tag]     = [0.]*numYears
    deathsU5annual[tag][0]  = cumulDeathsU5[tag][12*1-1]
    for i in range(1,numYears):
        thisYear = yearList[i]
        endMonthLast = 12*(thisYear-startYear)  -1
        endMonthThis = 12*(thisYear-startYear+1)-1
        deathsU5annual[tag][i] = cumulDeathsU5[tag][endMonthThis] - cumulDeathsU5[tag][endMonthLast]
# deaths averted
tag_baseline = plotData[0]["tag"]
deaths_baseline = deathsU5annual[tag_baseline]
deaths_averted = {}
deaths_averted_perc = {}
for iRun in range(1,numRuns):
    tag = plotData[iRun]["tag"]
    deaths_averted[tag] = [0.]*numYears
    deaths_averted_perc[tag] = [0.]*numYears
    for i in range(numYears):
        deaths_averted[tag][i] = deaths_baseline[i] - deathsU5annual[tag][i]
        deaths_averted_perc[tag][i] = deaths_averted[tag][i] / deaths_baseline[i] * 100.
# cases of stunting averted    
tag_baseline = plotData[0]["tag"]
stuntcase_baseline = stuntPopU5annual[tag_baseline]
stunted_averted = {}
for iRun in range(1,numRuns):
    tag = plotData[iRun]["tag"]
    stunted_averted[tag] = [0.]*numYears
    for i in range(numYears):
        stunted_averted[tag][i] = stuntcase_baseline[i] - stuntPopU5annual[tag][i]



#------------------------------------------------------------------------    
# MAKE PLOTS
filenamePrefix = '%s_comparison'%(country)

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib import rcParams

def myfunc(x, pos=0):
    return '%.0f%%'%(x)

def myfunc2(x, pos=0):
    return '%.1f%%'%(x)

# PLOTTING
print "\n Plotting..."
skip = 2
yearPlotList =  list(range(startYear, startYear+numYears, skip))
rcParams.update({'font.size':20})


# PLOT comparison of Stunted Fraction (everyone U5)
fig, ax = plt.subplots()
ax.set_xlim([yearList[0], yearList[numYears-1]])
ax.set_xticklabels(yearPlotList)
ax.tick_params(pad=11)
ax.set_ylim([35., 42.])
ax.yaxis.set_major_formatter(FuncFormatter(myfunc))
plt.title('Prevalence of stunting in children under 5',y=1.09)
plt.xlabel('Year')
# choose scenarios
plotRuns_Optima = [4,5,6]
plotRuns_LiST   = [4,5,6]
colorChoice     = ['#99FF99','#66DD66','#44BB44']
# plot
plotList = []
tagList_Optima = []
tagList_LiST   = []
for i in range(3):
    iRun = plotRuns_Optima[i]
    tag       = plotData[iRun]["tag"]
    color     = plotData[iRun]["color"]
    plotObj,  = plt.plot(yearList, stuntFracU5annual[tag], linewidth=1.7,     color=colorChoice[i])
    plotMark, = plt.plot(yearList, stuntFracU5annual[tag], ms=17, marker='o', color=colorChoice[i])
    plotList.append(plotMark)
    tagList_Optima.append("Optima: "+tag)
for i in range(3):
    iRun = plotRuns_LiST[i]
    scenario = scenarios[iRun]
    plotObj,  = plt.plot(yearList, stunting_LiST[scenario], linewidth=1.7,    color=colorChoice[i])
    plotMark, = plt.plot(yearList, stunting_LiST[scenario], ms=21, marker='*',color=colorChoice[i])
    plotList.append(plotMark)
    tagList_Optima.append("LiST     : "+scenario)
tagList = tagList_Optima + tagList_LiST
plt.legend(plotList, tagList, loc = 'center left', bbox_to_anchor=(1.05,0.5))
plt.savefig("%s_stuntingPrevalence_CF.png"%(filenamePrefix), bbox_inches='tight')




# PLOT comparison of Stunted Fraction (everyone U5)
fig, ax = plt.subplots()
ax.set_xlim([yearList[0], yearList[numYears-1]])
ax.set_xticklabels(yearPlotList)
ax.tick_params(pad=11)
ax.set_ylim([39., 42.])
ax.yaxis.set_major_formatter(FuncFormatter(myfunc2))
plt.title('Prevalence of stunting in children under 5',y=1.09)
plt.xlabel('Year')
# choose scenarios
plotRuns_Optima = [2,4,7]
plotRuns_LiST   = [2,4,9]
colorChoice     = ['#99FF99','#66DD66','#44BB44']
# plot
plotList = []
tagList_Optima = []
tagList_LiST   = []
for i in range(3):
    iRun = plotRuns_Optima[i]
    tag       = plotData[iRun]["tag"]
    color     = plotData[iRun]["color"]
    plotObj,  = plt.plot(yearList, stuntFracU5annual[tag], linewidth=1.7,     color=colorChoice[i])
    plotMark, = plt.plot(yearList, stuntFracU5annual[tag], ms=17, marker='o', color=colorChoice[i])
    plotList.append(plotMark)
    tagList_Optima.append("Optima: "+tag)
for i in range(3):
    iRun = plotRuns_LiST[i]
    scenario = scenarios[iRun]
    plotObj,  = plt.plot(yearList, stunting_LiST[scenario], linewidth=1.7,    color=colorChoice[i])
    plotMark, = plt.plot(yearList, stunting_LiST[scenario], ms=21, marker='*',color=colorChoice[i])
    plotList.append(plotMark)
    tagList_Optima.append("LiST     : "+scenario)
tagList = tagList_Optima + tagList_LiST
plt.legend(plotList, tagList, loc = 'center left', bbox_to_anchor=(1.05,0.5))
plt.savefig("%s_stuntingPrevalence.png"%(filenamePrefix), bbox_inches='tight')




# PLOT comparison of Stunted cases Averted (everyone U5)
fig, ax = plt.subplots()
ax.set_xlim([yearList[0], yearList[numYears-1]])
ax.set_xticklabels(yearPlotList)
ax.tick_params(pad=11)
ax.set_ylim([0, 130000])
plt.title('Cases of stunting averted in children under 5',y=1.09)
ax.yaxis.set_label_coords(-0.12,0.5)
plt.xlabel('Year')
# choose scenarios
plotRuns_Optima = [2,4,7] #[1,2,3]
plotRuns_LiST   = [2,4,9] #[4,5,6]
colorChoice     = ['#81D5EC','#51A5BC','#31859C'] # 31859C hue
# plot
plotList = []
tagList_Optima = []
tagList_LiST   = []
for i in range(3):
    iRun = plotRuns_Optima[i]
    tag       = plotData[iRun]["tag"]
    color     = plotData[iRun]["color"]
    plotObj,  = plt.plot(yearList, stunted_averted[tag], linewidth=1.7,     color=colorChoice[i])
    plotMark, = plt.plot(yearList, stunted_averted[tag], ms=17, marker='o', color=colorChoice[i])
    plotList.append(plotMark)
    tagList_Optima.append("Optima: "+tag)
for i in range(3):
    iRun = plotRuns_LiST[i]
    scenario = scenarios[iRun]
    plotObj,  = plt.plot(yearList, stunted_averted_LiST[scenario], linewidth=1.7,    color=colorChoice[i])
    plotMark, = plt.plot(yearList, stunted_averted_LiST[scenario], ms=21, marker='*',color=colorChoice[i])
    plotList.append(plotMark)
    tagList_Optima.append("LiST     : "+scenario)
tagList = tagList_Optima + tagList_LiST
#plt.legend(plotList, tagList, loc = 'upper center', bbox_to_anchor=(0.5,-0.13))
plt.legend(plotList, tagList, loc = 'center left', bbox_to_anchor=(1.05,0.5))
plt.savefig("%s_StuntingAverted.png"%(filenamePrefix), bbox_inches='tight')




# PLOT comparison of Deaths (everyone U5)
fig, ax = plt.subplots()
ax.set_xlim([yearList[0], yearList[numYears-1]])
ax.set_xticklabels(yearPlotList)
ax.tick_params(pad=11)
ax.set_ylim([0, 120000])
plt.title('Number of deaths in children under 5',y=1.09)
ax.yaxis.set_label_coords(-0.12,0.5)
plt.xlabel('Year')
# choose scenarios
plotRuns_Optima = [0,2,4,7]
plotRuns_LiST   = [0,2,4,9]
colorChoice     = ['grey','#E9D9FD','#C9B9DD','#8474BB'] # B2A2C6 hue
# plot
plotList = []
tagList_Optima = []
tagList_LiST   = []
for i in range(4):
    iRun = plotRuns_Optima[i]
    tag       = plotData[iRun]["tag"]
    color     = plotData[iRun]["color"]
    plotObj,  = plt.plot(yearList, deathsU5annual[tag], linewidth=1.7,     color=colorChoice[i])
    plotMark, = plt.plot(yearList, deathsU5annual[tag], ms=17, marker='o', color=colorChoice[i])
    plotList.append(plotMark)
    tagList_Optima.append("Optima: "+tag)
for i in range(4):
    iRun = plotRuns_LiST[i]
    scenario = scenarios[iRun]
    plotObj,  = plt.plot(yearList, deaths_LiST[scenario], linewidth=1.7,    color=colorChoice[i])
    plotMark, = plt.plot(yearList, deaths_LiST[scenario], ms=21, marker='*',color=colorChoice[i])
    plotList.append(plotMark)
    tagList_Optima.append("LiST     : "+scenario)
tagList = tagList_Optima + tagList_LiST
plt.legend(plotList, tagList, loc = 'center left', bbox_to_anchor=(1.05,0.5))
plt.savefig("%s_annualDeaths.png"%(filenamePrefix), bbox_inches='tight')



# PLOT comparison of Deaths (everyone U5) zoomed
fig, ax = plt.subplots()
ax.set_xlim([yearList[0], yearList[numYears-1]])
ax.set_xticklabels(yearPlotList)
ax.tick_params(pad=11)
ax.set_ylim([95000, 120000])
plt.title('Number of deaths in children under 5',y=1.09)
ax.yaxis.set_label_coords(-0.12,0.5)
plt.xlabel('Year')
# choose scenarios
plotRuns_Optima = [0,2,4,7]
plotRuns_LiST   = [0,2,4,9]
colorChoice     = ['grey','#E9D9FD','#C9B9DD','#8474BB'] # B2A2C6 hue
# plot
plotList = []
tagList_Optima = []
tagList_LiST   = []
for i in range(4):
    iRun = plotRuns_Optima[i]
    tag       = plotData[iRun]["tag"]
    color     = plotData[iRun]["color"]
    plotObj,  = plt.plot(yearList, deathsU5annual[tag], linewidth=1.7,     color=colorChoice[i])
    plotMark, = plt.plot(yearList, deathsU5annual[tag], ms=17, marker='o', color=colorChoice[i])
    plotList.append(plotMark)
    tagList_Optima.append("Optima: "+tag)
for i in range(4):
    iRun = plotRuns_LiST[i]
    scenario = scenarios[iRun]
    plotObj,  = plt.plot(yearList, deaths_LiST[scenario], linewidth=1.7,    color=colorChoice[i])
    plotMark, = plt.plot(yearList, deaths_LiST[scenario], ms=21, marker='*',color=colorChoice[i])
    plotList.append(plotMark)
    tagList_Optima.append("LiST     : "+scenario)
tagList = tagList_Optima + tagList_LiST
plt.legend(plotList, tagList, loc = 'center left', bbox_to_anchor=(1.05,0.5))
plt.savefig("%s_annualDeaths_zoom.png"%(filenamePrefix), bbox_inches='tight')




# PLOT comparison of Deaths Averted (everyone U5)
fig, ax = plt.subplots()
ax.set_xlim([yearList[0], yearList[numYears-1]])
ax.set_xticklabels(yearPlotList)
ax.tick_params(pad=11)
ax.set_ylim([0, 1500])
plt.title('Number of deaths averted in children under 5',y=1.09)
ax.yaxis.set_label_coords(-0.12,0.5)
plt.xlabel('Year')
# choose scenarios
plotRuns_Optima = [2,4,7]
plotRuns_LiST   = [2,4,9]
colorChoice     = ['#E9D9FD','#C9B9DD','#8474BB'] # B2A2C6 hue
# plot
plotList = []
tagList_Optima = []
tagList_LiST   = []
for i in range(3):
    iRun = plotRuns_Optima[i]
    tag       = plotData[iRun]["tag"]
    color     = plotData[iRun]["color"]
    plotObj,  = plt.plot(yearList, deaths_averted[tag], linewidth=1.7,     color=colorChoice[i])
    plotMark, = plt.plot(yearList, deaths_averted[tag], ms=17, marker='o', color=colorChoice[i])
    plotList.append(plotMark)
    tagList_Optima.append("Optima: "+tag)
for i in range(3):
    iRun = plotRuns_LiST[i]
    scenario = scenarios[iRun]
    plotObj,  = plt.plot(yearList, deaths_averted_LiST[scenario], linewidth=1.7,    color=colorChoice[i])
    plotMark, = plt.plot(yearList, deaths_averted_LiST[scenario], ms=21, marker='*',color=colorChoice[i])
    plotList.append(plotMark)
    tagList_Optima.append("LiST     : "+scenario)
tagList = tagList_Optima + tagList_LiST
plt.legend(plotList, tagList, loc = 'center left', bbox_to_anchor=(1.05,0.5))
plt.savefig("%s_DeathsAverted.png"%(filenamePrefix), bbox_inches='tight')




# PLOT comparison of Percentage of Deaths Averted (everyone U5)
fig, ax = plt.subplots()
ax.set_xlim([yearList[0], yearList[numYears-1]])
ax.set_xticklabels(yearPlotList)
ax.tick_params(pad=11)
ax.set_ylim([0, 1.5])
ax.yaxis.set_major_formatter(FuncFormatter(myfunc2))
plt.title('Deaths averted in children under 5',y=1.09)
ax.yaxis.set_label_coords(-0.12,0.5)
plt.xlabel('Year')
# choose scenarios
plotRuns_Optima = [2,4,7]
plotRuns_LiST   = [2,4,9]
colorChoice     = ['#E9D9FD','#C9B9DD','#8474BB'] # B2A2C6 hue
# plot
plotList = []
tagList_Optima = []
tagList_LiST   = []
for i in range(3):
    iRun = plotRuns_Optima[i]
    tag       = plotData[iRun]["tag"]
    color     = plotData[iRun]["color"]
    plotObj,  = plt.plot(yearList, deaths_averted_perc[tag], linewidth=1.7,     color=colorChoice[i])
    plotMark, = plt.plot(yearList, deaths_averted_perc[tag], ms=17, marker='o', color=colorChoice[i])
    plotList.append(plotMark)
    tagList_Optima.append("Optima: "+tag)
for i in range(3):
    iRun = plotRuns_LiST[i]
    scenario = scenarios[iRun]
    plotObj,  = plt.plot(yearList, deaths_averted_perc_LiST[scenario], linewidth=1.7,    color=colorChoice[i])
    plotMark, = plt.plot(yearList, deaths_averted_perc_LiST[scenario], ms=21, marker='*',color=colorChoice[i])
    plotList.append(plotMark)
    tagList_Optima.append("LiST     : "+scenario)
tagList = tagList_Optima + tagList_LiST
plt.legend(plotList, tagList, loc = 'center left', bbox_to_anchor=(1.05,0.5))
plt.savefig("%s_DeathsAvertedPerc.png"%(filenamePrefix), bbox_inches='tight')

