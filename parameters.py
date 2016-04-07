# -*- coding: utf-8 -*-
"""
Created on Fri April 1 2016

@author: madhura
"""

class Params:
    def __init__(self, data):
        #self.ages = data.ages
        self.causesOfDeath = data.causesOfDeath
        #self.totalMortality = data.totalMortality
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
    

# Add all functions for updating parameters due to interventions here....

