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
    def __init__(self, stuntStatus, wasteStatus, breastfeedingStatus, populationSize, mortalityRate):
        self.stuntStatus =  stuntStatus
        self.wasteStatus = wasteStatus
        self.breastfeedingStatus = breastfeedingStatus
        self.populationSize = populationSize
        self.mortalityRate = mortalityRate
        self.cumulativeDeaths = 0

class AgeCompartment:
    def __init__(self, name, dictOfBoxes, agingRate):
        self.name = name  
        self.dictOfBoxes = dictOfBoxes
        self.agingRate = agingRate

        
class Model:
    def __init__(self, name, fertileWomen, listOfAgeCompartments, ages, timestep):
        self.name = name
        self.fertileWomen = fertileWomen
        self.listOfAgeCompartments = listOfAgeCompartments
        self.ages = ages
        self.timestep = timestep
        self.constants = 0
        
    def setConstants(self, inputConstants):
        self.constants = inputConstants
        
    
    def applyMortality(self):
        for ageGroup in self.listOfAgeCompartments:
            for stuntingStatus in ["normal", "mild", "moderate", "high"]:
                for wastingStatus in ["normal", "mild", "moderate", "high"]:
                    for breastfeedingStatus in ["exclusive", "predominant", "partial", "none"]:
                        deaths = ageGroup.dictOfBoxes[stuntingStatus][wastingStatus][breastfeedingStatus].populationSize * ageGroup.dictOfBoxes[stuntingStatus][wastingStatus][breastfeedingStatus].mortalityRate
                        ageGroup.dictOfBoxes[stuntingStatus][wastingStatus][breastfeedingStatus].populationSize -= deaths
                        ageGroup.dictOfBoxes[stuntingStatus][wastingStatus][breastfeedingStatus].cumulativeDeaths += deaths



    def applyAging(self):
        numCompartments = len(self.listOfAgeCompartments)
        for wastingStatus in ["normal", "mild", "moderate", "high"]:
            for breastfeedingStatus in ["exclusive", "predominant", "partial", "none"]:
                # calculate how many people are aging out of each box
                agingOut = [None]*numCompartments
                for ind in range(0, numCompartments):
                    agingOut[ind] = {}
                    for stuntingStatus in ["normal", "mild", "moderate", "high"]:
                        thisCompartment = self.listOfAgeCompartments[ind]
                        thisBox = thisCompartment.dictOfBoxes[stuntingStatus][wastingStatus][breastfeedingStatus] 
                        numAging = int(thisBox.populationSize * thisCompartment.agingRate)
                        agingOut[ind][stuntingStatus] = numAging
                # first age group does not have aging in
                newborns = self.listOfAgeCompartments[0]
                for stuntingStatus in ["normal", "mild", "moderate", "high"]:
                    newbornBox = newborns.dictOfBoxes[stuntingStatus][wastingStatus][breastfeedingStatus]
                    newbornBox.populationSize -= agingOut[0][stuntingStatus]
                # for older age groups, you need to decide if people stayed stunted from previous age group
                for ind in range(1, numCompartments):
                    ageName = self.ages[ind]
                    thisAgeCompartment = self.listOfAgeCompartments[ind]
                    # non-stunted levels
                    for nonStuntedLevel in ["normal","mild","moderate"]:
                        thisBox = thisAgeCompartment.dictOfBoxes[nonStuntedLevel][wastingStatus][breastfeedingStatus]
                        thisBox.populationSize -= agingOut[ind][nonStuntedLevel]
                        thisBox.populationSize += (1. - self.constants.probStuntedIfNotPreviously[ageName]) * agingOut[ind-1][nonStuntedLevel]
                        thisBox.populationSize += (1. - self.constants.probStuntedIfPreviously[ageName]) * agingOut[ind-1]["high"]
                    # high stunting
                    thisBox = thisAgeCompartment.dictOfBoxes["high"][wastingStatus][breastfeedingStatus]
                    thisBox.populationSize -= agingOut[ind]["high"]
                    thisBox.populationSize += self.constants.probStuntedIfPreviously[ageName]*agingOut[ind-1]["high"]
                    for nonStuntedLevel in ["normal","mild","moderate"]:
                        thisBox.populationSize += self.constants.probStuntedIfNotPreviously[ageName]*agingOut[ind-1][nonStuntedLevel]
                    
        


    def applyBirths(self,data):
        # calculate total number of new babies
        birthRate = self.fertileWomen.birthRate  #WARNING: assuming per pre-determined timestep
        numWomen  = self.fertileWomen.populationSize
        numNewBabies = numWomen * birthRate
        # see constants.py for calculation of baseline probability of birth outcome
        # now calculate stunting probability accordingly
        for stuntingStatus in ["normal", "mild", "moderate", "high"]:
            for wastingStatus in ["normal", "mild", "moderate", "high"]:
                for breastfeedingStatus in ["exclusive", "predominant", "partial", "none"]:
                    stuntingFraction = 0.2 # WARNING PLACEHOLDER
                    self.listOfAgeCompartments[0].dictOfBoxes[stuntingStatus][wastingStatus][breastfeedingStatus].populationSize += numNewBabies * data.wastingDistribution[wastingStatus]["<1 month"] * data.breastfeedingDistribution[breastfeedingStatus]["<1 month"] * stuntingFraction



        
    def updateMortalityRate(self, data):
        for ageGroup in self.listOfAgeCompartments:
            age = ageGroup.name
            for stuntingStatus in ["normal", "mild", "moderate", "high"]:
                for wastingStatus in ["normal", "mild", "moderate", "high"]:
                    for breastfeedingStatus in ["exclusive", "predominant", "partial", "none"]:
                        count = 0                        
                        for cause in data.causesOfDeath:
                            t1 = self.constants.underlyingMortalityByAge[age]    
                            t2 = data.causeOfDeathByAge[cause][age]
                            t3 = data.RRStunting[cause][stuntingStatus][age]
                            t4 = data.RRWasting[cause][wastingStatus][age]
                            t5 = data.RRBreastfeeding[cause][breastfeedingStatus][age]
                            count += t1 * t2 * t3 * t4 * t5                            
                        ageGroup.dictOfBoxes[stuntingStatus][wastingStatus][breastfeedingStatus].mortalityRate = count

    


    def moveOneTimeStep(self):
        self.updateMortalityRate()
        self.applyMortality()
        self.applyAging()
        self.applyBirths()
        
        
