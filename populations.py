# -*- coding: utf-8 -*-
"""
Created on Thu Jun  1 16:35:38 2017

@author: ruth
"""
from copy import deepcopy as dcp

class Box:
    def __init__(self, populationSize):
        self.populationSize = populationSize
        self.mortalityRate = None
        self.cumulativeDeaths = 0

class PregnantWomenAgeCompartment:
    def __init__(self, name, birthRate, dictOfBoxes, agingRate, keyList):
        self.name = name
        self.agingRate = agingRate
        self.birthRate = birthRate
        self.dictOfBoxes = dcp(dictOfBoxes)
        for key in keyList.keys():
            setattr(self, key, keyList[key])
        
    def getTotalPopulation(self):
        totalSum = 0
        for anemiaStatus in self.anemiaList:
            for deliveryStatus in self.deliveryList:
                totalSum += self.dictOfBoxes[anemiaStatus][deliveryStatus].populationSize
        return totalSum

    def getAnemicFraction(self):
        totalAnemic = 0.
        totalPop = self.getTotalPopulation()
        for deliveryStatus in self.deliveryList:
            totalAnemic += self.dictOfBoxes['anemic'][deliveryStatus].populationSize
        return float(totalAnemic)/float(totalPop)
        
    def getNumberAnemic(self):
        totalAnemic = 0.
        for deliveryStatus in self.deliveryList:
            totalAnemic += self.dictOfBoxes['anemic'][deliveryStatus].populationSize
        return totalAnemic    

    def distributePopulation(self, anemiaDist, deliveryDist):
        totalPop = self.getTotalPopulation()
        for anemiaStatus in self.anemiaList:
            for deliveryStatus in self.deliveryList:
                self.dictOfBoxes[anemiaStatus][deliveryStatus].populationSize = anemiaDist['pregnant women'][anemiaStatus] * deliveryDist[deliveryStatus] * totalPop

    def getAnemiaDistribution(self):
        totalPop = self.getTotalPopulation()
        returnDict = {}
        for anemiaStatus in self.anemiaList:
            returnDict[anemiaStatus] = 0.
            for deliveryStatus in self.deliveryList:
                returnDict[anemiaStatus] += self.dictOfBoxes[anemiaStatus][deliveryStatus].populationSize / totalPop
        return returnDict
        

class AgeCompartment:
    def __init__(self, name, dictOfBoxes, agingRate, keyList):
        self.name = name  
        self.dictOfBoxes = dcp(dictOfBoxes)
        self.agingRate = agingRate
        for key in keyList.keys():
            setattr(self, key, keyList[key])

    def getTotalPopulation(self):
        totalSum = 0.
        for stuntingCat in self.stuntingList:
            for wastingCat in self.wastingList:
                for breastfeedingCat in self.breastfeedingList:
                    for anemiaStatus in self.anemiaList:
                        thisBox = self.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus]
                        totalSum += thisBox.populationSize
        return totalSum

    def getStuntedFraction(self):
        NumberStunted = 0.
        for stuntingCat in ["moderate", "high"]:
            for wastingCat in self.wastingList:
                for breastfeedingCat in self.breastfeedingList:
                    for anemiaStatus in self.anemiaList:
                        NumberStunted += self.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus].populationSize
        NumberTotal = self.getTotalPopulation()
        return float(NumberStunted)/float(NumberTotal)

    def getAnemicFraction(self):
        numberAnemic = 0.
        numberTotal = self.getTotalPopulation()
        for stuntingCat in self.stuntingList:
            for wastingCat in self.wastingList:
                for breastfeedingCat in self.breastfeedingList:
                    numberAnemic += self.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat]["anemic"].populationSize
        return float(numberAnemic)/float(numberTotal)
        
    def getNumberAnemic(self):
        numberAnemic = 0.
        for stuntingCat in self.stuntingList:
            for wastingCat in self.wastingList:
                for breastfeedingCat in self.breastfeedingList:
                    numberAnemic += self.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat]["anemic"].populationSize
        return numberAnemic    

    def getNumberStunted(self):
        NumberStunted = 0.
        for stuntingCat in ["moderate", "high"]:
            for wastingCat in self.wastingList:
                for breastfeedingCat in self.breastfeedingList:
                    for anemiaStatus in self.anemiaList:
                        NumberStunted += self.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus].populationSize
        return NumberStunted
        
    def getNumberNotStunted(self):
        NumberNotStunted = 0.
        for stuntingCat in ["normal", "mild"]:
            for wastingCat in self.wastingList:
                for breastfeedingCat in self.breastfeedingList:
                    for anemiaStatus in self.anemiaList:
                        NumberNotStunted += self.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus].populationSize
        return NumberNotStunted    

    def getCumulativeDeaths(self):
        totalSum = 0.
        for stuntingCat in self.stuntingList:
            for wastingCat in self.wastingList:
                for breastfeedingCat in self.breastfeedingList:
                    for anemiaStatus in self.anemiaList:
                        totalSum += self.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus].cumulativeDeaths
        return totalSum

    def getStuntingDistribution(self):
        totalPop = self.getTotalPopulation()
        returnDict = {}
        for stuntingCat in self.stuntingList:
            returnDict[stuntingCat] = 0.
            for wastingCat in self.wastingList:
                for breastfeedingCat in self.breastfeedingList:
                    for anemiaStatus in self.anemiaList:
                        returnDict[stuntingCat] += self.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus].populationSize / totalPop
        return returnDict

    def getWastingDistribution(self):
        totalPop = self.getTotalPopulation()
        returnDict = {}
        for wastingCat in self.wastingList:
            returnDict[wastingCat] = 0.
            for stuntingCat in self.stuntingList:
                for breastfeedingCat in self.breastfeedingList:
                    for anemiaStatus in self.anemiaList:
                        returnDict[wastingCat] += self.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus].populationSize / totalPop
        return returnDict

    def getBreastfeedingDistribution(self):
        totalPop = self.getTotalPopulation()
        returnDict = {}
        for breastfeedingCat in self.breastfeedingList:
            returnDict[breastfeedingCat] = 0.
            for wastingCat in self.wastingList:
                for stuntingCat in self.stuntingList:
                    for anemiaStatus in self.anemiaList:
                        returnDict[breastfeedingCat] += self.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus].populationSize / totalPop
        return returnDict

    def getAnemiaDistribution(self):
        totalPop = self.getTotalPopulation()
        returnDict = {}
        for anemiaStatus in self.anemiaList:
            returnDict[anemiaStatus] = 0.
            for breastfeedingCat in self.breastfeedingList:
                for wastingCat in self.wastingList:
                    for stuntingCat in self.stuntingList:
                        returnDict[anemiaStatus] += self.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus].populationSize / totalPop
        return returnDict


    def getNumberCorrectlyBreastfed(self,practice):
        NumberCorrectlyBreastfed = 0.
        for stuntingCat in self.stuntingList:
            for wastingCat in self.wastingList:
                for anemiaStatus in self.anemiaList:
                    NumberCorrectlyBreastfed += self.dictOfBoxes[stuntingCat][wastingCat][practice][anemiaStatus].populationSize
        return NumberCorrectlyBreastfed

    def distribute(self, stuntingDist, wastingDist, breastfeedingDist, anemiaDist):
        ageName = self.name
        totalPop = self.getTotalPopulation()
        for stuntingCat in self.stuntingList:
            for wastingCat in self.wastingList:
                for breastfeedingCat in self.breastfeedingList:
                    for anemiaStatus in self.anemiaList:
                        self.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus].populationSize = stuntingDist[ageName][stuntingCat] * wastingDist[ageName][wastingCat] *\
                                                                                                                   breastfeedingDist[ageName][breastfeedingCat] * anemiaDist[ageName][anemiaStatus] * totalPop

    def getMortality(self):
        agePop = 0.
        ageMortality = 0.
        for stuntingCat in self.stuntingList:
            for wastingCat in self.wastingList:
                for breastfeedingCat in self.breastfeedingList:
                    for anemiaStatus in self.anemiaList:
                        thisBox = self.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus]
                        boxMortality = thisBox.mortalityRate
                        boxPop = thisBox.populationSize
                        agePop += boxPop
                        ageMortality += boxMortality*boxPop
        ageMortality /= agePop
        return ageMortality
        
class ReproductiveAgeCompartment:
    def __init__(self, name, dictOfBoxes, agingRate, keyList):
        self.name = name  
        self.dictOfBoxes = dcp(dictOfBoxes)
        self.agingRate = agingRate
        for key in keyList.keys():
            setattr(self, key, keyList[key])

    def getTotalPopulation(self):
        totalSum = 0.
        for anemiaStatus in self.anemiaList:
            totalSum += self.dictOfBoxes[anemiaStatus].populationSize
        return totalSum

    def distributeAnemicPopulation(self, anemiaDist):
        ageName = self.name
        totalPop = self.getTotalPopulation()
        for anemiaStatus in self.anemiaList:
            self.dictOfBoxes[anemiaStatus].populationSize = anemiaDist[ageName][anemiaStatus] * totalPop

    def getAnemicFraction(self):
        numberAnemic = self.dictOfBoxes["anemic"].populationSize
        numberTotal = self.getTotalPopulation()
        return float(numberAnemic)/numberTotal
        
    def getNumberAnemic(self):
        numberAnemic = self.dictOfBoxes["anemic"].populationSize
        return numberAnemic    

    def getAnemiaDistribution(self):
       totalPop = self.getTotalPopulation()
       returnDict = {}
       for status in self.anemiaList:
           returnDict[status] = self.dictOfBoxes[status].populationSize / totalPop
       return returnDict