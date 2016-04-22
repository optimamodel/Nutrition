# -*- coding: utf-8 -*-
"""
Created on Wed Feb 24 13:43:14 2016

@author: ruthpearson
"""
from __future__ import division

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
    def __init__(self, name, dictOfBoxes, agingRate, keyList):
        self.name = name  
        self.dictOfBoxes = dictOfBoxes
        self.agingRate = agingRate
        self.ages,self.birthOutcomes,self.wastingList,self.stuntingList,self.breastfeedingList = keyList

    def getTotalPopulation(self):
        sum = 0.
        for stuntingCat in self.stuntingList:
            for wastingCat in self.wastingList:
                for breastfeedingCat in self.breastfeedingList:
                    thisBox = self.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat] 
                    sum += thisBox.populationSize
        return sum

    def getStuntedFraction(self):
        NumberStunted = 0.
        for stuntingCat in ["moderate", "high"]:
            for wastingCat in self.wastingList:
                for breastfeedingCat in self.breastfeedingList:
                    NumberStunted += self.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize
        NumberTotal = self.getTotalPopulation()
        return NumberStunted/NumberTotal

    def distribute(self, stuntingDist, wastingDist, breastfeedingDist, totalPop):
        ageName = self.name
        for stuntingCat in self.stuntingList:
            for wastingCat in self.wastingList:
                for breastfeedingCat in self.breastfeedingList:
                    self.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize = stuntingDist[ageName][stuntingCat] * wastingDist[ageName][wastingCat] * breastfeedingDist[ageName][breastfeedingCat] * totalPop


        
class Model:
    def __init__(self, name, fertileWomen, listOfAgeCompartments, keyList, timestep):
        self.name = name
        self.fertileWomen = fertileWomen
        self.listOfAgeCompartments = listOfAgeCompartments
        self.ages,self.birthOutcomes,self.wastingList,self.stuntingList,self.breastfeedingList = keyList
        self.timestep = timestep
        self.constants = None
        self.params = None
        import helper as helperCode
        self.helper = helperCode.Helper()

        
    def setConstants(self, inputConstants):
        self.constants = inputConstants

       
    def setParams(self, inputParams):
        self.params = inputParams


    def updateCoverages(self,newCoverage):
        # setup
        MortalityUpdate={}
        for cause in self.params.causesOfDeath:
            MortalityUpdate[cause] = 1.
        StuntingUpdate=1.
        # Zinc
        redStunting, redDiarrhea = self.params.increaseCoverageOfZinc(newCoverage["Zinc supplementation"])
        print "Reduction in Stunting due to Zinc = %g"%(redStunting)
        print "Reduction in Diarrhea mortality = "
        print redDiarrhea
        StuntingUpdate *= 1.-redStunting
        #for cause in self.params.causesOfDeath:
        MortalityUpdate["Diarrhea"] *= 1.-redDiarrhea
        # Repeat for all interventions
        #
        #
        # update stunting
        for ageGroup in self.listOfAgeCompartments:
            ageName = ageGroup.name
            oldProbStunting = self.params.stuntingDistribution[ageName]["high"] + self.params.stuntingDistribution[ageName]["moderate"]
            newProbStunting = oldProbStunting * StuntingUpdate
            print self.params.stuntingDistribution[ageName]
            self.params.stuntingDistribution[ageName] = self.helper.restratify(newProbStunting)
            print self.params.stuntingDistribution[ageName]
            totalPop = ageGroup.getTotalPopulation()
            ageGroup.distribute(self.params.stuntingDistribution,self.params.wastingDistribution,self.params.breastfeedingDistribution,totalPop)
        # update mortalities
        for ageGroup in self.listOfAgeCompartments:
            ageName = ageGroup.name
            self.constants.underlyingMortalities[ageName]["Diarrhea"] *= MortalityUpdate["Diarrhea"]


        
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
        eps = 1.e-5
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
                    for stuntingCat in self.stuntingList:
                        thisBox = thisCompartment.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat] 
                        agingOut[ind][wastingCat][breastfeedingCat][stuntingCat] = thisBox.populationSize * thisCompartment.agingRate #*self.timestep
        # first age group does not have aging in
        newborns = self.listOfAgeCompartments[0]
        for wastingCat in ["normal", "mild", "moderate", "high"]:
            for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
                for stuntingCat in self.stuntingList:
                    newbornBox = newborns.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat]
                    newbornBox.populationSize -= agingOut[0][wastingCat][breastfeedingCat][stuntingCat]
        # for older age groups, you need to decide if people stayed stunted from previous age group
        for ind in range(1, numCompartments):
            ageName = self.ages[ind]
            younger = self.ages[ind-1]
            thisAgeCompartment = self.listOfAgeCompartments[ind]
            # calculate how many of those aging in from younger age group are stunted (binary)
            numAgingIn = {}
            numAgingIn["notstunted"] = 0.
            numAgingIn["yesstunted"] = 0.
            for prevBF in ["exclusive", "predominant", "partial", "none"]:
                for prevWT in ["normal", "mild", "moderate", "high"]:
                    numAgingIn["notstunted"] += agingOut[ind-1][prevWT][prevBF]["normal"] + agingOut[ind-1][prevWT][prevBF]["mild"]
                    numAgingIn["yesstunted"] += agingOut[ind-1][prevWT][prevBF]["moderate"] + agingOut[ind-1][prevWT][prevBF]["high"]
            # calculate which of those aging in are moving into a stunted category (4 categories)
            numAgingInStratified = {}
            for stuntingCat in self.stuntingList:
                numAgingInStratified[stuntingCat] = 0.
            for prevStunt in ["yesstunted","notstunted"]:
                restratifiedProbBecomeStunted = self.helper.restratify(self.constants.probStuntedIfPrevStunted[prevStunt][ageName])
                for stuntingCat in self.stuntingList:
                    numAgingInStratified[stuntingCat] += restratifiedProbBecomeStunted[stuntingCat] * numAgingIn[prevStunt]
            # distribution those aging in amongst those stunting categories but also breastfeeding and wasting
            for wastingCat in ["normal", "mild", "moderate", "high"]:
                paw = self.params.wastingDistribution[ageName][wastingCat]
                for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
                    pab = self.params.breastfeedingDistribution[ageName][breastfeedingCat]
                    for stuntingCat in ["normal","mild","moderate","high"]:
                        thisBox = thisAgeCompartment.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat]
                        thisBox.populationSize -= agingOut[ind][wastingCat][breastfeedingCat][stuntingCat]
                        thisBox.populationSize += numAgingInStratified[stuntingCat] * pab * paw
            #print "Stunted fraction in %s is %g"%(ageName,thisAgeCompartment.getStuntedFraction())



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

