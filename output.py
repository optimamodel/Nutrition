# -*- coding: utf-8 -*-
"""
Created on Fri Mar 11 11:50:20 2016

@author: ruth
"""


def getPopSizeByAgePlot(modelList):
    ageList = modelList[0].ages
    #get population size for each age group
    popSize = {}
    for age in range(0, len(modelList[0].ages)):
        popSize[age] = 0
        countArray = []
        for model in modelList:
            count = 0            
            for stuntingStatus in ["normal", "mild", "moderate", "high"]:
                for wastingStatus in ["normal", "mild", "moderate", "high"]:
                    for breastfeedingStatus in ["exclusive", "predominant", "partial", "none"]:
                        count += model.listOfAgeCompartments[age].dictOfBoxes[stuntingStatus][wastingStatus][breastfeedingStatus].populationSize
            countArray.append(count)
        popSize[age] = countArray      
            
        
    
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
    plt.ylabel('population size')
    plt.xlabel('time steps in months')
    plt.title('Population Size by Age Group')
    plt.show()
    
    return popSize


def getCumulativeDeathsByAgePlot(modelList):
    ageList = modelList[0].ages
    #get population size for each age group
    cumulativeDeaths = {}
    for age in range(0, len(modelList[0].ages)):
        cumulativeDeaths[age] = 0
        countArray = []
        for model in modelList:
            count = 0            
            for stuntingStatus in ["normal", "mild", "moderate", "high"]:
                for wastingStatus in ["normal", "mild", "moderate", "high"]:
                    for breastfeedingStatus in ["exclusive", "predominant", "partial", "none"]:
                        count += model.listOfAgeCompartments[age].dictOfBoxes[stuntingStatus][wastingStatus][breastfeedingStatus].cumulativeDeaths
            countArray.append(count)
        cumulativeDeaths[age] = countArray            
    
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
    ax.legend(ageList, loc = 'upper left')
    plt.ylabel('cumulative deaths')
    plt.xlabel('time steps in months')
    plt.title('Cumulative Deaths by Age Group')
    plt.show()
    
def getNumStuntedByAgePlot(modelList):
    #this counts people in the top 2 stunting categories
    ageList = modelList[0].ages
    #get population size for each age group
    numStunted = {}
    for age in range(0, len(modelList[0].ages)):
        numStunted[age] = 0
        countArray = []
        for model in modelList:
            count = 0            
            for stuntingStatus in ["moderate", "high"]:
                for wastingStatus in ["normal", "mild", "moderate", "high"]:
                    for breastfeedingStatus in ["exclusive", "predominant", "partial", "none"]:
                        count += model.listOfAgeCompartments[age].dictOfBoxes[stuntingStatus][wastingStatus][breastfeedingStatus].populationSize
            countArray.append(count)
        numStunted[age] = countArray            
    
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
    ax.legend(ageList, loc = 'upper left')
    plt.ylabel('number of people stunted')
    plt.xlabel('time steps in months')
    plt.title('Number of People Stunted by Age Group')
    plt.show()
    
    
def getStuntedPercent(modelList): # NOT WORKING YET
    from operator import truediv    
    #this counts people in the top 2 stunting categories as stunted
    ageList = modelList[0].ages
    #get population size for each age group
    percentStunted = {}
    for age in range(0, len(modelList[0].ages)):
        percentStunted[age] = 0
        
        # count STUNTED 
        countArray = []
        for model in modelList:
            count = 0            
            for stuntingStatus in ["moderate", "high"]:
                for wastingStatus in ["normal", "mild", "moderate", "high"]:
                    for breastfeedingStatus in ["exclusive", "predominant", "partial", "none"]:
                        count += model.listOfAgeCompartments[age].dictOfBoxes[stuntingStatus][wastingStatus][breastfeedingStatus].populationSize
            countArray.append(count)
            
        # count NOT STUNTED 
        countArrayN = []
        for model in modelList:
            count = 0            
            for stuntingStatus in ["normal", "mild"]:
                for wastingStatus in ["normal", "mild", "moderate", "high"]:
                    for breastfeedingStatus in ["exclusive", "predominant", "partial", "none"]:
                        count += model.listOfAgeCompartments[age].dictOfBoxes[stuntingStatus][wastingStatus][breastfeedingStatus].populationSize
            countArrayN.append(count)
            
            
        percentStunted[age] = map(truediv, countArray, countArrayN)     
    
    import numpy as np
    import matplotlib.pyplot as plt
    
    x = np.arange(len(modelList))
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
    ax.set_xticklabels(x[:]+1)
    ax.set_ylabel('% of people stunted')
    ax.set_xlabel('time steps in months')
    ax.set_title('Percent of People Stunted by Age Group')
    plt.show()    
