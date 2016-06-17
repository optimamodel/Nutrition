# -*- coding: utf-8 -*-
"""
Created on Wed June 15 2016

@author: madhurakilledar
"""
from __future__ import division

import data as dataCode
import helper as helper
import output as output
from copy import deepcopy as dcp
import pickle as pickle

country = 'Bangladesh'
startYear = 2000

timestep = 1./12. 
numsteps = 180
timespan = timestep * float(numsteps)
#endYear  = startYear + int(timespan)

helper = helper.Helper()
ages = ["<1 month", "1-5 months", "6-11 months", "12-23 months", "24-59 months"]
birthOutcomes = ["Pre-term SGA", "Pre-term AGA", "Term SGA", "Term AGA"]
wastingList = ["normal", "mild", "moderate", "high"]
stuntingList = ["normal", "mild", "moderate", "high"]
breastfeedingList = ["exclusive", "predominant", "partial", "none"]
keyList = [ages, birthOutcomes, wastingList, stuntingList, breastfeedingList]

dataFilename = 'Input_Optima_%s_%i.xlsx'%(country,startYear)
spreadsheetData = dataCode.getDataFromSpreadsheet(dataFilename, keyList)
mothers = helper.makePregnantWomen(spreadsheetData)
mothers['annualPercentPopGrowth'] = -0.01
ageGroupSpans = [1., 5., 6., 12., 36.] # number of months in each age group
agingRateList = [1./1., 1./5., 1./6., 1./12., 1./36.] # fraction of people aging out per MONTH
numAgeGroups = len(ages)
agePopSizes  = helper.makeAgePopSizes(numAgeGroups, ageGroupSpans, spreadsheetData)
year1 = 3871841
year2 = 3731124
year3 = 3645815
year4 = 3567786
year5 = 3491964
agePopSizes  = [year1/12., year1*5./12., year1*6./12., year2, year3+year4+year5]

# initialise
newCoverages={}
for intervention in spreadsheetData.interventionList:
    newCoverages[intervention] = spreadsheetData.interventionCoveragesCurrent[intervention]
    print "Baseline coverage of %s = %g"%(intervention,spreadsheetData.interventionCoveragesCurrent[intervention])

plotData = []
run = 0

#------------------------------------------------------------------------    
# DEFAULT RUN WITH NO CHANGES TO INTERVENTIONS
nametag = "Optima model"
filenamePrefix = '%s_Historical'%(country)
pickleFilename = '%s.pkl'%(filenamePrefix)
plotcolor = 'grey'

print "\n"+nametag
modelH, constants, params = helper.setupModelConstantsParameters(nametag, mothers, timestep, agingRateList, agePopSizes, keyList, spreadsheetData)

totalStepsTaken = 0
# file to dump objects into at each time step
outfile = open(pickleFilename, 'wb')

yearsUntilNextUpdate = 4
stepsUntilNextUpdate = int(yearsUntilNextUpdate/timestep)
for t in range(stepsUntilNextUpdate):
    modelH.moveOneTimeStep()
    pickle.dump(modelH, outfile)
totalStepsTaken += stepsUntilNextUpdate

# update coverages in 2004
newCoverages["Vitamin A supplementation"] = 0.82
modelH.updateCoverages(newCoverages)
print "\n Current Coverages:"
for intervention in spreadsheetData.interventionList:
    print "%s : %g"%(intervention,newCoverages[intervention])

# Run model until 2007
yearsUntilNextUpdate = 3
stepsUntilNextUpdate = int(yearsUntilNextUpdate/timestep)
for t in range(stepsUntilNextUpdate):
    modelH.moveOneTimeStep()
    pickle.dump(modelH, outfile)
totalStepsTaken += stepsUntilNextUpdate

# update coverages in 2007
newCoverages["Vitamin A supplementation"] = 0.84
modelH.updateCoverages(newCoverages)
print "\n Current Coverages:"
for intervention in spreadsheetData.interventionList:
    print "%s : %g"%(intervention,newCoverages[intervention])

# Run model until 2011
yearsUntilNextUpdate = 4
stepsUntilNextUpdate = int(yearsUntilNextUpdate/timestep)
for t in range(stepsUntilNextUpdate):
    modelH.moveOneTimeStep()
    pickle.dump(modelH, outfile)
totalStepsTaken += stepsUntilNextUpdate

# update coverages in 2011
newCoverages["Vitamin A supplementation"] = 0.6
newCoverages["Breastfeeding promotion (dual delivery)"] = 0.61
modelH.updateCoverages(newCoverages)
print "\n Current Coverages:"
for intervention in spreadsheetData.interventionList:
    print "%s : %g"%(intervention,newCoverages[intervention])

# Run model until 2014
yearsUntilNextUpdate = 3
stepsUntilNextUpdate = int(yearsUntilNextUpdate/timestep)
for t in range(stepsUntilNextUpdate):
    modelH.moveOneTimeStep()
    pickle.dump(modelH, outfile)
totalStepsTaken += stepsUntilNextUpdate

# update coverages in 2014
newCoverages["Vitamin A supplementation"] = 0.621
newCoverages["Complementary feeding (education)"] = 0.247
modelH.updateCoverages(newCoverages)
print "\n Current Coverages:"
for intervention in spreadsheetData.interventionList:
    print "%s : %g"%(intervention,newCoverages[intervention])

# Run model until the end
print "Number of years left to run = %g"%((numsteps-totalStepsTaken)/12)
for t in range(numsteps-totalStepsTaken):
    modelH.moveOneTimeStep()
    pickle.dump(modelH, outfile)
totalStepsTaken += t+1

# done
outfile.close()    

# collect output, make graphs etc.
infile = open(pickleFilename, 'rb')
modelList = []
while 1:
    try:
        modelList.append(pickle.load(infile))
    except (EOFError):
        break
infile.close()

plotData.append({})
plotData[run]["modelList"] = modelList
plotData[run]["tag"] = nametag
plotData[run]["color"] = plotcolor
run += 1

numRuns = run
numYears = int(timespan)
yearList =  list(range(startYear, startYear+numYears))
#------------------------------------------------------------------------    

output.getCombinedPlots(run, plotData, startYear=startYear, filenamePrefix=filenamePrefix, save=True)
#output.getDeathsAverted(modelList, newModelList, 'test')
#output.getStuntedPercent(modelList, '2000-2015', startYear=2000)

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
ax.set_ylim([34., 47.])
plt.ylabel('Percentage of children under 5 stunted')
plt.xlabel('Year')

# plot
plotList = []
tagList = []
tag       = plotData[iRun]["tag"]
color     = plotData[iRun]["color"]
plotObj,  = plt.plot(yearList, stuntFracU5annual[tag], linewidth=1.7,     color=color)
plotMark, = plt.plot(yearList, stuntFracU5annual[tag], ms=10, marker='o', color=color)
plotList.append(plotMark)
tagList.append(tag)

historyYear      = np.array([2000, 2000, 2004, 2004, 2007, 2007, 2007, 2009, 2011, 2012, 2014])
historyStuntFrac = np.array([45,   44.7, 42,   43,   40,   36,   43.2, 43,   41,   42,   36])
plotHistory, = plt.scatter(historyYear, historyStuntFrac, s=17, marker='*', color="red")
plotList.append(plotHistory)
tagList.append("Historical data")

plt.legend(plotList, tagList, loc = 'upper center', bbox_to_anchor=(0.5,-0.1))
plt.savefig("%s_stuntingPrevalence.png"%(filenamePrefix), bbox_inches='tight')


"""
# PLOT comparison of Deaths (everyone U5)
fig, ax = plt.subplots()
ax.set_xticklabels(yearPlotList)
ax.set_xlim([yearList[0], yearList[numYears-1]])
ax.set_ylim([100000, 200000])
plt.ylabel('Number of deaths in children under 5')
plt.xlabel('Year')
# choose scenarios
plotRuns_Optima = [0,2]
colorChoice     = ['grey','blue']
# plot
plotList = []
tagList_Optima = []
for i in range(2):
    iRun = plotRuns_Optima[i]
    tag       = plotData[iRun]["tag"]
    color     = plotData[iRun]["color"]
    plotObj,  = plt.plot(yearList, deathsU5annual[tag], linewidth=1.7,     color=colorChoice[i])
    plotMark, = plt.plot(yearList, deathsU5annual[tag], ms=17, marker='o', color=colorChoice[i])
    plotList.append(plotMark)
    tagList_Optima.append("Optima: "+tag)

plt.legend(plotList, tagList, loc = 'upper center', bbox_to_anchor=(0.5,-0.1))
plt.savefig("%s_annualDeaths.png"%(filenamePrefix), bbox_inches='tight')
"""
