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
    def __init__(self, stuntCat, wasteCat, breastfeedingCat, populationSize, mortalityRate):
        self.stuntCat =  stuntCat
        self.wasteCat = wasteCat
        self.breastfeedingCat = breastfeedingCat
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
        self.constants = None
        self.params = None
        import helper as helperCode
        self.helper = helperCode.Helper()
        
    def setConstants(self, inputConstants):
        self.constants = inputConstants
        

    def setParams(self, inputParams):
        self.params = inputParams

    
    def applyMortality(self):
        for ageGroup in self.listOfAgeCompartments:
            for stuntingCat in ["normal", "mild", "moderate", "high"]:
                for wastingCat in ["normal", "mild", "moderate", "high"]:
                    for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
                        deaths = ageGroup.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize * ageGroup.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].mortalityRate * self.timestep
                        ageGroup.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize -= deaths
                        ageGroup.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].cumulativeDeaths += deaths



    def applyAging(self):
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
            restratIfPreviously    = self.helper.restratify(self.constants.probStuntedIfPrevStunted["yesstunted"][ageName])
            restratIfNotPreviously = self.helper.restratify(self.constants.probStuntedIfPrevStunted["notstunted"][ageName])
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
                        thisBox.populationSize += numAgingInNotStunted * restratIfNotPreviously[stuntingCat] * self.params.breastfeedingDistribution[ageName][breastfeedingCat]
                        thisBox.populationSize += numAgingInStunted    * restratIfPreviously[stuntingCat]    * self.params.breastfeedingDistribution[ageName][breastfeedingCat]




    def applyBirths(self):
        # calculate total number of new babies
        birthRate = self.fertileWomen.birthRate  #WARNING: assuming per pre-determined timestep
        numWomen  = self.fertileWomen.populationSize
        numNewBabies = numWomen * birthRate * self.timestep
        # see constants.py for calculation of baseline probability of birth outcome
        # now calculate stunting probability accordingly
        # restratify Stunting
        restratifiedStuntingAtBirth = {}
        for birthOutcome in ["Pre-term SGA","Pre-term AGA","Term SGA","Term AGA"]:
            restratifiedStuntingAtBirth[birthOutcome] = self.helper.restratify(self.constants.probsStuntingAtBirth[birthOutcome])
        # sum over birth outcome for full stratified stunting fractions, then apply to birth distribution
        stuntingFractions = {}
        for stuntingCat in ["normal", "mild", "moderate", "high"]:
            stuntingFractions[stuntingCat] = 0.
            for birthOutcome in ["Pre-term SGA","Pre-term AGA","Term SGA","Term AGA"]:
                stuntingFractions[stuntingCat] += restratifiedStuntingAtBirth[birthOutcome][stuntingCat] * self.params.birthOutcomeDist[birthOutcome]
            for wastingCat in ["normal", "mild", "moderate", "high"]:
                for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
                    self.listOfAgeCompartments[0].dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize += numNewBabies * self.params.wastingDistribution["<1 month"][wastingCat] * self.params.breastfeedingDistribution["<1 month"][breastfeedingCat] * stuntingFractions[stuntingCat]



        
    def updateMortalityRate(self):
        for ageGroup in self.listOfAgeCompartments:
            age = ageGroup.name
            for stuntingCat in ["normal", "mild", "moderate", "high"]:
                for wastingCat in ["normal", "mild", "moderate", "high"]:
                    for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
                        count = 0                        
                        for cause in self.params.causesOfDeath:
                            t1 = self.constants.underlyingMortalityByAge[age]    
                            t2 = self.params.causeOfDeathDist[age][cause]
                            t3 = self.params.RRStunting[age][cause][stuntingCat]
                            t4 = self.params.RRWasting[age][cause][wastingCat]
                            t5 = self.params.RRBreastfeeding[age][cause][breastfeedingCat]
                            count += t1 * t2 * t3 * t4 * t5                            
                        ageGroup.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].mortalityRate = count

    


    def moveOneTimeStep(self):
        self.updateMortalityRate()
        self.applyMortality()
        self.applyAging()
        self.applyBirths()
        
        
