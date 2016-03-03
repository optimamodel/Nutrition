# -*- coding: utf-8 -*-
"""
Created on Mon Feb 29 11:35:02 2016

@author: ruth
"""

class Constants:
    def __init__(self, data, model):
        self.data = data
        self.model = model
        self.underlyingMortalityByAge = getUnderlyingMortalityByAge(self)
        self.probStuntedIfNotPreviously = 0
        self.probStuntedIfPreviously = 0
        self.getStuntingProbabilities(self)

    def getUnderlyingMortalityByAge(self):
        #Equation is:  LHS = RHS * X
        #we are solving for X
        RHS = []
        for age in self.data.ages:
            count = 0
            for cause in self.data.causesOfDeath:
                for stuntingStatus in ["normal", "mild", "moderate", "high"]:
                        for wastingStatus in ["normal", "mild", "moderate", "high"]:
                            for breastFeedingStatus in ["exclusive", "predominant", "partial", "none"]:
                                t1 = self.data.stuntingDistribution[stuntingStatus][age]
                                t2 = self.data.wastingDistribution[wastingStatus][age] 
                                t3 = self.data.breastFeedingDistribution[breastFeedingStatus][age]
                                t4 = self.data.RRStunting[cause][stuntingStatus][age]
                                t5 = self.data.RRWasting[cause][wastingStatus][age]
                                t6 = self.data.RRBreastFeeding[cause][breastFeedingStatus][age]
                                t7 = self.data.causeOfDeathByAge[cause][age]
                                count += t1 * t2 * t3 * t4 * t5 * t6 * t7
            RHS.append(count)     
        
        
        LHS = [float(i) for i in self.data.totalMortalityByAge]
        
        X = []
        for i in range(0, len(LHS)):
            X.append(LHS[i] / RHS[i])
        Xdictionary = dict(zip(self.data.ages, X))  
        #return Xdictionary
        self.underlyingMortalityByAge = Xdictionary
    

    def getStuntingProbabilities(self):
        import sqrt from numpy
        numAgeGroups = len(self.model.listOfAgeCompartments)
        # probability of stunting progression
        self.probStuntedIfNotPreviously = {}
        self.probStuntedIfPreviously = {}
        for ageInd in range(1,numAgeGroups):
            ageName = self.data.ages[ageInd]
            OddsRatio = self.data.ORstuntingProgression[ageName]
            numStuntedNow =  self.model.listOfAgeCompartments.[ageInd].dictOfBoxes["high"]["normal"]["exclusive"].populationsSize
            numNotStuntedNow = 0.
            for stuntingStatus in ["normal", "mild", "moderate"]:
                numNotStuntedNow += self.model.listOfAgeCompartments.dictOfBoxes[stuntingStatus]["normal"]["exclusive"].populationsSize
            numTotalNow = numStuntedNow + numNotStuntedNow
            FracStuntedNow = numStuntedNow / numTotalNow # aka Fn
            # solve quadratic equation
            a = FracNotStuntedNow*(1-OddsRatio)
            b = -numTotalNow
            c = FracStuntedNow
            det = sqrt(b**2 - 4.*a*c)
            soln1 = (-b + det)/(2.*a)
            soln2 = (-b - det)/(2.*a)
            # not sure what to do if both or neither are solutions
            if(soln1>0.)and(soln1<1.): p0 = soln1
            if(soln2>0.)and(soln2<1.): p0 = soln2
            self.probStuntedIfNotPreviously[ageName] = p0
            self.probStuntedIfPreviously[ageName]    = p0*OddsRatio/(1.-p0+OddsRatio*p0)
        