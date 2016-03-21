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
                        deaths = ageGroup.dictOfBoxes[stuntingStatus][wastingStatus][breastfeedingStatus].populationSize * ageGroup.dictOfBoxes[stuntingStatus][wastingStatus][breastfeedingStatus].mortalityRate * self.timestep
                        ageGroup.dictOfBoxes[stuntingStatus][wastingStatus][breastfeedingStatus].populationSize -= deaths
                        ageGroup.dictOfBoxes[stuntingStatus][wastingStatus][breastfeedingStatus].cumulativeDeaths += deaths



    def applyAging(self,data):
        import helper as helperCode
        helper = helperCode.Helper()
        numCompartments = len(self.listOfAgeCompartments)
        # calculate how many people are aging out of each box
        agingOut = [None]*numCompartments
        for ind in range(0, numCompartments):
            thisCompartment = self.listOfAgeCompartments[ind]
            agingOut[ind] = {}
            for wastingCat in ["normal", "mild", "moderate", "high"]:
                agingOut[ind][wastingCat] = {}
                for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
                    agingOut[ind][wastingCat][breastfeedingCat] = {}
                    for stuntingCat in ["normal", "mild", "moderate", "high"]:
                        thisBox = thisCompartment.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat] 
                        agingOut[ind][wastingCat][breastfeedingCat][stuntingCat] = thisBox.populationSize * thisCompartment.agingRate  # * self.timestep
        # first age group does not have aging in
        newborns = self.listOfAgeCompartments[0]
        for wastingCat in ["normal", "mild", "moderate", "high"]:
            for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
                for stuntingCat in ["normal", "mild", "moderate", "high"]:
                    newbornBox = newborns.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat]
                    newbornBox.populationSize -= agingOut[0][wastingCat][breastfeedingCat][stuntingCat]
        # for older age groups, you need to decide if people stayed stunted from previous age group
        for ind in range(1, numCompartments):
            ageName = self.ages[ind]
            thisAgeCompartment = self.listOfAgeCompartments[ind]
            restratIfPreviously    = helper.restratify(self.constants.probStuntedIfPreviously[ageName])
            restratIfNotPreviously = helper.restratify(self.constants.probStuntedIfNotPreviously[ageName])
            for wastingCat in ["normal", "mild", "moderate", "high"]:
                numAgingInNotStunted = 0.
                numAgingInStunted    = 0.
                for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
                    numAgingInNotStunted += agingOut[ind-1][wastingCat][breastfeedingCat]["normal"] + agingOut[ind-1][wastingCat][breastfeedingCat]["mild"]
                    numAgingInStunted    += agingOut[ind-1][wastingCat][breastfeedingCat]["moderate"] + agingOut[ind-1][wastingCat][breastfeedingCat]["high"]
                for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
                    for stuntingCat in ["normal","mild","moderate","high"]:
                        thisBox = thisAgeCompartment.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat]
                        thisBox.populationSize -= agingOut[ind][wastingCat][breastfeedingCat][stuntingCat]
                        thisBox.populationSize += numAgingInNotStunted * restratIfNotPreviously[stuntingCat] * data.breastfeedingDistribution[breastfeedingCat][ageName]
                        thisBox.populationSize += numAgingInStunted    * restratIfPreviously[stuntingCat]    * data.breastfeedingDistribution[breastfeedingCat][ageName]



    def applyBirths(self,data):
        # calculate total number of new babies
        birthRate = self.fertileWomen.birthRate  #WARNING: assuming per pre-determined timestep
        numWomen  = self.fertileWomen.populationSize
        numNewBabies = numWomen * birthRate * self.timestep
        # see constants.py for calculation of baseline probability of birth outcome
        # now calculate stunting probability accordingly
        for stuntingCat in ["normal", "mild", "moderate", "high"]:
            for wastingCat in ["normal", "mild", "moderate", "high"]:
                for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
                    stuntingFraction = data.stuntingDistribution[stuntingCat]["<1 month"] # WARNING PLACEHOLDER
                    self.listOfAgeCompartments[0].dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize += numNewBabies * data.wastingDistribution[wastingCat]["<1 month"] * data.breastfeedingDistribution[breastfeedingCat]["<1 month"] * stuntingFraction



        
    def updateMortalityRate(self, data):
        for ageGroup in self.listOfAgeCompartments:
            age = ageGroup.name
            for stuntingCat in ["normal", "mild", "moderate", "high"]:
                for wastingCat in ["normal", "mild", "moderate", "high"]:
                    for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
                        count = 0                        
                        for cause in data.causesOfDeath:
                            t1 = self.constants.underlyingMortalityByAge[age]    
                            t2 = data.causeOfDeathByAge[cause][age]
                            t3 = data.RRStunting[cause][stuntingCat][age]
                            t4 = data.RRWasting[cause][wastingCat][age]
                            t5 = data.RRBreastfeeding[cause][breastfeedingCat][age]
                            count += t1 * t2 * t3 * t4 * t5                            
                        ageGroup.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].mortalityRate = count

    


    def moveOneTimeStep(self,data):
        self.updateMortalityRate(data)
        self.applyMortality()
        self.applyAging(data)
        self.applyBirths(data)
        
        
