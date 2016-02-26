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
    def __init__(self, name, dictOfBoxes, agingRate):
        self.name = name  
        self.dictOfBoxes = dictOfBoxes
        self.agingRate = agingRate

        
class Model:
    def __init__(self, name, fertileWomen, listOfAgeCompartments):
        self.name = name
        self.listOfAgeCompartments = listOfAgeCompartments
        
    def applyMortality(self):
        for ageGroup in self.listOfAgeCompartments:
            for stuntingStatus in ["normal", "mild", "moderate", "high"]:
                for wastingStatus in ["normal", "mild", "moderate", "high"]:
                    deaths = ageGroup.dictOfBoxes[stuntingStatus][wastingStatus].populationSize * ageGroup.dictOfBoxes[stuntingStatus][wastingStatus].mortalityRate
                    ageGroup.dictOfBoxes[stuntingStatus][wastingStatus].populationSize -= deaths
                    ageGroup.dictOfBoxes[stuntingStatus][wastingStatus].cumulativeDeaths += deaths
        
                
    def applyAging(self):
        numCompartments = len(self.listOfAgeCompartments)
        for stuntingStatus in ["normal", "mild", "moderate", "high"]:
            for wastingStatus in ["normal", "mild", "moderate", "high"]:
                aging = [0.]*numCompartments
                for ind in range(1, numCompartments):
                    youngerCompartment = self.listOfAgeCompartments[ind-1]
                    youngerBox = youngerCompartment.dictOfBoxes[stuntingStatus][wastingStatus] 
                    numAging = int(youngerBox.populationSize * youngerCompartment.agingRate)
                    aging[ind]   += numAging
                    aging[ind-1] -= numAging
                    
                #remember to age people out of the last age compartment
                #ageOut = self.listOfAgeCompartments[numCompartments].dictOfBoxes[stuntingStatus][wastingStatus].populationSize * self.listOfAgeCompartments[numCompartments].agingRate    
                #aging[numCompartments] -= ageOut 
                for ageCompartment in range(0, numCompartments):
                    self.listOfAgeCompartments[ageCompartment].dictOfBoxes[stuntingStatus][wastingStatus].populationSize += aging[ageCompartment]
                   
                
        
    def applyBirths(self):
        #PLACE HOLDER CODE
        x=2
        return x
    
    def moveOneTimeStep(self):
        self.applyMortality()
        self.applyAging()
        self.applyBirths()
        
        
        
        
        
                
