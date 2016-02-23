# -*- coding: utf-8 -*-
"""
Created on Fri Feb 19 11:33:36 2016

@author: ruthpearson
"""

class Compartment:
    def __init__(self, name, conditions, data, parameters, causeOfDeathList):
        self.name = name  
        self.conditions = conditions
        self.data = data
        self.parameters = parameters 
        self.causeOfDeathList = causeOfDeathList
        self.setOverallMortalityParameterFromDeathList()
        
    def setOverallMortalityParameterFromDeathList(self):
        combinedRate = 0
        for cause in self.causeOfDeathList:
            combinedRate += cause.mortalityRate #THIS IS NOT THE RIGHT WAY TO COMBINE MORTALITIES - PLACE HOLDER
        self.parameters.mortalityStunted = self.parameters.stuntingMortalityFactor * combinedRate
        self.parameters.mortalityNonStunted = combinedRate
       
    def updateCompartment(self):
        self.conditions.applyMortality(self.parameters.mortalityStunted, self.parameters.mortalityNotStunted)
        self.conditions.applyNewStunting(self.parameters.stuntingRate)
        self.conditions.applyRecovery(self.parameters.recoveryRate)
        
        
class Conditions:
    def __init__(self,stuntedPopulationSize, nonStuntedPopulationSize):
        self.stuntedPopulationSize = stuntedPopulationSize
        self.nonStuntedPopulationSize = nonStuntedPopulationSize 
        
    def applyMortality(self, mortalityStunted, mortalityNonStunted):
        self.stuntedPopulationSize -= self.stuntedPopulationSize * mortalityStunted
        self.nonStuntedPopulationSize -= self.nonStuntedPopulationSize * mortalityNonStunted
        
    def applyNewStunting(self, stuntingRate):
        newCases = self.nonStuntedPopulationSize * stuntingRate        
        self.stuntedPopulationSize += newCases
        self.nonStuntedPopulationSize -= newCases
        
    def applyRecovery(self, recoveryRate):
        recoveryCases = self.stuntedPopulationSize * recoveryRate
        self.stuntedPopulationSize -= recoveryCases
        self.nonStuntedPopulationSize += recoveryCases
         
         
class Data:
    def __init__(self,totalPopulationSize, percentStunted, mortalityPerMonth, listNumberDeathsByCause):
        self.totalPopulationSize = totalPopulationSize
        self.percentStunted = percentStunted
        self.listNumberDeathsByCause = listNumberDeathsByCause #ordering matches casue of death list for this age group
        
        
        
class Parameters:
    def __init__(self, stuntingRate, recoveryRate, agingRate, stuntingMortalityFactor):
        self.stuntingRate = stuntingRate
        self.recoveryRate = recoveryRate
        self.mortalityStunted = 0
        self.mortalityNotStunted = 0
        self.agingRate = agingRate
        self.stuntingMortalityFactor = stuntingMortalityFactor
        
   
   
class FertileWomen:
    def __init__(self, birthRateStunted, birthRateNonStunted, stuntedPopulationSize, nonStuntedPopulationSize, probabilityOfStuntedBabyIfStunted, probabilityOfStuntedBabyIfNonStunted):    
        self.birthRateStunted = birthRateStunted
        self.birthRateNonStunted = birthRateNonStunted
        self.probabilityOfStuntedBabyIfStunted = probabilityOfStuntedBabyIfStunted
        self.probabilityOfStuntedBabyIfNonStunted = probabilityOfStuntedBabyIfNonStunted
        self.stuntedPopulationSize = stuntedPopulationSize
        self.nonStuntedPopulationSize = nonStuntedPopulationSize
 
 
class Model:
    def __init__(self, fertileWomen, compartmentList):
        self.fertileWomen = fertileWomen
        self.compartmentList = compartmentList
        
    def moveOneTimeStep(self):
        #call update on compartment list (independent of other compartments)
        for group in self.compartmentList:
            group.updateCompartment()
        
        #updates that involve interactions with other compartments
        #1. births
        newborns = self.compartmentList[0]
        mums = self.fertileWomen
        newStunted    = mums.stuntedPopulationSize    * mums.birthRateStunted    * mums.probabilityOfStuntedBabyIfStunted \
            +           mums.nonStuntedPopulationSize * mums.birthRateNonStunted * mums.probabilityOfStuntedBabyIfNonStunted
        newNonStunted = mums.stuntedPopulationSize    * mums.birthRateStunted    * (1. - mums.probabilityOfStuntedBabyIfStunted) \
            +           mums.nonStuntedPopulationSize * mums.birthRateNonStunted * (1. - mums.probabilityOfStuntedBabyIfNonStunted)
        newborns.conditions.stuntedPopulationSize    += newStunted
        newborns.conditions.nonStuntedPopulationSize += newNonStunted
        #2. perform aging
        numCompartments = len(self.compartmentList)
        aging = [] * numCompartments
        for ind in range(1,numCompartments):
            younger = self.compartmentList[ind-1]
            numStuntedAging    = younger.conditions.stuntedPopulationSize    * younger.parameters.agingRate
            numNonStuntedAging = younger.conditions.nonStuntedPopulationSize * younger.parameters.agingRate
            aging[ind]['stunted']      += numStuntedAging
            aging[ind-1]['stunted']    -= numStuntedAging
            aging[ind]['nonStunted']   += numNonStuntedAging
            aging[ind-1]['nonStunted'] -= numNonStuntedAging
        for ind in range(numCompartments):
            self.compartmentList[ind].conditions.stuntedPopulationSize    += aging[ind]['stunted']
            self.compartmentList[ind].conditions.nonStuntedPopulationSize += aging[ind]['nonStunted']
            
#        #new births first
#        saveThisPopulationSizeStunted = self.compartmentList[0].conditions.stuntedPopulationSize
#        saveThisPopulationSizeNonStunted = self.compartmentList[0].conditions.nonStuntedPopulationSize        
#        
#        self.compartmentList[0].conditions.stuntedPopulationSize += self.fertileWomen.birthRateStunted * self.fertileWomen.stuntedPopulationSize    
#        self.compartmentList[0].conditions.nonStuntedPopulationSize += self.fertileWomen.bithRateNonStunted * self.fertileWomen.nonStuntedPopulationSize        
#        
#        #all the other compartments
#        for group in range(1, len(self.compartmentList)):
#            #USE SAVED VALUES   
#            #make this better   
#            addThis = self.compartmentList[group-1].conditions.stuntedPopulationSize * self.compartmentList[group-1].parameters.agingRate
#            minusThis =  self.compartmentList[group].conditions.stuntedPopulationSize * self.compartmentList[group].parameters.agingRate           
#            #need to do this for stunted and non-stunted
#            self.compartmentList[group] += addThis - minusThis
#            
    
    
class CauseOfDeath:
    def __init__(self,name, mortalityRate):
        self.name = name
        self.mortalityRate = mortalityRate 
        
        
    
    
    
    
