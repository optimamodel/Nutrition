# -*- coding: utf-8 -*-
"""
Created on Fri Feb 19 11:33:36 2016

@author: ruthpearson
"""

class Compartment:
    def __init__(self, name, InitialConditions(), Data(), Parameters()):
        self.name = name  
        self.InitialConditions = InitialConditions()
        self.Data = Data()
        self.Parameters = Parameters()  
       
    def UpdateCompartment(self):
        InitialConditions.applyMortality(Parameters.mortalityStunted, Parameters.mortalityNotStunted)
        InitialConditions.applyNewStunting(Parameters.stuntingRate)
        InitialConditions.applyRecovery(Parameters.recoveryRate)
        
        
class InitialConditions:
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
    def __init__(self,totalPopulationSize, percentStunted, mortalityPerMonth):
        self.totalPopulationSize = totalPopulationSize
        self.percentStunted = percentStunted
        self.mortalityPerMonth = mortalityPerMonth
        
class Parameters:
    def __init__(self, stuntingRate, recoveryRate, mortalityStunted, mortalityNotStunted, agingRate):
        self.stuntingRate = stuntingRate
        self.recoveryRate = recoveryRate
        self.mortalityStunted = mortalityStunted
        self.mortalityNotStunted = mortalityNotStunted
        self.agingRate = agingRate
   
   
