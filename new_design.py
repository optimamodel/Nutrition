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
    def __init__(self, stuntStatus, wasteStatus, breastFeedingStatus, populationSize, mortalityRate):
        self.stuntStatus =  stuntStatus
        self.wasteStatus = wasteStatus
        self.breastFeedingStatus = breastFeedingStatus
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
        self.fertileWomen = fertileWomen
        self.listOfAgeCompartments = listOfAgeCompartments
        
    def applyMortality(self):
        for ageGroup in self.listOfAgeCompartments:
            for stuntingStatus in ["normal", "mild", "moderate", "high"]:
                for wastingStatus in ["normal", "mild", "moderate", "high"]:
                    for breastFeedingStatus in ["exclusive", "predominant", "partial", "none"]:
                        deaths = ageGroup.dictOfBoxes[stuntingStatus][wastingStatus][breastFeedingStatus].populationSize * ageGroup.dictOfBoxes[stuntingStatus][wastingStatus][breastFeedingStatus].mortalityRate
                        ageGroup.dictOfBoxes[stuntingStatus][wastingStatus][breastFeedingStatus].populationSize -= deaths
                        ageGroup.dictOfBoxes[stuntingStatus][wastingStatus][breastFeedingStatus].cumulativeDeaths += deaths
        
                
    def applyAging(self):
        #currently there is no movement between statuses when aging 
        numCompartments = len(self.listOfAgeCompartments)
        for stuntingStatus in ["normal", "mild", "moderate", "high"]:
            for wastingStatus in ["normal", "mild", "moderate", "high"]:
                for breastFeedingStatus in ["exclusive", "predominant", "partial", "none"]:
                    aging = [0.]*numCompartments
                    for ind in range(1, numCompartments):
                        youngerCompartment = self.listOfAgeCompartments[ind-1]
                        youngerBox = youngerCompartment.dictOfBoxes[stuntingStatus][wastingStatus][breastFeedingStatus] 
                        numAging = int(youngerBox.populationSize * youngerCompartment.agingRate)
                        aging[ind]   += numAging
                        aging[ind-1] -= numAging
                    
                    #remember to age people out of the last age compartment
                    ageOut = self.listOfAgeCompartments[numCompartments-1].dictOfBoxes[stuntingStatus][wastingStatus][breastFeedingStatus].populationSize * self.listOfAgeCompartments[numCompartments-1].agingRate    
                    aging[numCompartments-1] -= ageOut 
                    for ageCompartment in range(0, numCompartments):
                        self.listOfAgeCompartments[ageCompartment].dictOfBoxes[stuntingStatus][wastingStatus][breastFeedingStatus].populationSize += aging[ageCompartment]
                   
                
        
    def applyBirths(self):
        #PLACE HOLDER CODE
        x=2
        return x
        
        
    def updateMortalityRate(self, data, underlyingMortality):
        for ageGroup in self.listOfAgeCompartments:
            age = ageGroup.name
            for stuntingStatus in ["normal", "mild", "moderate", "high"]:
                for wastingStatus in ["normal", "mild", "moderate", "high"]:
                    for breastFeedingStatus in ["exclusive", "predominant", "partial", "none"]:
                        count = 0                        
                        for cause in data.causesOfDeath:
                            t1 = underlyingMortality[age]    
                            t2 = data.causeOfDeathByAge[cause][age]
                            t3 = data.RRStunting[cause][stuntingStatus][age]
                            t4 = data.RRWasting[cause][wastingStatus][age]
                            t5 = data.RRBreastFeeding[cause][breastFeedingStatus][age]
                            count += t1 * t2 * t3 * t4 * t5                            
                        ageGroup.dictOfBoxes[stuntingStatus][wastingStatus][breastFeedingStatus].mortalityRate = count
       
    
    def moveOneTimeStep(self):
        self.updateMortalityRate()
        self.applyMortality()
        self.applyAging()
        self.applyBirths()
        
        
        
        
        
                
