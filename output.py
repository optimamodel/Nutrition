# -*- coding: utf-8 -*-
"""
Created on Fri Mar 11 11:50:20 2016

@author: ruth
"""


def getPopSizeByAgePlot(modelList, label):
    ageList = modelList[0].ages
    #get population size for each age group
    popSize = {}
    for age in range(0, len(modelList[0].ages)):
        popSize[age] = 0
        countThis = []
        for model in modelList:
            count = 0            
            for stuntingStatus in ["normal", "mild", "moderate", "high"]:
                for wastingStatus in ["normal", "mild", "moderate", "high"]:
                    for breastfeedingStatus in ["exclusive", "predominant", "partial", "none"]:
                        count += model.listOfAgeCompartments[age].dictOfBoxes[stuntingStatus][wastingStatus][breastfeedingStatus].populationSize
            countThis.append(count)
        popSize[age] = countThis      
    
    #get some x axis stuff    
    numYears = len(modelList)/12         
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


def getCumulativeDeathsByAgePlot(modelList, label):
    ageList = modelList[0].ages
    #get population size for each age group
    cumulativeDeaths = {}
    for age in range(0, len(modelList[0].ages)):
        cumulativeDeaths[age] = 0
        countThis = []
        for model in modelList:
            count = 0            
            for stuntingStatus in ["normal", "mild", "moderate", "high"]:
                for wastingStatus in ["normal", "mild", "moderate", "high"]:
                    for breastfeedingStatus in ["exclusive", "predominant", "partial", "none"]:
                        count += model.listOfAgeCompartments[age].dictOfBoxes[stuntingStatus][wastingStatus][breastfeedingStatus].cumulativeDeaths
            countThis.append(count)
        cumulativeDeaths[age] = countThis            
    
    #get some x axis stuff    
    numYears = len(modelList)/12         
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
            for stuntingStatus in ["moderate", "high"]:
                for wastingStatus in ["normal", "mild", "moderate", "high"]:
                    for breastfeedingStatus in ["exclusive", "predominant", "partial", "none"]:
                        count += model.listOfAgeCompartments[age].dictOfBoxes[stuntingStatus][wastingStatus][breastfeedingStatus].populationSize
            countThis.append(count)
        numStunted[age] = countThis      
        
    #get some x axis stuff    
    numYears = len(modelList)/12         
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
    
    
def getStuntedPercent(modelList, label): # NOT WORKING YET
    from operator import truediv  
    import numpy as np
    #this counts people in the top 2 stunting categories as stunted
    ageList = modelList[0].ages
    #get population size for each age group
    percentStunted = {}
    for age in range(0, len(modelList[0].ages)):
        percentStunted[age] = 0
        
        # count STUNTED 
        countThis = []
        for model in modelList:
            count = 0            
            for stuntingStatus in ["moderate", "high"]:
                for wastingStatus in ["normal", "mild", "moderate", "high"]:
                    for breastfeedingStatus in ["exclusive", "predominant", "partial", "none"]:
                        count += model.listOfAgeCompartments[age].dictOfBoxes[stuntingStatus][wastingStatus][breastfeedingStatus].populationSize
            countThis.append(count)
            
        # count NOT STUNTED 
        countThisN = []
        for model in modelList:
            count = 0            
            for stuntingStatus in ["normal", "mild"]:
                for wastingStatus in ["normal", "mild", "moderate", "high"]:
                    for breastfeedingStatus in ["exclusive", "predominant", "partial", "none"]:
                        count += model.listOfAgeCompartments[age].dictOfBoxes[stuntingStatus][wastingStatus][breastfeedingStatus].populationSize
            countThisN.append(count)
            
        
        #get yearly average
        numYears = len(modelList)/12 
        yearAveStunted = []
        yearAveNotStunted = []
        for year in range(1, numYears+1):
            yearAveStunted.append(np.average(countThis[(year - 1) * 12 : (year * 12) - 1]))
            yearAveNotStunted.append(np.average(countThisN[(year - 1) * 12 : (year * 12) - 1]))
            
        percentStunted[age] = map(truediv, yearAveStunted, yearAveNotStunted)    
        
    yearList = [2017]
    for i in range(1, numYears):
        yearList.append(yearList[0] + i)
    
    import numpy as np
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
