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
    def __init__(self, name, listOfBoxes, agingRate):
        self.name = name  
        self.listOfBoxes = listOfBoxes
        self.agingRate = agingRate
        
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
        numCompartments = len(self.listOfAgeCompartments)
        unagedListOfAgeCompartments = self.listOfAgeCompartments
        for ind in range(1, len(self.listOfAgeCompartments)):
            youngerBoxes = unagedListOfAgeCompartments[ind-1].listOfBoxes
            for stuntingStatus in ["mild","moderate","high","severe"]:
                for wastingStatus in ["mild","moderate","high","severe"]:
#                    youngerBox = youngerBoxes[stuntingStatus][wastingStatus]
#                    numAging = youngerBoxes.populationSize
            numStuntedAging    = youngerBoxes.conditions.stuntedPopulationSize    * youngerBoxes.parameters.agingRate
            numNonStuntedAging = youngerBoxes.conditions.nonStuntedPopulationSize * youngerBoxes.parameters.agingRate
            aging[ind]['stunted']      += numStuntedAging
            aging[ind-1]['stunted']    -= numStuntedAging
            aging[ind]['nonStunted']   += numNonStuntedAging
            aging[ind-1]['nonStunted'] -= numNonStuntedAging
        for ind in range(numCompartments):
            self.compartmentList[ind].conditions.stuntedPopulationSize    += aging[ind]['stunted']
            self.compartmentList[ind].conditions.nonStuntedPopulationSize += aging[ind]['nonStunted']

        
    def moveOneTimeStep(self):
        self.applyMortality()
        self.applyAging()
        
        
        
        
        
                
