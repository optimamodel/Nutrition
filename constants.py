# -*- coding: utf-8 -*-
"""
Created on Mon Feb 29 11:35:02 2016

@author: ruth
"""

class Constants:
    def __init__(self, data, model):
        self.data = data
        self.model = model
        
        self.underlyingMortalityByAge = []        
        self.probStuntedIfNotPreviously = 0
        self.probStuntedIfPreviously = 0
        self.baselineProbBirthOutcome = {}  
        
        self.getUnderlyingMortalityByAge()
        self.getStuntingProbabilities()
        self.getBaselineProbBirthOutcome()

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
        from numpy import sqrt 
        numAgeGroups = len(self.model.listOfAgeCompartments)
        # probability of stunting progression
        self.probStuntedIfNotPreviously = {}
        self.probStuntedIfPreviously = {}
        for ageInd in range(1,numAgeGroups):
            ageName = self.data.ages[ageInd]
            OddsRatio = self.data.ORstuntingProgression[ageName]
            numStuntedNow =  self.model.listOfAgeCompartments[ageInd].dictOfBoxes["high"]["normal"]["exclusive"].populationsSize
            numNotStuntedNow = 0.
            for stuntingStatus in ["normal", "mild", "moderate"]:
                numNotStuntedNow += self.model.listOfAgeCompartments.dictOfBoxes[stuntingStatus]["normal"]["exclusive"].populationsSize
            numTotalNow = numStuntedNow + numNotStuntedNow
            FracStuntedNow = numStuntedNow / numTotalNow # aka Fn
            FracNotStuntedNow = 1 - FracStuntedNow
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
        


    # calculation of probability of birth outcome (given baseline maternalAge=18-34 years , birthOrder=second or third, timeBetweenBirths=>24 months 
    # P(birthOutcome | standard (maternalAge,birthOrder,timeBtwn))
    def getBaselineProbBirthOutcome(self):
        # P(maternalAge,birthOrder,timeBtwn)
        probBirthAndTime = {}
        for maternalAge in ["<18 years","18-34 years","35-49 years"]:
            probBirthAndTime[maternalAge]={}
            for birthOrder in ["first","second or third","greater than third"]:
                probBirthAndTime[maternalAge][birthOrder]={}
                probCircumstance = self.data.birthCircumstanceDist[maternalAge][birthOrder]
                if birthOrder == "first":
                    probBirthAndTime[maternalAge][birthOrder]["first"] = probCircumstance
                else:
                    probTimeBtwnBirths = self.data.timeBetweenBirthsDist
                    probFirst = probTimeBtwnBirths["first"]
                    for timeBtwnBirths in ["<18 months","18-23 months","<24 months"]:
                        probTimeIfNotFirst = probTimeBtwnBirths[timeBtwnBirths]/(1-probFirst)
                        probBirthAndTime[maternalAge][birthOrder][timeBtwnBirths] = probCircumstance * probTimeIfNotFirst
        # now calculate baseline
        sumProbOutcome = 0.
        # only need to calculate for first 3 birth outcomes, for which relative risks are provided
        for birthOutcome in ["pretermSGA","pretermAGA","termSGA"]:
            summation = 0.
            for maternalAge in ["<18 years","18-34 years","35-49 years"]:
                for birthOrder in ["first","second or third","greater than third"]:
                    for timeBtwnBirths in ["first","<18 months","18-23 months","<24 months"]:
                        P_bt = probBirthAndTime[maternalAge][birthOrder][timeBtwnBirths]
                        RR_gb = self.data.RRbirthOutcomeByAgeAndOrder[birthOutcome][maternalAge][birthOrder]
                        RR_gt = self.data.RRbirthOutcomeByTime[birthOutcome][timeBtwnBirths]
                        summation += P_bt * RR_gb * RR_gt
            self.baselineProbBirthOutcome[birthOutcome] = self.data.probBirthOutcome[birthOutcome] / summation
            sumProbOutcome += self.baselineProbBirthOutcome[birthOutcome]
        self.baselineProbBirthOutcome["termAGA"] = 1. - sumProbOutcome

