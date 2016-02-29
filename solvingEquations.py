# -*- coding: utf-8 -*-
"""
Created on Mon Feb 29 11:35:02 2016

@author: ruth
"""

#you can use the fake data for testing
#eg in getUnderlyingMortalityByAge(data), fakeData would be the data input
import fake_data as fakeDataCode
fakeData = fakeDataCode.getFakeData()


def getUnderlyingMortalityByAge(data):
    #Equation is:  LHS = RHS * X
    #we are solving for X
    RHS = []
    for age in data.ages:
        count = 0
        for cause in data.causesOfDeath:
            for stuntingStatus in ["normal", "mild", "moderate", "high"]:
                    for wastingStatus in ["normal", "mild", "moderate", "high"]:
                        for breastFeedingStatus in ["exclusive", "predominant", "partial", "none"]:
                            t1 = data.stuntingDistribution[stuntingStatus][age]
                            t2 = data.wastingDistribution[wastingStatus][age] 
                            t3 = data.breastFeedingDistribution[breastFeedingStatus][age]
                            t4 = data.RRStunting[cause][stuntingStatus][age]
                            t5 = data.RRWasting[cause][wastingStatus][age]
                            t6 = data.RRBreastFeeding[cause][breastFeedingStatus][age]
                            t7 = data.causeOfDeathByAge[cause][age]
                            count += t1 * t2 * t3 * t4 * t5 * t6 * t7
        RHS.append(count)     
    
    
    LHS = [float(i) for i in data.totalMortalityByAge]
    
    X = []
    for i in range(0, len(LHS)):
        X.append(LHS[i] / RHS[i])
    return X
    

