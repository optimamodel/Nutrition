# -*- coding: utf-8 -*-
"""
Created on Fri April 1 2016

@author: madhura
"""
from __future__ import division
from copy import deepcopy as dcp

class Params:
    def __init__(self, data, constants, keyList):
        self.constants = constants
        self.ages, self.birthOutcomes, self.wastingList, self.stuntingList, self.breastfeedingList = keyList
        import helper as helperCode
        self.helper = helperCode.Helper()

        self.causesOfDeath = dcp(data.causesOfDeath)
        self.causeOfDeathDist = dcp(data.causeOfDeathDist)
        self.stuntingDistribution = dcp(data.stuntingDistribution)
        self.wastingDistribution = dcp(data.wastingDistribution)
        self.breastfeedingDistribution = dcp(data.breastfeedingDistribution)
        self.RRStunting = dcp(data.RRStunting)
        self.RRWasting = dcp(data.RRWasting)
        self.RRBreastfeeding = dcp(data.RRBreastfeeding)
        self.RRdeathByBirthOutcome = dcp(data.RRdeathByBirthOutcome)
        self.ORstuntingProgression = dcp(data.ORstuntingProgression)
        self.incidenceDiarrhea = dcp(data.incidenceDiarrhea)
        self.RRdiarrhea = dcp(data.RRdiarrhea)
        self.ORdiarrhea = dcp(data.ORdiarrhea)
        self.birthCircumstanceDist = dcp(data.birthCircumstanceDist)
        self.timeBetweenBirthsDist = dcp(data.timeBetweenBirthsDist)
        self.RRbirthOutcomeByAgeAndOrder = dcp(data.RRbirthOutcomeByAgeAndOrder)
        self.RRbirthOutcomeByTime = dcp(data.RRbirthOutcomeByTime)
        self.ORBirthOutcomeStunting = dcp(data.ORBirthOutcomeStunting)
        self.birthOutcomeDist = dcp(data.birthOutcomeDist)
        self.ORstuntingZinc = dcp(data.ORstuntingZinc)
        self.interventionCoverages = dcp(data.interventionCoveragesCurrent)
        self.interventionMortalityEffectiveness = dcp(data.interventionMortalityEffectiveness)
        self.interventionAffectedFraction = dcp(data.interventionAffectedFraction)
    

# Add all functions for updating parameters due to interventions here....

    def increaseCoverageOfZinc(self, newCoverage):
        oldCoverage = self.interventionCoverages["Zinc supplementation"]
        # -------------------------
        # calculate reduction in stunted fraction
        stuntingUpdate = {}
        for ageName in self.ages:
            probStuntingIfZinc = self.constants.fracStuntedIfZinc["zinc"][ageName]
            probStuntingIfNoZinc = self.constants.fracStuntedIfZinc["nozinc"][ageName]
            oldProbStunting = self.stuntingDistribution[ageName]["high"] + self.stuntingDistribution[ageName]["moderate"]
            newProbStunting = newCoverage*probStuntingIfZinc + (1.-newCoverage)*probStuntingIfNoZinc
            stuntingUpdate[ageName] = (oldProbStunting - newProbStunting)/oldProbStunting
        # -------------------------
        # Mortality
        mortalityReduction={}
        for ageName in self.ages:
            mortalityReduction[ageName]={}
            for cause in self.causesOfDeath:
                mortalityReduction[ageName][cause]=0.
        # Diarrhea
        for ageName in ["12-23 months", "24-59 months"]:
            affectedFrac = 0.253 # take from data
            effectiveness = 0.5 # take from data
            mortalityReduction[ageName]["Diarrhea"] = affectedFrac * effectiveness * (newCoverage - oldCoverage) / (1. - effectiveness*oldCoverage)
        # Pneumonia
        for ageName in ["12-23 months", "24-59 months"]:
            affectedFrac = 0.253 # take from data
            effectiveness = 0.5 # take from data
            mortalityReduction[ageName]["Pneumonia"] = affectedFrac * effectiveness * (newCoverage - oldCoverage) / (1. - effectiveness*oldCoverage)
        # -------------------------
        # Incidence
        for ageName in ["12-23 months", "24-59 months"]:
            affectedFrac = 0.253 # take from data
            effectiveness = 0.65 # take from data
            reduction = affectedFrac * effectiveness * (newCoverage - oldCoverage) / (1. - effectiveness*oldCoverage)
            self.incidenceDiarrhea[ageName] *= 1.-reduction
        # -------------------------
        return stuntingUpdate, mortalityReduction
        
        
    def getMortalityReduction(self, newCoverage):
        mortalityReduction={}
        for ageName in self.ages:
            mortalityReduction[ageName]={}
            for cause in self.causesOfDeath:
                mortalityReduction[ageName][cause]=1.
        causeList = ((self.interventionMortalityEffectiveness.values()[0]).values()[0]).keys()        
        for ageName in self.ages:
            for intervention in newCoverage.keys():
                for cause in causeList:
                    affectedFrac = self.interventionAffectedFraction[intervention][ageName][cause]
                    effectiveness = self.interventionMortalityEffectiveness[intervention][ageName][cause]
                    newCoverageVal = newCoverage[intervention]
                    oldCoverage = self.interventionCoverages[intervention]
                    reduction = affectedFrac * effectiveness * (newCoverageVal - oldCoverage) / (1. - effectiveness*oldCoverage)
                    mortalityReduction[ageName][cause] *= 1. - reduction
        return mortalityReduction            
        
        
    def getStuntingUpdate(self, newCoverage):
        stuntingUpdate = {}
        for ageName in self.ages:
            stuntingUpdate[ageName] = 1
            oldProbStunting = self.stuntingDistribution[ageName]["high"] + self.stuntingDistribution[ageName]["moderate"]
            for intervention in newCoverage.keys():            
                if intervention == 'Zinc supplementation': 
                    probStuntingIfZinc = self.constants.fracStuntedIfZinc["zinc"][ageName]
                    probStuntingIfNoZinc = self.constants.fracStuntedIfZinc["nozinc"][ageName]
                    newProbStunting = newCoverage[intervention]*probStuntingIfZinc + (1.-newCoverage[intervention])*probStuntingIfNoZinc
                    reduction = (oldProbStunting - newProbStunting)/oldProbStunting
                    
                else:      
                    reduction = 0
                    
                stuntingUpdate[ageName] *= 1. - reduction
        return stuntingUpdate        
            
            
                        

        
        
