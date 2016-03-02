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
        
    # Before beginning model, determine constants. Either put this into __init__ or call directly after creating Model
    def calcConstants(self,data):
        import sqrt from numpy
        numAgeGroups = len(self.listOfAgeCompartments)
        # probability of stunting progression
        self.probStuntedIfNotPreviouslyStunted = {}
        self.probStuntedPreviouslyStunted = {}
        for ageInd in range(1,numAgeGroups):
            ageName = data.ages[ageInd]
            OddsRatio = data.ORstuntingProgression[ageName]
            numStuntedNow =  self.listOfAgeCompartments.[ageInd].dictOfBoxes["high"]["normal"]["exclusive"].populationsSize
            numNotStuntedNow = 0.
            for stuntingStatus in ["normal", "mild", "moderate"]:
                numNotStuntedNow += self.listOfAgeCompartments.dictOfBoxes[stuntingStatus]["normal"]["exclusive"].populationsSize
            numTotalNow = numStuntedNow + numNotStuntedNow
            FracStuntedNow = numStuntedNow / numTotalNow # aka Fn
            # solve quadratic equation
            a = FracNotStuntedNow*(1-OddsRatio)
            b = -numTotalNow
            c = FracStuntedNow
            det = sqrt(b**2 - 4.*a*c)
            soln1 = (-b + det)/(2.*a)
            soln2 = (-b - det)/(2.*a)
            # not sure what to do if both or neither are solutions
            if(soln1>0.)and(soln1<1.): p0 = soln1
            if(soln2>0.)and(soln2<1.): p0 = soln2
            self.probStuntedIfNotPreviouslyStunted[ageName] = p0
            self.probStuntedPreviouslyStunted[ageName]      = p0*OddsRatio/(1.-p0+OddsRatio*p0)
        # probability of stunting given IUGR status...


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
                for breastfeedingStatus in ["exclusive", "predominant", "partial", "none"]:
                    aging = [0.]*numCompartments
                    for ind in range(1, numCompartments):
                        youngerCompartment = self.listOfAgeCompartments[ind-1]
                        youngerBox = youngerCompartment.dictOfBoxes[stuntingStatus][wastingStatus][breastfeedingStatus] 
                        numAging = int(youngerBox.populationSize * youngerCompartment.agingRate)
                        aging[ind]   += numAging
                        aging[ind-1] -= numAging
                    
                    #remember to age people out of the last age compartment
                    ageOut = self.listOfAgeCompartments[numCompartments-1].dictOfBoxes[stuntingStatus][wastingStatus][breastfeedingStatus].populationSize * self.listOfAgeCompartments[numCompartments-1].agingRate    
                    aging[numCompartments-1] -= ageOut 
                    for ageCompartment in range(0, numCompartments):
                        self.listOfAgeCompartments[ageCompartment].dictOfBoxes[stuntingStatus][wastingStatus][breastfeedingStatus].populationSize += aging[ageCompartment]
                   
                
        

    def applyBirths(self,data):
        # calculate total number of new babies
        birthRate = self.fertileWomen.birthRate  #WARNING: assuming per pre-determined timestep
        numWomen  = self.fertileWomen.populationSize
        numNewBabies = numWomen * birthRate
        # P(mothersAge,birthOrder,timeBtwn)
        probBirthAndTime = {}
        for mothersAge in ["<18 years","18-34 years","35-49 years"]:
            probBirthAndTime[mothersAge]={}
            for birthOrder in ["first","second or third","greater than third"]:
                probBirthAndTime[mothersAge][birthOrder]={}
                probCircumstance = data.birthCircumstanceDist[mothersAge][birthOrder]
                if birthOrder == "first":
                    probBirthAndTime[mothersAge][birthOrder]["first"] = probCircumstance
                else:
                    probTimeBtwnBirths = data.timeBetweenBirthsDist
                    probFirst = probTimeBtwnBirths["first"]
                    for timeBtwnBirths in ["<18 months","18-23 months","<24 months"]:
                        probTimeIfNotFirst = probTimeBtwnBirths[timeBtwnBirths]/(1-probFirst)
                        probBirthAndTime[mothersAge][birthOrder][timeBtwnBirths] = probCircumstance * probTimeIfNotFirst
        # calculate baseline P(birthOutcome | standard (mothersAge,birthOrder,timeBtwn))
        baselineStatusAtBirth = {}
        sumProbOutcome = 0.
        # continue for each birth outcome (first 3 anyway, for which relative risks are provided)
        for birthOutcome in ["pretermSGA","pretermAGA","termSGA"]: #,"termAGA"]:
            summation = 0.
            for mothersAge in ["<18 years","18-34 years","35-49 years"]:
                for birthOrder in ["first","second or third","greater than third"]:
                    for timeBtwnBirths in ["first","<18 months","18-23 months","<24 months"]:
                        P_bt = probBirthAndTime[mothersAge][birthOrder][timeBtwnBirths]
                        RR_gb = data.RRbirthOutcomeByAgeAndOrder[birthOutcome][mothersAge][birthOrder]
                        RR_gt = data.RRbirthOutcomeByTime[birthOutcome][timeBtwnBirths]
                        summation += P_bt * RR_gb * RR_gt
            baselineStatusAtBirth[birthOutcome] = data.probBirthOutcome[birthOutcome] / summation
            sumProbOutcome += baselineStatusAtBirth[birthOutcome]
        baselineStatusAtBirth["termAGA"] = 1. - sumProbOutcome
        # now calculate stunting probability accordingly
        for stuntingStatus in ["normal", "mild", "moderate", "high"]:
            for wastingStatus in ["normal", "mild", "moderate", "high"]:
                for breastfeedingStatus in ["exclusive", "predominant", "partial", "none"]:
                    #self.listOfAgeCompartments[0].dictOfBoxes[stuntingStatus][wastingStatus][breastfeedingStatus].populationSize += numNewBabies * data.wastingDistribution[wastingStatus]["0-1 month"] * data.breastfeedingDistribution[breastfeedingStatus]["0-1 month"] * stuntingFraction
        #return x


        
    def updateMortalityRate(self, data, underlyingMortality):
        for ageGroup in self.listOfAgeCompartments:
            age = ageGroup.name
            for stuntingStatus in ["normal", "mild", "moderate", "high"]:
                for wastingStatus in ["normal", "mild", "moderate", "high"]:
                    for breastfeedingStatus in ["exclusive", "predominant", "partial", "none"]:
                        count = 0                        
                        for cause in data.causesOfDeath:
                            t1 = underlyingMortality[age]    
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
        
        
