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
        # unagedListOfAgeCompartments = self.listOfAgeCompartments # I think this doesn't make a copy of the list, but just points to the same address in memory, so dangerous to use as we are
        for stuntingStatus in ["mild","moderate","high","severe"]:
            for wastingStatus in ["mild","moderate","high","severe"]:
                aging = [0.]*numCompartments
                for ind in range(0, numCompartments):
                    youngerCompartment = self.listOfAgeCompartments[ind-1]
                    #youngerBoxes = youngerCompartment.allBoxes
                    youngerBox = youngerBoxes[stuntingStatus][wastingStatus] #need to be able to search for box
                    numAging = int(youngerBox.populationSize * youngerCompartment.agingRate)
                    aging[ind]   += numAging
                    aging[ind-1] -= numAging
                for ind in range(numCompartments):
                    self.listOfAgeCompartments[ind].allBoxes[stuntingStatus][wastingStatus].populationSize += aging[ind]

        
    def moveOneTimeStep(self):
        self.applyMortality()
        self.applyAging()
        
        
        
        
        
                
