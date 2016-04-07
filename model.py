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
    def __init__(self, name, fertileWomen, listOfAgeCompartments, listOfLabels, timestep):
        self.name = name
        self.fertileWomen = fertileWomen
        self.listOfAgeCompartments = listOfAgeCompartments
        self.ages,self.birthOutcomes = listOfLabels
        self.timestep = timestep
        self.constants = None
        self.params = None
        import helper as helperCode
        self.helper = helperCode.Helper()

        
    def setConstants(self, inputConstants):
        self.constants = inputConstants

       
    def setParams(self, inputParams):
        self.params = inputParams

    
        
    def updateMortalityRate(self):
        # Newborns first
        ageGroup = self.listOfAgeCompartments[0]
        age = ageGroup.name
        for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
            count = 0.
            for cause in self.params.causesOfDeath:
                Rb = self.params.RRBreastfeeding[age][cause][breastfeedingCat]
                for birthoutcome in self.birthOutcomes:
                    Rbo = self.params.RRdeathByBirthOutcome[cause][birthoutcome]
                    count += Rb * Rbo * self.constants.underlyingMortalities[age][cause]
            for stuntingCat in ["normal", "mild", "moderate", "high"]:
                for wastingCat in ["normal", "mild", "moderate", "high"]:
                    ageGroup.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].mortalityRate = count
        # over 1 months
        for ageGroup in self.listOfAgeCompartments[1:]:
            age = ageGroup.name
            for stuntingCat in ["normal", "mild", "moderate", "high"]:
                for wastingCat in ["normal", "mild", "moderate", "high"]:
                    for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
                        count = 0.
                        for cause in self.params.causesOfDeath:
                            t1 = self.constants.underlyingMortalities[age][cause]
                            #t2 = self.params.causeOfDeathDist[age][cause]
                            t3 = self.params.RRStunting[age][cause][stuntingCat]
                            t4 = self.params.RRWasting[age][cause][wastingCat]
                            t5 = self.params.RRBreastfeeding[age][cause][breastfeedingCat]
                            count += t1 * t3 * t4 * t5                            
                        ageGroup.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].mortalityRate = count

    

    def applyMortality(self):
        for ageGroup in self.listOfAgeCompartments:
            for stuntingCat in ["normal", "mild", "moderate", "high"]:
                for wastingCat in ["normal", "mild", "moderate", "high"]:
                    for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
                        thisBox = ageGroup.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat]
                        deaths = thisBox.populationSize * thisBox.mortalityRate * self.timestep
                        thisBox.populationSize -= deaths
                        thisBox.cumulativeDeaths += deaths
                    


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
            younger = self.ages[ind-1]
            thisAgeCompartment = self.listOfAgeCompartments[ind]
            Za = self.params.InciDiarrhoea[ageName]
            RRnot = self.params.RRdiarrhoea[ageName]["none"]
            for wastingCat in ["normal", "mild", "moderate", "high"]:
                prevWT = wastingCat
                numAgingIn = {}
                numAgingIn["notstunted"] = 0.
                numAgingIn["yesstunted"] = 0.
                for prevBF in ["exclusive", "predominant", "partial", "none"]:
                    numAgingIn["notstunted"] += agingOut[ind-1][prevWT][prevBF]["normal"] + agingOut[ind-1][prevWT][prevBF]["mild"]
                    numAgingIn["yesstunted"] += agingOut[ind-1][prevWT][prevBF]["moderate"] + agingOut[ind-1][prevWT][prevBF]["high"]
                    RDa = self.params.RRdiarrhoea[younger][prevBF]
                    beta = {}
                    beta["dia"]   = 1. - (RRnot*Za-RDa*Za)/(RRnot*Za)
                    beta["nodia"] = (RRnot*Za-RDa*Za)/(RRnot*Za)
                for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
                    for stuntingCat in ["normal","mild","moderate","high"]:
                        thisBox = thisAgeCompartment.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat]
                        thisBox.populationSize -= agingOut[ind][wastingCat][breastfeedingCat][stuntingCat]
                        for prevStunt in ["yesstunted","notstunted"]:
                            for prevDiarr in ["dia","nodia"]:
                                gamma = self.constants.probStunted[ageName][prevStunt][prevDiarr]
                                fracStunted = self.helper.restratify(gamma)
                                thisBox.populationSize += fracStunted[stuntingCat] * beta[prevDiarr] * numAgingIn[prevStunt] * self.params.breastfeedingDistribution[ageName][breastfeedingCat]



    def applyBirths(self):
        # calculate total number of new babies
        birthRate = self.fertileWomen.birthRate  #WARNING: assuming per pre-determined timestep
        numWomen  = self.fertileWomen.populationSize
        numNewBabies = 170000 #numWomen * birthRate * self.timestep
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





    def moveOneTimeStep(self):
        self.updateMortalityRate()
        self.applyMortality()
        self.applyAging()
        self.applyBirths()
        
        
