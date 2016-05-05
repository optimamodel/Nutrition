# -*- coding: utf-8 -*-
"""
Created on Fri Mar 11 11:50:20 2016

@author: ruth
"""
from __future__ import division


def getPopSizeByAgePlot(modelList, label):
    ageList = modelList[0].ages
    #get population size for each age group
    popSize = {}
    for age in range(0, len(modelList[0].ages)):
        popSize[age] = 0
        countThis = []
        for model in modelList:
            count = 0            
            for stuntingCat in ["normal", "mild", "moderate", "high"]:
                for wastingCat in ["normal", "mild", "moderate", "high"]:
                    for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
                        count += model.listOfAgeCompartments[age].dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize
            countThis.append(count)
        popSize[age] = countThis      
    
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
    for age in range(0, numAges):
        totalPop.append([])
        stuntPop.append([])
        m=0
        for model in modelList:
            total     = model.listOfAgeCompartments[age].getTotalPopulation()
            stuntfrac = model.listOfAgeCompartments[age].getStuntedFraction()
            totalPop[age].append(total)
            stuntPop[age].append(total*stuntfrac)
            totalPopU5[m] += total
            stuntPopU5[m] += total*stuntfrac
            m+=1

    #get some x axis stuff    
    numYears = int(len(modelList)/12)
    yearList = list(range(2016, 2016+numYears+1))#[2016]
    xTickList = list(range(0, 12*(numYears+1), 12)) # [0]
    #for i in range(1, numYears):
        #yearList.append(yearList[0] + i)   
        #xTickList.append(i * 12)
    
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
    #for age in range(0, len(modelList[0].ages)):
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
    for age in range(0, len(modelList[0].ages)):
        cumulativeDeaths[age] = 0
        countThis = []
        for model in modelList:
            count = 0            
            for stuntingCat in ["normal", "mild", "moderate", "high"]:
                for wastingCat in ["normal", "mild", "moderate", "high"]:
                    for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
                        count += model.listOfAgeCompartments[age].dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].cumulativeDeaths
            countThis.append(count)
        cumulativeDeaths[age] = countThis  

    
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
    for age in range(0, len(modelList[0].ages)):
        numStunted[age] = 0
        countThis = []
        for model in modelList:
            count = 0            
            for stuntingCat in ["moderate", "high"]:
                for wastingCat in ["normal", "mild", "moderate", "high"]:
                    for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
                        count += model.listOfAgeCompartments[age].dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize
            countThis.append(count)
        numStunted[age] = countThis      
        
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
    
    
    
def getStuntedPercent(modelList, label): 
    import numpy as np
    ageList = modelList[0].ages
    percentStunted = {}
    for age in range(0, len(modelList[0].ages)):
        StuntedFracList = []
        for model in modelList:
            StuntedFrac = model.listOfAgeCompartments[age].getStuntedFraction()
            StuntedFracList.append(StuntedFrac)
        #get yearly average
        numYears = int(len(modelList)/12)
        yearAveStuntedPerc = []
        for year in range(1, numYears+1):
            yearAveStuntedPerc.append(100.*np.average(StuntedFracList[(year - 1) * 12 : (year * 12) - 1]))
        percentStunted[age] = yearAveStuntedPerc
    yearList = [2017]
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

    
    
def getCombinedPlots(numRuns, data): #modelList1, tag1, modelList2, tag2):
    # set up
    totalPopU5 = {}
    stuntPopU5 = {}
    for run in range(numRuns):
        modelList = data[run]["modelList"]
        tag       = data[run]["tag"]
        ageList = modelList[0].ages
        numAges = len(ageList)
        numMonths = len(modelList) 
        # initialise
        totalPopU5[tag] = [0.]*numMonths
        stuntPopU5[tag] = [0.]*numMonths
        totalPop = []
        stuntPop = []
        for age in range(numAges):
            totalPop.append([])
            stuntPop.append([])
            m=0
            for model in modelList:
                total     = model.listOfAgeCompartments[age].getTotalPopulation()
                stuntfrac = model.listOfAgeCompartments[age].getStuntedFraction()
                totalPop[age].append(total)
                stuntPop[age].append(total*stuntfrac)
                totalPopU5[tag][m] += total
                stuntPopU5[tag][m] += total*stuntfrac
                m+=1


    stuntFracU5 = {}
    for run in range(numRuns):
        tag       = data[run]["tag"]
        stuntFracU5[tag] = [0.]*numMonths
        for m in range(numMonths):
            stuntFracU5[tag][m] = stuntPopU5[tag][m] / totalPopU5[tag][m]


    import numpy as np
    import matplotlib.pyplot as plt
    numYears = int(len(modelList)/12)
    skip = 2
    yearList =  list(range(2016, 2016+numYears+1, skip))#[2016]
    xTickList = list(range(0, 12*(numYears+1),    skip*12)) # [0]
    x = np.arange(numMonths)

    fig, ax = plt.subplots()
    ax.set_xticks(xTickList)
    ax.set_xticklabels(yearList)
    ax.set_xlim([0, 12*numYears])
    plt.ylabel('Stunted population size')
    #plt.title('Total and Stunted Population Size : %s'%(label))
    #plot_total = plt.fill_between(x, totalPopU5, stuntPopU5, color='blue')
    for run in range(numRuns):
        tag       = data[run]["tag"]
        color     = data[run]["color"]
        plot_stunt = plt.fill_between(x, stuntPopU5[tag], 0, color=color)
    #ax.legend([plot_total, plot_stunt], ["Total", "Stunted"])
        #ax.legend([plot_total, plot_stunt], ["Total", "Stunted"])
    plt.show()


    fig, ax = plt.subplots()
    ax.set_xticks(xTickList)
    ax.set_xticklabels(yearList)
    ax.set_xlim([0, 12*numYears])
    plt.ylabel('Stunted prevalence')
    for run in range(numRuns):
        tag       = data[run]["tag"]
        color     = data[run]["color"]
        plot_stunt = plt.fill_between(x, stuntFracU5[tag], 0, color=color)
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

    
def getStuntingStatusesGivenAge(modelList, age, lable):
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
        high.append(model.params.stuntingDistribution[age]['high'])
        moderate.append(model.params.stuntingDistribution[age]['moderate'])
        mild.append(model.params.stuntingDistribution[age]['mild'])
        normal.append(model.params.stuntingDistribution[age]['normal'])
    
    ax.plot(high, label = 'high')
    ax.plot(moderate, label = 'moderate')
    ax.plot(mild, label = 'mild')
    ax.plot(normal, label = 'normal')
    plt.legend()
    plt.title(age + ":  " + lable)
    plt.ylim(0, 1)
    plt.show()
    
    
    
    
    
    
