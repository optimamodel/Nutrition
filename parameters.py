# -*- coding: utf-8 -*-
"""
Created on Fri April 1 2016

@author: madhura
"""
from __future__ import division

class Params:
    def __init__(self, data, constants, keyList):
        self.constants = constants
        self.ages,self.birthOutcomes,self.wastingList,self.stuntingList,self.breastfeedingList = keyList
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
        self.InciDiarrhoea = data.InciDiarrhoea
        self.RRdiarrhoea = data.RRdiarrhoea
        self.ORdiarrhoea = data.ORdiarrhoea
        self.birthCircumstanceDist = data.birthCircumstanceDist
        self.timeBetweenBirthsDist = data.timeBetweenBirthsDist
        self.RRbirthOutcomeByAgeAndOrder = data.RRbirthOutcomeByAgeAndOrder
        self.RRbirthOutcomeByTime = data.RRbirthOutcomeByTime
        self.ORBirthOutcomeStunting = data.ORBirthOutcomeStunting
        self.birthOutcomeDist = data.birthOutcomeDist
        self.ORstuntingZinc = data.ORstuntingZinc
        self.InterventionCoverages = data.InterventionCoveragesCurrent
    

# Add all functions for updating parameters due to interventions here....

    def increaseCoverageOfZinc(self,newCoverage):
        oldCoverage = self.InterventionCoverages["Zinc supplementation"]
        for ageName in self.ages:
            probStuntingIfZinc = self.constants.fracStuntedIfZinc["zinc"][ageName]
            probStuntingIfNoZinc = self.constants.fracStuntedIfZinc["nozinc"][ageName]
            #oldProbStunting = 
            newProbStunting = newCoverage*probStuntingIfZinc + (1.-newCoverage)*probStuntingIfNoZinc
            self.stuntingDistribution[ageName] = self.helper.restratify(newProbStunting)
        affectedFrac = 0.253
        effectiveness = 0.65
        reduction = affectedFrac * effectiveness * (newCoverage - oldCoverage) / (1. - effectiveness*oldCoverage)
        self.InciDiarrhoea["12-23 months"] *= (1.-reduction)
