# -*- coding: utf-8 -*-
"""
Created on Fri April 1 2016

@author: madhura
"""
from __future__ import division
from copy import deepcopy as dcp

class Params:
    def __init__(self, data, derived, keyList):
        self.derived = derived

        self.ages = keyList['ages']
        self.birthOutcomes = keyList['birthOutcomes']
        self.wastingList = keyList['wastingList']
        self.stuntingList = keyList['stuntingList']
        self.breastfeedingList = keyList['breastfeedingList']

        self.causesOfDeath = dcp(data.causesOfDeath)
        self.conditions = dcp(data.conditions)
        self.demographics = dcp(data.demographics)
        #self.totalMortality = dcp(data.totalMortality)
        self.causeOfDeathDist = dcp(data.causeOfDeathDist)
        self.stuntingDistribution = dcp(data.stuntingDistribution)
        self.wastingDistribution = dcp(data.wastingDistribution)
        self.breastfeedingDistribution = dcp(data.breastfeedingDistribution)
        self.RRStunting = dcp(data.RRStunting)
        self.RRWasting = dcp(data.RRWasting)
        self.RRBreastfeeding = dcp(data.RRBreastfeeding)
        self.RRdeathByBirthOutcome = dcp(data.RRdeathByBirthOutcome)
        #self.ORstuntingProgression = dcp(data.ORstuntingProgression)
        self.incidences = dcp(data.incidences)
        #self.RRdiarrhea = dcp(data.RRdiarrhea)
        #self.ORstuntingCondition = dcp(data.ORstuntingCondition)
        #self.ORstuntingBirthOutcome = dcp(data.ORstuntingBirthOutcome)
        self.birthOutcomeDist = dcp(data.birthOutcomeDist)
        #self.ORstuntingIntervention = dcp(data.ORstuntingIntervention)
        #self.ORappropriatebfIntervention = dcp(data.ORappropriatebfIntervention)
        self.ageAppropriateBreastfeeding = dcp(data.ageAppropriateBreastfeeding)
        self.interventionCoverages = dcp(data.interventionCoveragesCurrent)
        self.interventionMortalityEffectiveness = dcp(data.interventionMortalityEffectiveness)
        self.interventionAffectedFraction = dcp(data.interventionAffectedFraction)
        self.interventionIncidenceEffectiveness = dcp(data.interventionIncidenceEffectiveness)
        self.interventionsMaternal = dcp(data.interventionsMaternal)
        self.complementsList = dcp(data.complementsList)
    

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
                probStuntingIfCovered    = self.derived.probStuntedIfCovered[intervention]["covered"][ageName]
                probStuntingIfNotCovered = self.derived.probStuntedIfCovered[intervention]["not covered"][ageName]
                newProbStunting = newCoverage[intervention]*probStuntingIfCovered + (1.-newCoverage[intervention])*probStuntingIfNotCovered
                reduction = (oldProbStunting - newProbStunting)/oldProbStunting
                stuntingUpdate[ageName] *= 1. - reduction
        return stuntingUpdate        
            

    def getAppropriateBFNew(self, newCoverage):
        appropriatebfFracNew = {}
        for ageName in self.ages:
            appropriatePractice = self.ageAppropriateBreastfeeding[ageName]
            appropriatebfFracBefore = self.breastfeedingDistribution[ageName][appropriatePractice]
            appropriatebfFracNew[ageName] = appropriatebfFracBefore
            for intervention in newCoverage.keys():
                probAppropriateIfCovered    = self.derived.probAppropriatelyBreastfedIfCovered[intervention]["covered"][ageName]
                probAppropriateIfNotCovered = self.derived.probAppropriatelyBreastfedIfCovered[intervention]["not covered"][ageName]
                appropriatebfFracNewThis = newCoverage[intervention]*probAppropriateIfCovered + (1.-newCoverage[intervention])*probAppropriateIfNotCovered
                fracAdd = appropriatebfFracNewThis - appropriatebfFracBefore
                appropriatebfFracNew[ageName] += fracAdd
        return appropriatebfFracNew               

            
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

        
    def getStuntingUpdateDueToIncidence(self, beta):
        stuntingUpdate = {}
        for ageName in self.ages:
            stuntingUpdate[ageName] = 1.
            newProbStunting = 0
            oldProbStunting = self.stuntingDistribution[ageName]["high"] + self.stuntingDistribution[ageName]["moderate"]
            for breastfeedingCat in self.breastfeedingList:
                pab = self.breastfeedingDistribution[ageName][breastfeedingCat]
                t1 = beta[ageName][breastfeedingCat] * self.derived.fracStuntedIfDiarrhea["dia"][ageName]
                t2 = (1 - beta[ageName][breastfeedingCat]) * self.derived.fracStuntedIfDiarrhea["nodia"][ageName]                
                newProbStunting += pab * (t1 + t2)
            reduction = (oldProbStunting - newProbStunting)/oldProbStunting
            stuntingUpdate[ageName] *= 1. - reduction
        return stuntingUpdate
        
        
    def getStuntingUpdateComplementaryFeeding(self, newCoverage):
        stuntingUpdate = {}
        FracSecure = 1. - self.demographics['fraction food insecure']
        FracCoveredEduc = newCoverage['Complementary feeding (education)']
        FracCoveredSupp = newCoverage['Complementary feeding (supplementation)']
        Frac = [0.]*4
        Frac[0] = FracSecure * FracCoveredEduc
        Frac[1] = FracSecure * (1 - FracCoveredEduc)
        Frac[2] = (1 - FracSecure) * FracCoveredSupp
        Frac[3] = (1 - FracSecure) * (1 - FracCoveredSupp)
        for ageName in self.ages:
            stuntingUpdate[ageName] = 1.
            oldProbStunting = self.stuntingDistribution[ageName]["high"] + self.stuntingDistribution[ageName]["moderate"]
            newProbStunting = 0
            for i in range(len(self.complementsList)):            
                probThisGroup = self.derived.probsStuntingComplementaryFeeding[ageName][self.complementsList[i]]
                newProbStunting += probThisGroup * Frac[i]
            reduction = (oldProbStunting - newProbStunting)/oldProbStunting
            stuntingUpdate[ageName] *= 1. - reduction
        return stuntingUpdate           
