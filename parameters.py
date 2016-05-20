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
        self.conditions = dcp(data.conditions)
        self.totalMortality = dcp(data.totalMortality)
        self.causeOfDeathDist = dcp(data.causeOfDeathDist)
        self.stuntingDistribution = dcp(data.stuntingDistribution)
        self.wastingDistribution = dcp(data.wastingDistribution)
        self.breastfeedingDistribution = dcp(data.breastfeedingDistribution)
        self.RRStunting = dcp(data.RRStunting)
        self.RRWasting = dcp(data.RRWasting)
        self.RRBreastfeeding = dcp(data.RRBreastfeeding)
        self.RRdeathByBirthOutcome = dcp(data.RRdeathByBirthOutcome)
        self.ORstuntingProgression = dcp(data.ORstuntingProgression)
        self.incidences = dcp(data.incidences)
        self.RRdiarrhea = dcp(data.RRdiarrhea)
        self.ORstuntingCondition = dcp(data.ORstuntingCondition)
        #self.birthCircumstanceDist = dcp(data.birthCircumstanceDist)
        #self.timeBetweenBirthsDist = dcp(data.timeBetweenBirthsDist)
        #self.RRbirthOutcomeByAgeAndOrder = dcp(data.RRbirthOutcomeByAgeAndOrder)
        #self.RRbirthOutcomeByTime = dcp(data.RRbirthOutcomeByTime)
        self.ORstuntingBirthOutcome = dcp(data.ORstuntingBirthOutcome)
        self.birthOutcomeDist = dcp(data.birthOutcomeDist)
        self.ORstuntingIntervention = dcp(data.ORstuntingIntervention)
        self.ORexclusivebfIntervention = dcp(data.ORexclusivebfIntervention)
        self.interventionCoverages = dcp(data.interventionCoveragesCurrent)
        self.interventionMortalityEffectiveness = dcp(data.interventionMortalityEffectiveness)
        self.interventionAffectedFraction = dcp(data.interventionAffectedFraction)
        self.interventionIncidenceEffectiveness = dcp(data.interventionIncidenceEffectiveness)
        self.interventionsMaternal = dcp(data.interventionsMaternal)
    

# Add all functions for updating parameters due to interventions here....

    def getMortalityUpdate(self, newCoverage):
        mortalityUpdate = {}
        for ageName in self.ages:
            mortalityUpdate[ageName] = {}
            for cause in self.causesOfDeath:
                mortalityUpdate[ageName][cause] = 1.
        causeList = ((self.interventionMortalityEffectiveness.values()[0]).values()[0]).keys()        
        for ageName in self.ages:
            for intervention in newCoverage.keys():
                for cause in causeList:
                    affectedFrac = self.interventionAffectedFraction[intervention][ageName][cause]
                    effectiveness = self.interventionMortalityEffectiveness[intervention][ageName][cause]
                    newCoverageVal = newCoverage[intervention]
                    oldCoverage = self.interventionCoverages[intervention]
                    reduction = affectedFrac * effectiveness * (newCoverageVal - oldCoverage) / (1. - effectiveness*oldCoverage)
                    mortalityUpdate[ageName][cause] *= 1. - reduction
        return mortalityUpdate           
        
    def getBirthOutcomeUpdate(self, newCoverage):
        birthOutcomeUpdate = {}
        for outcome in self.birthOutcomes:
            birthOutcomeUpdate[outcome] = 1.
        for intervention in newCoverage.keys():
            for outcome in self.birthOutcomes:
                affectedFrac = self.interventionsMaternal[intervention][outcome]['affected fraction']
                effectiveness = self.interventionsMaternal[intervention][outcome]['effectiveness']
                newCoverageVal = newCoverage[intervention]
                oldCoverage = self.interventionCoverages[intervention]
                reduction = affectedFrac * effectiveness * (newCoverageVal - oldCoverage) / (1. - effectiveness*oldCoverage)
                birthOutcomeUpdate[outcome] *= 1. - reduction
        return birthOutcomeUpdate               
        
        
    def getStuntingUpdate(self, newCoverage):
        stuntingUpdate = {}
        for ageName in self.ages:
            stuntingUpdate[ageName] = 1.
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
            
    """
    def getBreastfeedingUpdate(self, newCoverage):
        breastfeedingUpdate = {}
        for ageName in self.ages:
            breastfeedingUpdate[ageName] = {}
            for breastfeedingCat in self.breastfeedingList:
                breastfeedingUpdate[ageName][breastfeedingCat] = 1.
            oldFracExclusive = self.breastfeedingDistribution[ageName]["exclusive"]
            for intervention in newCoverage.keys():
                probStuntingIfCovered    = self.constants.fracStuntedIfCovered["zinc"][ageName]
                probStuntingIfNotCovered = self.constants.fracStuntedIfCovered["nozinc"][ageName]
                newFracExclusive = newCoverage[intervention]*probStuntingIfCovered + (1.-newCoverage[intervention])*probStuntingIfNotCovered
                reduction = (oldFracExclusive - newFracExclusive)/oldFracExclusive
                breastfeedingUpdate[breastfeedingCat] *= 1. - reduction
        return breastfeedingUpdate               
    """
            
    def getIncidenceUpdate(self, newCoverage):
        incidenceUpdate = {}
        for ageName in self.ages:
            incidenceUpdate[ageName] = {}
            for condition in self.conditions:
                incidenceUpdate[ageName][condition] = 1.
        for ageName in self.ages:
            for intervention in newCoverage.keys():
                for condition in self.conditions:
                    affectedFrac = self.interventionAffectedFraction[intervention][ageName][condition]
                    effectiveness = self.interventionIncidenceEffectiveness[intervention][ageName][condition]
                    newCoverageVal = newCoverage[intervention]
                    oldCoverage = self.interventionCoverages[intervention]
                    reduction = affectedFrac * effectiveness * (newCoverageVal - oldCoverage) / (1. - effectiveness*oldCoverage)
                    incidenceUpdate[ageName][condition] *= 1. - reduction
        return incidenceUpdate                         

        
    def getIncidenceStuntingUpdateGivenBeta(self, beta):
        stuntingUpdate = {}
        for ageName in self.ages:
            stuntingUpdate[ageName] = 1.
            newProbStunting = 0
            oldProbStunting = self.stuntingDistribution[ageName]["high"] + self.stuntingDistribution[ageName]["moderate"]
            for breastfeedingCat in self.breastfeedingList:
                pab = self.breastfeedingDistribution[ageName][breastfeedingCat]
                t1 = beta[ageName][breastfeedingCat] * self.constants.fracStuntedIfDiarrhea["dia"][ageName]
                t2 = (1 - beta[ageName][breastfeedingCat]) * self.constants.fracStuntedIfDiarrhea["nodia"][ageName]                
                newProbStunting += pab * (t1 + t2)
            reduction = (oldProbStunting - newProbStunting)/oldProbStunting
            stuntingUpdate[ageName] *= 1. - reduction
        return stuntingUpdate
            
