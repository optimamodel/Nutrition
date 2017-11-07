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

        for key in keyList.keys():
            setattr(self, key, keyList[key])

        self.causesOfDeath = dcp(data.causesOfDeath)
        self.conditions = dcp(data.conditions)
        self.demographics = dcp(data.demographics)
        #self.rawMortality = dcp(data.rawMortality)
        self.causeOfDeathDist = dcp(data.causeOfDeathDist)
        self.stuntingDistribution = dcp(data.stuntingDistribution)
        self.wastingDistribution = dcp(data.wastingDistribution)
        self.breastfeedingDistribution = dcp(data.breastfeedingDistribution)
        self.RRdeathStunting = dcp(data.RRdeathStunting)
        self.RRdeathWasting = dcp(data.RRdeathWasting)
        self.RRdeathBreastfeeding = dcp(data.RRdeathBreastfeeding)
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
        self.coverage = dcp(data.coverage)
        self.effectivenessMortality = dcp(data.effectivenessMortality)
        self.affectedFraction = dcp(data.affectedFraction)
        self.effectivenessIncidence = dcp(data.effectivenessIncidence)
        self.interventionsMaternal = dcp(data.interventionsMaternal)
        self.foodSecurityGroups = dcp(data.foodSecurityGroups)
    

# Add all functions for updating parameters due to interventions here....

    def getMortalityUpdate(self, newCoverage):
        mortalityUpdate = {}
        for ageName in self.ages:
            mortalityUpdate[ageName] = {}
            for cause in self.causesOfDeath:
                mortalityUpdate[ageName][cause] = 1.
        causeList = ((self.effectivenessMortality.values()[0]).values()[0]).keys()        
        for ageName in self.ages:
            for intervention in newCoverage.keys():
                for cause in causeList:
                    affectedFrac = self.affectedFraction[intervention][ageName][cause]
                    effectiveness = self.effectivenessMortality[intervention][ageName][cause]
                    newCoverageVal = newCoverage[intervention]
                    oldCoverage = self.coverage[intervention]
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
                oldCoverage = self.coverage[intervention]
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
        correctbfFracNew = {}
        for ageName in self.ages:
            correctPractice = self.ageAppropriateBreastfeeding[ageName]
            correctbfFracBefore = self.breastfeedingDistribution[ageName][correctPractice]
            correctbfFracNew[ageName] = correctbfFracBefore
            for intervention in newCoverage.keys():
                probCorrectIfCovered    = self.derived.probCorrectlyBreastfedIfCovered[intervention]["covered"][ageName]
                probCorrectIfNotCovered = self.derived.probCorrectlyBreastfedIfCovered[intervention]["not covered"][ageName]
                correctbfFracNewThis = newCoverage[intervention]*probCorrectIfCovered + (1.-newCoverage[intervention])*probCorrectIfNotCovered
                fracAdd = correctbfFracNewThis - correctbfFracBefore
                correctbfFracNew[ageName] += fracAdd
        return correctbfFracNew               

            
    def getIncidenceUpdate(self, newCoverage):
        incidenceUpdate = {}
        for ageName in self.ages:
            incidenceUpdate[ageName] = {}
            for condition in self.conditions:
                incidenceUpdate[ageName][condition] = 1.
        for ageName in self.ages:
            for intervention in newCoverage.keys():
                for condition in self.conditions:
                    affectedFrac = self.affectedFraction[intervention][ageName][condition]
                    effectiveness = self.effectivenessIncidence[intervention][ageName][condition]
                    newCoverageVal = newCoverage[intervention]
                    oldCoverage = self.coverage[intervention]
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
        for ageName in self.ages:
            stuntingUpdate[ageName] = 1.      
        key1 = 'IYCF'
        key2 = 'Public provision of complementary foods'
        # collect data
        X1 = self.demographics['fraction poor']
        X2 = self.demographics['fraction food insecure (poor)']
        X3 = self.demographics['fraction food insecure (not poor)']
        Ce  = newCoverage[key1]
        Cse = newCoverage[key2]
        # calculate fraction of children in each of the food security/access to intervention groups
        Frac = [0.]*4
        Frac[0] = X1*(1.-X2)*Ce + (1.-X1)*(1.-X3)*Ce + X1*(1.-X2)*(1.-Ce)*Cse
        Frac[1] = X1*(1.-X2)*(1.-Ce)*(1.-Cse) + (1.-X1)*(1.-X3)*(1.-Ce)
        Frac[2] = X1*X2*Cse + (1.-X1)*X3*Ce
        Frac[3] = X1*X2*(1.-Cse) + (1.-X1)*X3*(1.-Ce)
        # calculate stunting update
        for ageName in self.ages:
            oldProbStunting = self.stuntingDistribution[ageName]["high"] + self.stuntingDistribution[ageName]["moderate"]
            newProbStunting = 0
            for i in range(len(self.foodSecurityGroups)):            
                probStuntedThisGroup = self.derived.probStuntedComplementaryFeeding[ageName][self.foodSecurityGroups[i]]
                newProbStunting += probStuntedThisGroup * Frac[i]
            reduction = (oldProbStunting - newProbStunting)/oldProbStunting
            stuntingUpdate[ageName] *= 1. - reduction
        return stuntingUpdate           
