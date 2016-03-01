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
        # continue for each birth outcome
        for birthOutcome in ["pretermSGA","pretermAGA","termSGA","termAGA"]:
            summation = 0.
            for mothersAge in ["<18 years","18-34 years","35-49 years"]:
                for birthOrder in ["first","second or third","greater than third"]:
                    for timeBtwnBirths in ["first","<18 months","18-23 months","<24 months"]:
                        P_bt = probBirthAndTime[mothersAge][birthOrder][timeBtwnBirths]
                        RR_gb = data.RRbirthOutcomeByAgeAndOrder[birthOutcome][mothersAge][birthOrder]
                        RR_gt = data.RRbirthOutcomeByTime[birthOutcome][timeBtwnBirths]
                        summation += P_bt * RR_gb * RR_gt
            baselineStatusAtBirth[birthOutcome] = data.probBirthOutcome[birthOutcome] / summation
        # now decide stunting odds accordingly BUT DOES BIRTH AGE, ORDER, AND TIME EVEN MATTER?
        for stuntingStatus in ["normal", "mild", "moderate", "high"]:
            for wastingStatus in ["normal", "mild", "moderate", "high"]:
                for breastFeedingStatus in ["exclusive", "predominant", "partial", "none"]:
                    #self.listOfAgeCompartments[0].dictOfBoxes[stuntingStatus][wastingStatus][breastFeedingStatus].populationSize += numNewBabies * statusSpecificFraction
        #return x


        
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
        
        
        
        
        
                
