# -*- coding: utf-8 -*-
"""
Created on Fri Feb 26 15:57:07 2016

@author: ruth
"""

class Data:
    def __init__(self, ages, causesOfDeath, totalMortalityByAge, causeOfDeathByAge, RRStunting, RRWasting, RRBreastFeeding, stuntingDistribution, wastingDistribution, breastFeedingDistribution):
        self.ages = ages
        self.causesOfDeath = causesOfDeath
        self.totalMortalityByAge = totalMortalityByAge
        self.causeOfDeathByAge = causeOfDeathByAge
        self.RRStunting = RRStunting
        self.RRWasting = RRWasting
        self.RRBreastFeeding = RRBreastFeeding
        self.stuntingDistribution = stuntingDistribution
        self.wastingDistribution = wastingDistribution
        self.breastFeedingDistribution = breastFeedingDistribution
    
    
    
def getFakeData():
        
    ages = ["0-1 month", "1-6 months", "6-12 months", "12-24 months", "24-59 months"]
    causesOfDeath = ["diarrhea", "malaria"]
    #THIS IS LEFT HAND SIDE OF EQUATION
    totalMortalityByAge = [22, 35, 35, 35, 49]
    
    #causes of death are percent (0 to 1)
    causeOfDeathByAge = {"diarrhea":{"0-1 month":0.4, "1-6 months":0.1, "6-12 months":0.1, "12-24 months":0.1, "24-59 months":0.1}, "malaria":{"0-1 month":0.2, "1-6 months":0.2, "6-12 months":0.2, "12-24 months":0.2, "24-59 months":0.2}}
    
    #Relative Risks for stunting, wasting, breast feeding
    RRStuntingMalaria = {"normal":{"0-1 month":0.1, "1-6 months":0.1, "6-12 months":0.1, "12-24 months":0.1, "24-59 months":0.1},
                         "mild":{"0-1 month":0.1, "1-6 months":0.1, "6-12 months":0.1, "12-24 months":0.1, "24-59 months":0.1},
                         "moderate":{"0-1 month":0.1, "1-6 months":0.1, "6-12 months":0.1, "12-24 months":0.1, "24-59 months":0.1},
                         "high":{"0-1 month":0.1, "1-6 months":0.1, "6-12 months":0.1, "12-24 months":0.1, "24-59 months":0.1} }
    
    RRBreastFeedingMalaria = {"exclusive":{"0-1 month":0.1, "1-6 months":0.1, "6-12 months":0.1, "12-24 months":0.1, "24-59 months":0.1},
                                 "predominant":{"0-1 month":0.1, "1-6 months":0.1, "6-12 months":0.1, "12-24 months":0.1, "24-59 months":0.1},
                                 "partial":{"0-1 month":0.1, "1-6 months":0.1, "6-12 months":0.1, "12-24 months":0.1, "24-59 months":0.1},
                                 "none":{"0-1 month":0.1, "1-6 months":0.1, "6-12 months":0.1, "12-24 months":0.1, "24-59 months":0.1} }    
    
    #make a dictionary of RR for each disease
    #diarrhea would be same form as malaria, just re-use for now
    RRStunting = {"diarrhea":RRStuntingMalaria, "malaria":RRStuntingMalaria}
    RRWasting = {"diarrhea":RRStuntingMalaria, "malaria":RRStuntingMalaria} #this is just the same as stunting for now    
    RRBreastFeeding = {"diarrhea":RRBreastFeedingMalaria, "malaria":RRBreastFeedingMalaria} #this is just the same as stunting for now
    
    #stunting, wasting, breast feeding distributions (similar form to one disease table of RR, so just re-use for now)
    stuntingDistribution = RRStuntingMalaria
    wastingDistribution = RRStuntingMalaria
    breastFeedingDistribution = RRBreastFeedingMalaria
    
    fakeData = Data(ages, causesOfDeath, totalMortalityByAge, causeOfDeathByAge, RRStunting, RRWasting, RRBreastFeeding, stuntingDistribution, wastingDistribution, breastFeedingDistribution)
    return fakeData
    
