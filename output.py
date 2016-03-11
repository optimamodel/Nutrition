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
