# -*- coding: utf-8 -*-
"""
Created on Fri April 1 2016

@author: madhura
"""
from __future__ import division

class Params:
    def __init__(self, data, constants, keyList):
        self.constants = constants
        self.ages, self.birthOutcomes, self.wastingList, self.stuntingList, self.breastfeedingList = keyList
        import helper as helperCode
        self.helper = helperCode.Helper()

        self.causesOfDeath = data.causesOfDeath
        self.causeOfDeathDist = data.causeOfDeathDist
        self.stuntingDistribution = data.stuntingDistribution
        self.wastingDistribution = data.wastingDistribution
        self.breastfeedingDistribution = data.breastfeedingDistribution
        self.RRStunting = data.RRStunting
        self.RRWasting = data.RRWasting
        self.RRBreastfeeding = data.RRBreastfeeding
        self.RRdeathByBirthOutcome = data.RRdeathByBirthOutcome
        self.ORstuntingProgression = data.ORstuntingProgression
        self.incidenceDiarrhea = data.incidenceDiarrhea
        self.RRdiarrhea = data.RRdiarrhea
        self.ORdiarrhea = data.ORdiarrhea
        self.birthCircumstanceDist = data.birthCircumstanceDist
        self.timeBetweenBirthsDist = data.timeBetweenBirthsDist
        self.RRbirthOutcomeByAgeAndOrder = data.RRbirthOutcomeByAgeAndOrder
        self.RRbirthOutcomeByTime = data.RRbirthOutcomeByTime
        self.ORBirthOutcomeStunting = data.ORBirthOutcomeStunting
        self.birthOutcomeDist = data.birthOutcomeDist
        self.ORstuntingZinc = data.ORstuntingZinc
        self.InterventionCoverages = data.InterventionCoveragesCurrent
        self.interventionMortalityEffectiveness = data.interventionMortalityEffectiveness
        self.interventionAffectedFraction = data.interventionAffectedFraction
    

# Add all functions for updating parameters due to interventions here....

    def increaseCoverageOfZinc(self, newCoverage):
        oldCoverage = self.InterventionCoverages["Zinc supplementation"]
        # -------------------------
        # calculate reduction in stunted fraction
        stuntingReduction = {}
        for ageName in self.ages:
            probStuntingIfZinc = self.constants.fracStuntedIfZinc["zinc"][ageName]
            probStuntingIfNoZinc = self.constants.fracStuntedIfZinc["nozinc"][ageName]
            oldProbStunting = self.stuntingDistribution[ageName]["high"] + self.stuntingDistribution[ageName]["moderate"]
            newProbStunting = newCoverage*probStuntingIfZinc + (1.-newCoverage)*probStuntingIfNoZinc
            stuntingReduction[ageName] = (oldProbStunting - newProbStunting)/oldProbStunting
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
        return stuntingReduction, mortalityReduction
        
        
    def getMortalityReduction(self, newCoverage):
        mortalityReduction={}
        for ageName in self.ages:
            mortalityReduction[ageName]={}
            for cause in self.causesOfDeath:
                mortalityReduction[ageName][cause]=1.
        causeList = ((self.interventionMortalityEffectiveness.values()[0]).values()[0]).keys()        
        for ageName in self.ages:
            for intervention in newCoverage:
                for cause in causeList:
                    affectedFrac = self.interventionAffectedFraction[intervention][ageName][cause]
                    effectiveness = self.interventionMortalityEffectiveness[intervention][ageName][cause]
                    newCoverageVal = newCoverage[intervention]
                    oldCoverage = self.InterventionCoverages[intervention]
                    reduction = affectedFrac * effectiveness * (newCoverageVal - oldCoverage) / (1. - effectiveness*oldCoverage)
                    mortalityReduction[ageName][cause] *= 1. - reduction
        return mortalityReduction            
        
        
    def getStuntingReduction(self, newCoverage):
        stuntingReduction = {}
        for ageName in self.ages:
            stuntingReduction[ageName] = 1
            oldProbStunting = self.stuntingDistribution[ageName]["high"] + self.stuntingDistribution[ageName]["moderate"]
            for intervention in newCoverage.keys():            
                if "zinc" or "Zinc" in intervention: 
                    probStuntingIfZinc = self.constants.fracStuntedIfZinc["zinc"][ageName]
                    probStuntingIfNoZinc = self.constants.fracStuntedIfZinc["nozinc"][ageName]
                    newProbStunting = newCoverage[intervention]*probStuntingIfZinc + (1.-newCoverage[intervention])*probStuntingIfNoZinc
                    reduction = (oldProbStunting - newProbStunting)/oldProbStunting
                    
                else:      
                    reduction = 0
                                 
                stuntingReduction[ageName] *= 1. - reduction    
        return stuntingReduction        
            
            
                        

        
        
