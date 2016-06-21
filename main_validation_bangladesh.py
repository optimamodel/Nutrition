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
numYears = int(timespan)
yearList = list(range(startYear, startYear+numYears))

helper = helper.Helper()
ages = ["<1 month", "1-5 months", "6-11 months", "12-23 months", "24-59 months"]
birthOutcomes = ["Pre-term SGA", "Pre-term AGA", "Term SGA", "Term AGA"]
wastingList = ["normal", "mild", "moderate", "high"]
stuntingList = ["normal", "mild", "moderate", "high"]
breastfeedingList = ["exclusive", "predominant", "partial", "none"]
keyList = [ages, birthOutcomes, wastingList, stuntingList, breastfeedingList]
ageGroupSpans = [1., 5., 6., 12., 36.] # number of months in each age group
agingRateList = [1./1., 1./5., 1./6., 1./12., 1./36.] # fraction of people aging out per MONTH
numAgeGroups = len(ages)

dataFilename = 'Input_Optima_%s_%i.xlsx'%(country,startYear)

spreadsheetData = dataCode.getDataFromSpreadsheet(dataFilename, keyList)
mothers = helper.makePregnantWomen(spreadsheetData)
mothers['annualPercentPopGrowth'] = -0.01
agePopSizes  = helper.makeAgePopSizes(numAgeGroups, ageGroupSpans, spreadsheetData)
year1 = 3871841
year2 = 3731124
year3 = 3645815
year4 = 3567786
year5 = 3491964
agePopSizes  = [year1/12., year1*5./12., year1*6./12., year2, year3+year4+year5]

# initialise
newCoverages={}
print "Baseline coverages:"
for intervention in spreadsheetData.interventionList:
    newCoverages[intervention] = spreadsheetData.interventionCoveragesCurrent[intervention]
    print "%s : %g"%(intervention,spreadsheetData.interventionCoveragesCurrent[intervention])

plotData = []
run = 0

#------------------------------------------------------------------------    
# HISTORICAL BUT BASELINE 2000

nametag = "Baseline"
filenamePrefix = '%s_Historical'%(country)
pickleFilename = '%s_baseline.pkl'%(filenamePrefix)
plotcolor = 'grey'

print "\n"+nametag
modelB, constants, params = helper.setupModelConstantsParameters(nametag, mothers, timestep, agingRateList, agePopSizes, keyList, spreadsheetData)

# file to dump objects into at each time step
outfile = open(pickleFilename, 'wb')

# Run model until the end
for t in range(numsteps):
    modelB.moveOneTimeStep()
    pickle.dump(modelB, outfile)

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


#------------------------------------------------------------------------    
# HISTORICAL SCALE UPS

nametag = "Nutrition-specific interventions only (Optima)"
filenamePrefix = '%s_Historical'%(country)
pickleFilename = '%s.pkl'%(filenamePrefix)
plotcolor = 'green'

print "\n"+nametag
modelH, constants, params = helper.setupModelConstantsParameters(nametag, mothers, timestep, agingRateList, agePopSizes, keyList, spreadsheetData)

totalStepsTaken = 0
# file to dump objects into at each time step
outfile = open(pickleFilename, 'wb')

# Run model until 2004
yearsUntilNextUpdate = 4
print "\n running for %i years"%(yearsUntilNextUpdate)
stepsUntilNextUpdate = int(yearsUntilNextUpdate/timestep)
for t in range(stepsUntilNextUpdate):
    modelH.moveOneTimeStep()
    pickle.dump(modelH, outfile)
totalStepsTaken += stepsUntilNextUpdate

modelH.getDiagnostics(verbose=True)

# update coverages in 2004
newCoverages["Vitamin A supplementation"] = 0.82
print "\n Updating..."
modelH.updateCoverages(newCoverages)
print "\n coverages after 2004:"
for intervention in spreadsheetData.interventionList:
    print "%s : %g"%(intervention,newCoverages[intervention])

modelH.getDiagnostics(verbose=True)

# Run model until 2007
yearsUntilNextUpdate = 3
print "\n running for %i years"%(yearsUntilNextUpdate)
stepsUntilNextUpdate = int(yearsUntilNextUpdate/timestep)
for t in range(stepsUntilNextUpdate):
    modelH.moveOneTimeStep()
    pickle.dump(modelH, outfile)
totalStepsTaken += stepsUntilNextUpdate

modelH.getDiagnostics(verbose=True)

# update coverages in 2007
newCoverages["Vitamin A supplementation"] = 0.84
print "\n Updating..."
modelH.updateCoverages(newCoverages)
print "\n coverages after 2007:"
for intervention in spreadsheetData.interventionList:
    print "%s : %g"%(intervention,newCoverages[intervention])

modelH.getDiagnostics(verbose=True)

# Run model until 2011
yearsUntilNextUpdate = 4
print "\n running for %i years"%(yearsUntilNextUpdate)
stepsUntilNextUpdate = int(yearsUntilNextUpdate/timestep)
for t in range(stepsUntilNextUpdate):
    modelH.moveOneTimeStep()
    pickle.dump(modelH, outfile)
totalStepsTaken += stepsUntilNextUpdate

modelH.getDiagnostics(verbose=True)

# update coverages in 2011
newCoverages["Vitamin A supplementation"] = 0.6
print "\n Updating..."
modelH.updateCoverages(newCoverages)
print "\n coverages after 2011:"
for intervention in spreadsheetData.interventionList:
    print "%s : %g"%(intervention,newCoverages[intervention])

modelH.getDiagnostics(verbose=True)

newCoverages["Breastfeeding promotion (dual delivery)"] = 0.61
print "\n Updating..."
modelH.updateCoverages(newCoverages)
print "\n coverages after 2011:"
for intervention in spreadsheetData.interventionList:
    print "%s : %g"%(intervention,newCoverages[intervention])

modelH.getDiagnostics(verbose=True)

# Run model until 2014
yearsUntilNextUpdate = 3
print "\n running for %i years"%(yearsUntilNextUpdate)
stepsUntilNextUpdate = int(yearsUntilNextUpdate/timestep)
for t in range(stepsUntilNextUpdate):
    modelH.moveOneTimeStep()
    pickle.dump(modelH, outfile)
totalStepsTaken += stepsUntilNextUpdate

modelH.getDiagnostics(verbose=True)

# update coverages in 2014
newCoverages["Vitamin A supplementation"] = 0.621
newCoverages["Complementary feeding (education)"] = 0.247
print "\n Updating..."
modelH.updateCoverages(newCoverages)
print "\n coverages after 2014::"
for intervention in spreadsheetData.interventionList:
    print "%s : %g"%(intervention,newCoverages[intervention])

modelH.getDiagnostics(verbose=True)

# Run model until the end
print "\n Number of years left to run = %g"%((numsteps-totalStepsTaken)/12)
for t in range(numsteps-totalStepsTaken):
    modelH.moveOneTimeStep()
    pickle.dump(modelH, outfile)
totalStepsTaken += t+1

modelH.getDiagnostics(verbose=True)

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

#------------------------------------------------------------------------    
numRuns = run

output.getCombinedPlots(run, plotData, startYear=startYear, filenamePrefix=filenamePrefix, save=True)
#output.getDeathsAverted(modelList, newModelList, 'test')
#output.getStuntedPercent(modelList, '2000-2015', startYear=2000)

#------------------------------------------------------------------------    

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib import rcParams

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
print "\n Plotting..."

rcParams.update({'font.size':20})

#skip = 2
#yearTickList =  list(range(startYear, startYear+numYears, skip))
yearAxisLimits = [yearList[0]-1, yearList[numYears-1]+1]

def myfunc(x, pos=0):
    return '%.0f%%'%(x)

# PLOT comparison of Stunted Fraction (everyone U5)
fig, ax = plt.subplots()
ax.set_xlabel('Year', size=20)
ax.set_xlim(yearAxisLimits)
#plt.rc('xtick', labelsize=20)
#ax.get_xticklabels().set_fontsize(20)
#ax.set_xticklabels(yearTickList)
#plt.ylabel('Percentage of children under 5 stunted')
ax.set_ylim([0, 50])
ax.yaxis.set_major_formatter(FuncFormatter(myfunc))
#plt.rc('ytick', labelsize=24)
#ax.get_yticklabels().set_fontsize(20)

# plot
plotList = []
tagList = []
for iRun in range(numRuns):
    tag       = plotData[iRun]["tag"]
    color     = plotData[iRun]["color"]
    plotObj,  = plt.plot(yearList, stuntFracU5annual[tag], linewidth=3.3, color=color)
    plotList.append(plotObj)
    tagList.append(tag)

#allYear      = [2000, 2000, 2004, 2004, 2007, 2007, 2007, 2009, 2011, 2012, 2014]
#allStuntFrac = [45,   44.7, 42,   43,   40,   36,   43.2, 43,   41,   42,   36]

BDHSyear      = [2000, 2004, 2007, 2011, 2014]
BDHSstuntFrac = [44.7, 43,   43.2, 41,   36  ]
plotBDHS = plt.scatter(BDHSyear, BDHSstuntFrac, s=80, marker='s', color="#DD0055")
plotList.append(plotBDHS)
tagList.append("Data (BDHS)")

otherYear      = [2000, 2004, 2007, 2007, 2009, 2012]
otherStuntFrac = [45,   42,   40,   36,   43,   42  ]
plotOther = plt.scatter(otherYear, otherStuntFrac, s=80, marker='D', color="#DD7722")
plotList.append(plotOther)
tagList.append("Data (other)")


plt.legend(plotList, tagList, loc = 'upper center', bbox_to_anchor=(0.5,-0.1))
plt.savefig("%s_stuntingPrevalence.png"%(filenamePrefix), bbox_inches='tight')


"""
# PLOT comparison of Deaths (everyone U5)
fig, ax = plt.subplots()
ax.set_xticklabels(yearTickList)
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
