# -*- coding: utf-8 -*-
"""
Created on Fri Mar 11 11:50:20 2016

@author: ruth

contains:
getPopSizeByAgePlot()
getPopAndStuntedSizePlot()
getCumulativeDeathsByAgePlot()
getNumStuntedByAgePlot()
getStuntedPercent()
getCombinedPlots()
getCompareDeathsAverted()
getU5StuntingCasesAverted()
getA5StuntingCasesAverted()
getSimpleBarFromDictionary()
getStuntingStatusesGivenAge()
getDeathsAverted()
getBudgetPieChartComparison()
plotCoverage()
plotSpendingAllocation()
plotSpendingAndCoverageTogether()
compareOptimisationOutput()
"""

from __future__ import division


def getPopSizeByAgePlot(modelList, label):
    ageList = modelList[0].ages
    #get population size for each age group
    popSize = {}
    for iAge in range(0, len(modelList[0].ages)):
        popSize[iAge] = 0
        countThis = []
        for model in modelList:
            count = model.listOfAgeCompartments[iAge].getTotalPopulation()
            countThis.append(count)
        popSize[iAge] = countThis      
    
    #get some x axis stuff    
    numYears = int(len(modelList)/12)
    yearList = [2016]
    xTickList = [0]
    for i in range(1, numYears+1):
        yearList.append(yearList[0] + i)   
        xTickList.append(i * 12)
    
    import numpy as np
    import matplotlib.pyplot as plt
    x = np.arange(len(modelList))
    y1 = popSize[0]
    y2 = popSize[1]
    y3 = popSize[2]
    y4 = popSize[3]
    y5 = popSize[4]
    
    fig, ax = plt.subplots()
    ax.stackplot(x, y1, y2, y3, y4, y5)
    ax.legend(ageList, loc = 'upper left')
    ax.set_xticks(xTickList)
    ax.set_xticklabels(yearList)
    #ax.set_ylim([0, 1.6e10])
    plt.ylabel('population size')
    #plt.xlabel('time steps in months')
    plt.title('Population Size by Age Group:  ' + label)
    plt.show()
    
    return popSize



def getPopAndStuntedSizePlot(modelList, label):
    ageList = modelList[0].ages
    numAges = len(ageList)
    # get populations sizes for all U5s
    numMonths = len(modelList) 
    totalPopU5 = [0.]*numMonths
    stuntPopU5 = [0.]*numMonths
    # get population size for each age group
    totalPop = []
    stuntPop = []
    for iAge in range(0, numAges):
        totalPop.append([])
        stuntPop.append([])
        m=0
        for model in modelList:
            total     = model.listOfAgeCompartments[iAge].getTotalPopulation()
            stuntfrac = model.listOfAgeCompartments[iAge].getStuntedFraction()
            totalPop[iAge].append(total)
            stuntPop[iAge].append(total*stuntfrac)
            totalPopU5[m] += total
            stuntPopU5[m] += total*stuntfrac
            m+=1

    #get some x axis stuff    
    numYears = int(len(modelList)/12)
    yearList = list(range(2016, 2016+numYears+1))
    xTickList = list(range(0, 12*(numYears+1), 12))
    
    import numpy as np
    import matplotlib.pyplot as plt
    x = np.arange(len(modelList))

    fig, ax = plt.subplots()
    plot_total = plt.fill_between(x, totalPopU5, stuntPopU5, color='blue')
    plot_stunt = plt.fill_between(x, stuntPopU5, 0,         color='red')
    ax.set_xticks(xTickList)
    ax.set_xticklabels(yearList)
    ax.set_xlim([0, 12*numYears])
    plt.ylabel('population size')
    plt.title('Total and Stunted Population Size : %s'%(label))
    ax.legend([plot_total, plot_stunt], ["Total", "Stunted"])
    plt.show()


    axes=[]
    fig, ax = plt.subplots()
    #for iAge in range(0, len(modelList[0].ages)):
    #    fig, ((axes[0], axes[1], axes[2]), (axes[3], axes[4], ax5)) = plt.subplots(2,3)
    y1 = totalPop[0]
    y2 = totalPop[1]
    y3 = totalPop[2]
    y4 = totalPop[3]
    y5 = totalPop[4]
    ax.stackplot(x, y1, y2, y3, y4, y5)
    ax.legend(ageList, loc = 'upper left')
    ax.set_xticks(xTickList)
    ax.set_xticklabels(yearList)
    #ax.set_ylim([0, 1.6e10])
    plt.ylabel('population size')
    #plt.xlabel('time steps in months')
    plt.title('Population Size by Age Group:  ' + label)
    plt.show()
    
    #return totalPop, stuntPop



def getCumulativeDeathsByAgePlot(modelList, label):
    ageList = modelList[0].ages
    #get population size for each age group
    cumulativeDeaths = {}
    for iAge in range(0, len(modelList[0].ages)):
        cumulativeDeaths[iAge] = 0
        countThis = []
        for model in modelList:
            count = model.listOfAgeCompartments[iAge].getCumulativeDeaths()
            countThis.append(count)
        cumulativeDeaths[iAge] = countThis  

    
    #get some x axis stuff    
    numYears = int(len(modelList)/12)
    yearList = [2016]
    xTickList = [0]
    for i in range(1, numYears+1):
        yearList.append(yearList[0] + i)   
        xTickList.append(i * 12)    
    
    import numpy as np
    import matplotlib.pyplot as plt
    x = np.arange(len(modelList))
    y1 = cumulativeDeaths[0]
    y2 = cumulativeDeaths[1]
    y3 = cumulativeDeaths[2]
    y4 = cumulativeDeaths[3]
    y5 = cumulativeDeaths[4]
    
    fig, ax = plt.subplots()
    ax.stackplot(x, y1, y2, y3, y4, y5)
    ax.set_xticks(xTickList)
    ax.set_xticklabels(yearList)
    ax.legend(ageList, loc = 'upper left')
    plt.ylabel('cumulative deaths')
    #plt.xlabel('time steps in months')
    plt.title('Cumulative Deaths by Age Group:  ' + label)
    plt.show()

    
def getNumStuntedByAgePlot(modelList, label):
    #this counts people in the top 2 stunting categories
    ageList = modelList[0].ages
    #get population size for each age group
    numStunted = {}
    for iAge in range(0, len(modelList[0].ages)):
        numStunted[iAge] = 0
        countThis = []
        for model in modelList:
            count = model.listOfAgeCompartments[iAge].getNumberStunted()
            countThis.append(count)
        numStunted[iAge] = countThis      
        
    #get some x axis stuff    
    numYears = int(len(modelList)/12)
    yearList = [2016]
    xTickList = [0]
    for i in range(1, numYears+1):
        yearList.append(yearList[0] + i)   
        xTickList.append(i * 12)      
    
    import numpy as np
    import matplotlib.pyplot as plt
    x = np.arange(len(modelList))
    y1 = numStunted[0]
    y2 = numStunted[1]
    y3 = numStunted[2]
    y4 = numStunted[3]
    y5 = numStunted[4]
    
    fig, ax = plt.subplots()
    ax.stackplot(x, y1, y2, y3, y4, y5)
    ax.set_xticks(xTickList)
    ax.set_xticklabels(yearList)
    ax.legend(ageList, loc = 'upper left')
    plt.ylabel('number of people stunted')
    #plt.xlabel('time steps in months')
    plt.title('Number of People Stunted by Age Group:  ' + label)
    plt.show()
    
    
    
def getStuntedPercent(modelList, label, startYear=2016): 
    import numpy as np
    ageList = modelList[0].ages
    percentStunted = {}
    for iAge in range(0, len(modelList[0].ages)):
        StuntedFracList = []
        for model in modelList:
            StuntedFrac = model.listOfAgeCompartments[iAge].getStuntedFraction()
            StuntedFracList.append(StuntedFrac)
        #get yearly average
        numYears = int(len(modelList)/12)
        yearAveStuntedPerc = []
        for year in range(1, numYears+1):
            yearAveStuntedPerc.append(100.*np.average(StuntedFracList[(year - 1) * 12 : (year * 12) - 1]))
        percentStunted[iAge] = yearAveStuntedPerc
    yearList = [startYear]
    for i in range(1, numYears):
        yearList.append(yearList[0] + i)
    import matplotlib.pyplot as plt
    x = np.arange(numYears)
    width = 0.35
    fig, ax = plt.subplots()    
    rects1 = ax.bar(6*x*width, percentStunted[0], width, color='r')
    rects2 = ax.bar(6*x*width + width, percentStunted[1], width, color='y')
    rects3 = ax.bar(6*x*width + 2*width, percentStunted[2], width, color='g')
    rects4 = ax.bar(6*x*width + 3*width, percentStunted[3], width, color='c')
    rects5 = ax.bar(6*x*width + 4*width, percentStunted[4], width, color='m')
    # Shrink current axis's height by 10% on the bottom
    box = ax.get_position()
    ax.set_position([box.x0, box.y0 + box.height * 0.1,
                 box.width, box.height * 0.9])
    
    ax.legend( (rects1[0], rects2[0], rects3[0], rects4[0], rects5[0]), (ageList[:]), loc = 'upper center', bbox_to_anchor=(0.5, -0.15), ncol=5, fancybox=True, shadow=True)
    ax.set_xticks(x*6*width + 2.5*width)
    ax.set_xticklabels(yearList)
    ax.set_ylabel('% of people stunted')
    #ax.set_xlabel('time steps in months')
    ax.set_title('Percent of People Stunted by Age Group:  ' + label)
    plt.show()    

    
    
def getCombinedPlots(numRuns, data, startYear=2016, filenamePrefix="compare", save=False):
    import numpy as np
    import matplotlib.pyplot as plt
    # set up
    modelList = data[0]["modelList"]
    ageList = modelList[0].ages
    numAges = len(ageList)
    numMonths = len(modelList)
    numYears = int(len(modelList)/12)

    totalPopU5 = {}
    stuntPopU5 = {}
    cumulDeathsU5 = {}
    cumulDeathsList = {}
    for run in range(numRuns):
        modelList = data[run]["modelList"]
        tag       = data[run]["tag"]
        # initialise
        totalPopU5[tag] = [0.]*numMonths
        stuntPopU5[tag] = [0.]*numMonths
        cumulDeathsU5[tag] = [0.]*numMonths
        for mon in range(numMonths):
            model = modelList[mon]
            for iAge in range(numAges):
                ageName = ageList[iAge]
                total       = model.listOfAgeCompartments[iAge].getTotalPopulation()
                stuntFrac   = model.listOfAgeCompartments[iAge].getStuntedFraction()
                cumulDeaths = model.listOfAgeCompartments[iAge].getCumulativeDeaths()
                totalPopU5[tag][mon]    += total
                stuntPopU5[tag][mon]    += total*stuntFrac
                cumulDeathsU5[tag][mon] += cumulDeaths
    # stunted fraction can't be added, so calculate from stuntPopU5 and totalPopU5 afterward
    stuntFracU5 = {}
    for run in range(numRuns):
        tag       = data[run]["tag"]
        stuntFracU5[tag] = [0.]*numMonths
        for m in range(numMonths):
            stuntFracU5[tag][m] = 100. * stuntPopU5[tag][m] / totalPopU5[tag][m]

    # PLOTTING
    skip = 2
    yearList =  list(range(startYear, startYear+numYears+1, skip))
    xTickList = list(range(0, 12*(numYears+1),    skip*12))
    monthList = np.arange(numMonths)

    tagList  = []
    for run in range(numRuns):
        tag       = data[run]["tag"]
        tagList.append(tag)

    # PLOT comparison of Stunted Population Size (everyone U5)
    fig, ax = plt.subplots()
    ax.set_xticks(xTickList)
    ax.set_xticklabels(yearList)
    ax.set_xlim([0, 12*numYears])
    #ax.set_ylim([0., 1.5*stuntPopU5[data[0]["tag"]][0]])
    plt.ylabel('Stunted population size (all U5)')
    plotList = []
    for run in range(numRuns):
        tag       = data[run]["tag"]
        color     = data[run]["color"]
        plotObj, = plt.plot(monthList, stuntPopU5[tag], linewidth=3., color=color)
        plotList.append(plotObj)
    plt.legend(plotList, tagList, loc = 'center left', bbox_to_anchor=(1,0.5))
    if save:
        plt.savefig("%s_stuntedPopSize.png"%(filenamePrefix), bbox_inches='tight')
    else:
        plt.show()

    # PLOT comparison of Stunted Fraction (everyone U5)
    fig, ax = plt.subplots()
    ax.set_xticks(xTickList)
    ax.set_xticklabels(yearList)
    ax.set_xlim([0, 12*numYears])
    #ax.set_ylim([0., 40.])
    plt.ylabel('Stunted prevalence (all U5)')
    plotList = []
    for run in range(numRuns):
        tag       = data[run]["tag"]
        color     = data[run]["color"]
        plotObj, = plt.plot(monthList, stuntFracU5[tag], linewidth=3., color=color)
        plotList.append(plotObj)
    plt.legend(plotList, tagList, loc = 'center left', bbox_to_anchor=(1,0.5))
    if save:
        plt.savefig("%s_stuntedFraction.png"%(filenamePrefix), bbox_inches='tight')
    else:
        plt.show()

    # PLOT comparison of Cumulative Deaths (everyone U5)
    fig, ax = plt.subplots()
    ax.set_xticks(xTickList)
    ax.set_xticklabels(yearList)
    ax.set_xlim([0, 12*numYears])
    plt.ylabel('Cumulative Deaths (all U5)')
    plotList = []
    for run in range(numRuns):
        tag       = data[run]["tag"]
        color     = data[run]["color"]
        plotObj, = plt.plot(monthList, cumulDeathsU5[tag], linewidth=3., color=color)
        plotList.append(plotObj)
    plt.legend(plotList, tagList, loc = 'center left', bbox_to_anchor=(1,0.5))
    if save:
        plt.savefig("%s_cumulativeDeaths.png"%(filenamePrefix), bbox_inches='tight')
    else:
        plt.show()




def getCompareDeathsAverted(numRuns, data, scalePercent=0.2, filenamePrefix="compare", title="", save=False):
    import numpy as np
    from math import ceil
    import matplotlib.pyplot as plt
    # set up
    modelList = data[0]["modelList"]
    ageList = modelList[0].ages
    numAges = len(ageList)
    numMonths = len(modelList)
    tagList  = []
    for run in range(numRuns):
        tag       = data[run]["tag"]
        tagList.append(tag)
    # add up deaths
    cumulDeathsU5 = {}
    cumulDeathsList = {}
    for run in range(numRuns):
        modelList = data[run]["modelList"]
        tag       = data[run]["tag"]
        # initialise
        cumulDeathsU5[tag] = [0.]*numMonths
        cumulDeathsList[tag] = {}
        for ageName in ageList:
            cumulDeathsList[tag][ageName] = [0.]*numMonths
        for mon in range(numMonths):
            model = modelList[mon]
            for iAge in range(numAges):
                ageName = ageList[iAge]
                cumulDeaths = model.listOfAgeCompartments[iAge].getCumulativeDeaths()
                cumulDeathsU5[tag][mon] += cumulDeaths
                cumulDeathsList[tag][ageName][mon] = cumulDeaths
    # calculate deaths averted
    deathsAvertedList    = []
    deathsNeoAvertedList = []
    neonatesName = ageList[0]
    tagBaseline = data[0]["tag"]
    deathsNeoBaseline = cumulDeathsList[tagBaseline][neonatesName][numMonths-1]
    deathsBaseline    = cumulDeathsU5[tagBaseline][numMonths-1]
    for run in range(1, numRuns):
        tag       = data[run]["tag"]
        deathsNeoScenario = cumulDeathsList[tag][neonatesName][numMonths-1]
        deathsScenario    = cumulDeathsU5[tag][numMonths-1]
        deathsNeoAvertedList.append(deathsNeoBaseline - deathsNeoScenario)
        deathsAvertedList.append(   deathsBaseline    - deathsScenario)
    # PLOTTING
    # setup figure
    fig, ax = plt.subplots()
    ax.set_title(title, size=16, y=1.13)
    maxDeaths      = max(deathsAvertedList)
    maxDeathsAxis  = ceil(maxDeaths/5000.)*5000
    maxPercentAxis = maxDeathsAxis/deathsBaseline*100.
    percentTicks = np.arange(scalePercent,maxPercentAxis,scalePercent)
    pTicksTrans = percentTicks/100.*deathsBaseline
    y_pos = np.arange(numRuns-1)
    # axes
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.axes.get_xaxis().tick_bottom()
    ax.axes.get_yaxis().tick_left()
    ax.set_ylim(0,numRuns-1)
    ax.set_xlim(0,maxDeathsAxis)
    ax.set_yticks(y_pos+0.5)
    ax.set_yticklabels(tagList[1:])
    ax.set_ylabel('Interventions',  size=16)
    ax.set_xlabel('Number of deaths averted in children', size=14)
    ax2 = ax.twiny()
    ax2.set_xlim(ax.get_xlim())
    ax2.set_xticks(pTicksTrans)
    ax2.set_xticklabels(percentTicks)
    ax2.set_xlabel('Percent of deaths averted (%)', size=14)
    # plot
    barwid = 0.5
    h1 = ax.barh(y_pos+0.5-0.5*barwid, deathsAvertedList,    height=barwid, facecolor='#99CCEE', edgecolor='k', linewidth=1.5)
    h2 = ax.barh(y_pos+0.5-0.5*barwid, deathsNeoAvertedList, height=barwid, facecolor='#FF9977', edgecolor='k', linewidth=1.5)
    plt.legend([h1,h2],["<5 years","<1 month"])
    if save:
        plt.savefig("%s_totalDeathsAverted.png"%(filenamePrefix), bbox_inches='tight')
    else:
        plt.show()



def getDALYsAverted(numRuns, data, scalePercent=0.2, filenamePrefix="compare", title="", save=False):
    import numpy as np
    from math import ceil
    import matplotlib.pyplot as plt
    # set up
    modelList = data[0]["modelList"]
    ageList = modelList[0].ages
    numMonths = len(modelList)
    tagList  = []
    for run in range(numRuns):
        tag       = data[run]["tag"]
        tagList.append(tag)
    # add up DALYs
    cumulDALYsU5 = {}
    for run in range(numRuns):
        modelList = data[run]["modelList"]
        tag       = data[run]["tag"]
        # initialise
        cumulDALYsU5[tag] = [0.]*numMonths
        for mon in range(numMonths):
            model = modelList[mon]
            cumulDALYsU5[tag][mon] += model.getDALYs()
    # calculate DALYs averted
    DALYsAvertedList    = []
    tagBaseline = data[0]["tag"]
    DALYsBaseline    = cumulDALYsU5[tagBaseline][numMonths-1]
    for run in range(1, numRuns):
        tag       = data[run]["tag"]
        DALYsScenario    = cumulDALYsU5[tag][numMonths-1]
        DALYsAvertedList.append(   DALYsBaseline    - DALYsScenario)
    # PLOTTING
    # setup figure
    fig, ax = plt.subplots()
    ax.set_title(title, size=16, y=1.13)
    maxDALYs      = max(DALYsAvertedList)
    maxDALYsAxis  = ceil(maxDALYs/100000.)*100000
    maxPercentAxis = maxDALYsAxis/DALYsBaseline*100.
    percentTicks = np.arange(scalePercent,maxPercentAxis,scalePercent)
    pTicksTrans = percentTicks/100.*DALYsBaseline
    y_pos = np.arange(numRuns-1)
    # axes
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.axes.get_xaxis().tick_bottom()
    ax.axes.get_yaxis().tick_left()
    ax.set_ylim(0,numRuns-1)
    ax.set_xlim(0,maxDALYsAxis)
    ax.set_yticks(y_pos+0.5)
    ax.set_yticklabels(tagList[1:])
    ax.set_ylabel('Interventions',  size=16)
    ax.set_xlabel('Number of DALYs averted in children', size=14)
    ax2 = ax.twiny()
    ax2.set_xlim(ax.get_xlim())
    ax2.set_xticks(pTicksTrans)
    ax2.set_xticklabels(percentTicks)
    ax2.set_xlabel('Percent of DALYs averted (%)', size=14)
    # plot
    barwid = 0.6
    h1 = ax.barh(y_pos+0.5-0.5*barwid, DALYsAvertedList,    height=barwid, facecolor='#99CCEE', edgecolor='k', linewidth=1.5)
    #plt.legend([h1,h2],["<5 years","<1 month"])
    if save:
        plt.savefig("%s_DALYsAverted.png"%(filenamePrefix), bbox_inches='tight')
    else:
        plt.show()



def getU5StuntingCasesAverted(numRuns, data, scalePercent=0.2, filenamePrefix="compare", title="", save=False):
    import numpy as np
    from math import ceil
    import matplotlib.pyplot as plt
    # set up
    modelList = data[0]["modelList"]
    ageList = modelList[0].ages
    numAges = len(ageList)
    numMonths = len(modelList)
    tagList  = []
    for run in range(numRuns):
        tag       = data[run]["tag"]
        tagList.append(tag)
    # add up deaths
    totalPopU5 = {}
    stuntPopU5 = {}
    for run in range(numRuns):
        modelList = data[run]["modelList"]
        tag       = data[run]["tag"]
        # initialise
        totalPopU5[tag] = [0.]*numMonths
        stuntPopU5[tag] = [0.]*numMonths
        for mon in range(numMonths):
            model = modelList[mon]
            for iAge in range(numAges):
                ageName = ageList[iAge]
                total       = model.listOfAgeCompartments[iAge].getTotalPopulation()
                stuntFrac   = model.listOfAgeCompartments[iAge].getStuntedFraction()
                totalPopU5[tag][mon]    += total
                stuntPopU5[tag][mon]    += total*stuntFrac
    # stunted fraction can't be added, so calculate from stuntPopU5 and totalPopU5 afterward
    stuntFracU5 = {}
    for run in range(numRuns):
        tag       = data[run]["tag"]
        stuntFracU5[tag] = [0.]*numMonths
        for m in range(numMonths):
            stuntFracU5[tag][m] = 100. * stuntPopU5[tag][m] / totalPopU5[tag][m]
    # calculate stunting cases averted
    stuntingAvertedList    = []
    tagBaseline = data[0]["tag"]
    stuntingCasesBaseline    = stuntPopU5[tagBaseline][numMonths-1]
    for run in range(1, numRuns):
        tag = data[run]["tag"]
        stuntingCasesScenario = stuntPopU5[tag][numMonths-1]
        stuntingAvertedList.append(stuntingCasesBaseline - stuntingCasesScenario)

    # PLOTTING
    # setup figure
    fig, ax = plt.subplots()
    ax.set_title(title, size=16, y=1.13)
    maxStunting     = max(stuntingAvertedList)
    maxStuntingAxis = ceil(maxStunting/10000.)*10000
    maxPercentAxis = maxStuntingAxis/stuntingCasesBaseline*100.
    percentTicks = np.arange(scalePercent,maxPercentAxis,scalePercent)
    pTicksTrans = percentTicks/100.*stuntingCasesBaseline
    y_pos = np.arange(numRuns-1)
    # axes
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.axes.get_xaxis().tick_bottom()
    ax.axes.get_yaxis().tick_left()
    ax.set_ylim(0,numRuns-1)
    ax.set_xlim(0,maxStuntingAxis)
    ax.set_yticks(y_pos+0.5)
    ax.set_yticklabels(tagList[1:])
    ax.set_ylabel('Interventions',  size=16)
    ax.set_xlabel('Number of stunting cases averted in children under 5', size=14)
    ax2 = ax.twiny()
    ax2.set_xlim(ax.get_xlim())
    ax2.set_xticks(pTicksTrans)
    ax2.set_xticklabels(percentTicks)
    ax2.set_xlabel('Percent of stunting cases averted (%)', size=14)
    # plot
    barwid = 0.5
    h1 = ax.barh(y_pos+0.5-0.5*barwid, stuntingAvertedList, height=barwid, facecolor='#99CCEE', edgecolor='k', linewidth=1.5)
    if save:
        plt.savefig("%s_U5stuntingCasesAverted.png"%(filenamePrefix), bbox_inches='tight')
    else:
        plt.show()





def getA5StuntingCasesAverted(numRuns, data, scalePercent=0.2, filenamePrefix="compare", title="", save=False):
    import numpy as np
    from math import ceil
    import matplotlib.pyplot as plt
    # set up
    modelList = data[0]["modelList"]
    numMonths = len(modelList)
    tagList  = []
    for run in range(numRuns):
        tag       = data[run]["tag"]
        tagList.append(tag)
    # add up deaths
    stuntPopA5 = {}
    for run in range(numRuns):
        modelList = data[run]["modelList"]
        tag       = data[run]["tag"]
        stuntPopA5[tag] = modelList[numMonths-1].getCumulativeAgingOutStunted()
    # calculate stunting cases averted
    stuntingAvertedList    = []
    tagBaseline = data[0]["tag"]
    stuntingCasesBaseline    = stuntPopA5[tagBaseline]
    for run in range(1, numRuns):
        tag = data[run]["tag"]
        stuntingCasesScenario = stuntPopA5[tag]
        stuntingAvertedList.append(stuntingCasesBaseline - stuntingCasesScenario)

    # PLOTTING
    # setup figure
    fig, ax = plt.subplots()
    ax.set_title(title, size=16, y=1.13)
    maxStunting     = max(stuntingAvertedList)
    maxStuntingAxis = ceil(maxStunting/10000.)*10000
    maxPercentAxis = maxStuntingAxis/stuntingCasesBaseline*100.
    percentTicks = np.arange(scalePercent,maxPercentAxis,scalePercent)
    pTicksTrans = percentTicks/100.*stuntingCasesBaseline
    y_pos = np.arange(numRuns-1)
    # axes
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.axes.get_xaxis().tick_bottom()
    ax.axes.get_yaxis().tick_left()
    ax.set_ylim(0,numRuns-1)
    ax.set_xlim(0,maxStuntingAxis)
    ax.set_yticks(y_pos+0.5)
    ax.set_yticklabels(tagList[1:])
    ax.set_ylabel('Interventions',  size=16)
    ax.set_xlabel('Number of stunting cases averted in children by age 5', size=14)
    ax2 = ax.twiny()
    ax2.set_xlim(ax.get_xlim())
    ax2.set_xticks(pTicksTrans)
    ax2.set_xticklabels(percentTicks)
    ax2.set_xlabel('Percent of stunting cases averted (%)', size=14)
    # plot
    barwid = 0.5
    h1 = ax.barh(y_pos+0.5-0.5*barwid, stuntingAvertedList, height=barwid, facecolor='#99CCEE', edgecolor='k', linewidth=1.5)
    if save:
        plt.savefig("%s_A5stuntingCasesAverted.png"%(filenamePrefix), bbox_inches='tight')
    else:
        plt.show()





def getSimpleBarFromDictionary(dictionary, label, order):
    import numpy as np
    import matplotlib.pyplot as plt
    from collections import OrderedDict
    
    d = OrderedDict([])
    for i in range(0, len(dictionary)):
        d[order[i]] = dictionary[order[i]]
    
    X = np.arange(len(dictionary))
    plt.bar(X, d.values(), align='center', width=0.5)
    plt.xticks(X, d.keys())
    ymax = 1
    plt.ylim(0, ymax)
    plt.title(label)
    plt.show()

    
def getStuntingStatusesGivenAge(modelList, ageName, lable):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    numYears = int(len(modelList)/12) 
    yearList = list(range(2016, 2016 + numYears + 1))
    xticklist = range(0, len(modelList) + 12, 12)
    ax.set_xticks(xticklist)
    ax.set_xticklabels(yearList)
    
    high = []
    moderate = []
    mild = []
    normal = []
    
    for model in modelList:
        high.append(model.params.stuntingDistribution[ageName]['high'])
        moderate.append(model.params.stuntingDistribution[ageName]['moderate'])
        mild.append(model.params.stuntingDistribution[ageName]['mild'])
        normal.append(model.params.stuntingDistribution[ageName]['normal'])
    
    ax.plot(high, label = 'high')
    ax.plot(moderate, label = 'moderate')
    ax.plot(mild, label = 'mild')
    ax.plot(normal, label = 'normal')
    plt.legend()
    plt.title(ageName + ":  " + lable)
    plt.ylim(0, 1)
    plt.show()
    
def getDeathsAverted(modelList, modelList2, label):
    import numpy as np
    import matplotlib.pyplot as plt
    finalIndex = len(modelList) - 1
    deathsAvertedByAge=[]
    for iAge in range(0, len(modelList[0].ages)):
        deathsAverted = modelList[finalIndex].listOfAgeCompartments[iAge].getCumulativeDeaths() - modelList2[finalIndex].listOfAgeCompartments[iAge].getCumulativeDeaths()
        deathsAvertedByAge.append(deathsAverted)
    X = np.arange(len(modelList[0].ages))
    plt.bar(X, deathsAvertedByAge, align='center', width=0.5)
    plt.xticks(X, modelList[0].ages)
    plt.title('total deaths averted: ' + label)
    plt.show()     
        
def getBudgetPieChartComparison(budgetDictBefore, budgetDictAfter, optimise, fvalBefore, fvalAfter, string):
    # get colour dictionary
    colorStep = 1./float(len(budgetDictAfter))-1.e-2
    plotColor = {}
    run = 1
    for intervention in budgetDictAfter.keys():
        plotColor[intervention] = (1.0-colorStep*run, 1.0-0.23*abs(run-4), 0.0+colorStep*run)
        run += 1
    #tidy up dictionaries    
    budgetDictAfterClean = {}
    budgetDictBeforeClean = {}
    colorsBefore = []
    colorsAfter = []
    for key in sorted(budgetDictBefore.keys()):
        if budgetDictBefore[key] > 1:
            budgetDictBeforeClean[key] = budgetDictBefore[key]
            colorsBefore.append(plotColor[key])
        if budgetDictAfter[key] > 1:
            budgetDictAfterClean[key] = budgetDictAfter[key]   
            colorsAfter.append(plotColor[key])
    from pylab import *
    figure()
    ax1 = subplot(211, aspect='equal', adjustable='box-forced')
    labels = sorted(budgetDictBeforeClean.keys())
    fracs = [budgetDictBeforeClean[key] for key in sorted(budgetDictBeforeClean.keys())] 
    ax1.pie(fracs, labels = labels, colors = colorsBefore)    
    ax1.set_title('before: fval = ' + str(fvalBefore))
    ax2 = subplot(212, aspect='equal', adjustable='box-forced')
    labels = sorted(budgetDictAfterClean.keys())
    fracs = [budgetDictAfterClean[key] for key in sorted(budgetDictAfterClean.keys())]
    ax2.pie(fracs, labels = labels, colors = colorsAfter)
    ax2.set_title('after: fval = ' + str(fvalAfter))
    plt.suptitle('optimising for: ' + optimise + '. ' + string)
    #plt.show()
    plt.savefig(string + '.png')

def plotCoverage(coverageDict, string):
    from pylab import *    
    val = coverageDict.values()    # the bar lengths
    pos = arange(len(coverageDict))+.5    # the bar centers on the y axis
    figure(1)
    barh(pos,val, align='center')
    yticks(pos, coverageDict.keys())
    xlabel('Coverage')
    title(string)
    grid(True)


def plotSpendingAllocation(spendDict, string):
    from pylab import *
    val = spendDict.values()    # the bar lengths
    pos = arange(len(spendDict))+.5    # the bar centers on the y axis
    figure(1)
    barh(pos,val, align='center')
    yticks(pos, spendDict.keys())
    xlabel('Spending')
    title(string)
    grid(True)
    
    
def plotSpendingAndCoverageTogether(spendDict, coverageDict):
    from pylab import *
    f, (ax1, ax2) = plt.subplots(1, 2, sharey=True)
    val = spendDict.values()    # the bar lengths
    pos = arange(len(spendDict))+.5    # the bar centers on the y axis
    ax1.barh(pos,val, align='center')
    yticks(pos, spendDict.keys())
    ax1.set_title('Spending')
    grid(True)
    val = coverageDict.values()    # the bar lengths
    pos = arange(len(coverageDict))+.5    # the bar centers on the y axis
    ax2.barh(pos,val, align='center')
    ax2.set_title('Coverage')
    grid(True)    
    
    
def compareOptimisationOutput(spendDictBefore, spendDictAfter, coverageDictBefore, coverageDictAfter, optimise, string):
    from pylab import *
    f, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, sharex='col', sharey='row')
    
    val = spendDictBefore.values()    # the bar lengths
    pos = arange(len(spendDictBefore))+.5    # the bar centers on the y axis
    ax1.barh(pos,val, align='center')
    ax1.set_yticklabels(spendDictBefore.keys())
    #yticks(pos, spendDict.keys())
    ax1.set_title('spending before')
    ax1.grid(True)
    
    val = coverageDictBefore.values()    # the bar lengths
    pos = arange(len(coverageDictBefore))+.5    # the bar centers on the y axis
    ax2.barh(pos,val, align='center')
    ax2.set_title('coverage before')
    ax2.grid(True)        
    
    val = spendDictAfter.values()    # the bar lengths
    pos = arange(len(spendDictAfter))+.5    # the bar centers on the y axis
    ax3.barh(pos,val, align='center')
    ax3.set_yticklabels(spendDictAfter.keys())
    ax3.set_title('spending after')
    ax3.grid(True)
    
    val = coverageDictAfter.values()    # the bar lengths
    pos = arange(len(coverageDictAfter))+.5    # the bar centers on the y axis
    ax4.barh(pos,val, align='center')
    ax4.set_title('coverage after')
    ax4.grid(True)        
    
    plt.suptitle('optimising for: ' + optimise + '. ' + string)
    #plt.show()
    plt.savefig(string + '.png')
    
    
