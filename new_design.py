# -*- coding: utf-8 -*-
"""
Created on Wed Feb 24 13:43:14 2016

@author: ruthpearson
"""

class FertileWomen:
    def __init__(self, birthRate, populationSize):
        self.birthRate = birthRate
        self.populationSize = populationSize

class Box:
    def __init__(self, stuntStatus, wasteStatus, populationSize, mortalityRate):
        self.stuntStatus =  stuntStatus
        self.wasteStatus = wasteStatus
        self.populationSize = populationSize
        self.mortalityRate = mortalityRate
        self.cumulativeDeaths = 0

class AgeCompartment:
    def __init__(self, name, listOfBoxes, agingRate, stuntDict, wasteDict):
        self.name = name  
        self.listOfBoxes = listOfBoxes
        self.agingRate = agingRate
        self.stuntDict = stuntDict
        self.wasteDict = wasteDict
        
class Model:
    def __init__(self, name, fertileWomen, listOfAgeCompartments):
        self.name = name
        self.listOfAgeCompartments = listOfAgeCompartments
        
    def applyMortality(self):
        for ageGroup in self.listOfAgeCompartments:
            for box in ageGroup.listOfBoxes:
                deaths = box.populationSize * box.mortalityRate
                box.populationSize -= deaths
                box.cumulativeDeaths += deaths
        
                
    def applyAging(self):
        unagedListOfAgeCompartments = self.listOfAgeCompartments
        for group in range(1, len(self.listOfAgeCompartments)):
            
            addThese = self.listOfAgeCompartments[group-1]
            minusThese = 1
        
    def moveOneTimeStep(self):
        self.applyMortality()
        self.applyAging()
        
        
        
        
        
                