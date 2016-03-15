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
    
    p1 = plt.bar(x,percentStunted[0])
    p2 = plt.bar(x,percentStunted[1])
    #y3 = percentStunted[2]
    #y4 = percentStunted[3]
    #y5 = percentStunted[4]
    
    #fig, ax = plt.subplots()
    #ax.stackplot(x, y1, y2, y3, y4, y5)
    #ax.legend(ageList, loc = 'upper left')
    plt.ylabel('% of people stunted')
    plt.xlabel('time steps in months')
    plt.title('Percent of People Stunted by Age Group')
    plt.legend((p1[0], p2[0]),('thing 1', 'thing 2'))
    plt.show()    
