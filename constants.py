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
        self.baselineProbsBirthOutcome = {}  
        self.probsBirthOutcome = {}  
        self.birthStuntingQuarticCoefficients = []
        self.baselineProbStuntingAtBirth = 0.
        self.probsStuntingAtBirth = {}

        self.getUnderlyingMortalityByAge()
        self.getProbStuntingProgression()
        self.getProbStuntingDiarrhoea()
        self.getBaselineProbsBirthOutcome()
        self.getBirthStuntingQuarticCoefficients()
        self.getProbStuntingAtBirthForBaselineBirthOutcome()
        self.getProbsStuntingAtBirth()


    def getUnderlyingMortalityByAge(self):
        #Equation is:  LHS = RHS * X
        #we are solving for X
        RHS = []
        for age in self.data.ages:
            count = 0
            for cause in self.data.causesOfDeath:
                for stuntingStatus in ["normal", "mild", "moderate", "high"]:
                        for wastingStatus in ["normal", "mild", "moderate", "high"]:
                            for breastfeedingStatus in ["exclusive", "predominant", "partial", "none"]:
                                t1 = self.data.stuntingDistribution[stuntingStatus][age]
                                t2 = self.data.wastingDistribution[wastingStatus][age] 
                                t3 = self.data.breastfeedingDistribution[breastfeedingStatus][age]
                                t4 = self.data.RRStunting[cause][stuntingStatus][age]
                                t5 = self.data.RRWasting[cause][wastingStatus][age]
                                t6 = self.data.RRBreastfeeding[cause][breastfeedingStatus][age]
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
    


    def getProbStuntingProgression(self):
        from numpy import sqrt 
        numAgeGroups = len(self.model.listOfAgeCompartments)
        # probability of stunting progression
        self.probStuntedIfNotPreviously = {}
        self.probStuntedIfPreviously = {}
        eps = 1.e-5
        for ageInd in range(1,numAgeGroups):
            ageName = self.data.ages[ageInd]
            thisAge = self.model.listOfAgeCompartments[ageInd]
            younger = self.model.listOfAgeCompartments[ageInd-1]
            OddsRatio = self.data.ORstuntingProgression[ageName]
            numStuntedThisAge = 0.
            numStuntedYounger = 0.
            numNotStuntedThisAge = 0.
            numNotStuntedYounger = 0.
            for wastingCat in ["normal", "mild", "moderate", "high"]:
                for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
                    for stuntingCat in ["moderate","high"]:
                        numStuntedThisAge +=  thisAge.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize
                        numStuntedYounger +=  younger.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize
                    for stuntingCat in ["normal", "mild"]:
                        numNotStuntedThisAge += thisAge.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize
                        numNotStuntedYounger += younger.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize
            fracStuntedThisAge = numStuntedThisAge / (numStuntedThisAge + numNotStuntedThisAge + eps)
            fracStuntedYounger = numStuntedYounger / (numStuntedYounger + numNotStuntedYounger + eps)
            # solve quadratic equation ax**2 + bx + c = 0
            a = (1.-fracStuntedYounger) * (1.-OddsRatio)
            b = (OddsRatio-1)*fracStuntedThisAge - OddsRatio*fracStuntedYounger - (1.-fracStuntedYounger)
            c = fracStuntedThisAge
            det = sqrt(b**2 - 4.*a*c)
            soln1 = (-b + det)/(2.*a)
            soln2 = (-b - det)/(2.*a)
            # not sure what to do if both or neither are solutions
            if(soln1>0.)and(soln1<1.): p0 = soln1
            if(soln2>0.)and(soln2<1.): p0 = soln2
            self.probStuntedIfNotPreviously[ageName] = p0
            self.probStuntedIfPreviously[ageName]    = p0*OddsRatio/(1.-p0+OddsRatio*p0)
        


    def getProbStuntingDiarrhoea(self):
        from numpy import sqrt 
        numAgeGroups = len(self.model.listOfAgeCompartments)
        # probability of stunting progression
        self.probStuntedIfNotPreviously = {}
        self.probStuntedIfPreviously = {}
        eps = 1.e-5
        for ageInd in range(1,numAgeGroups):
            ageName = self.data.ages[ageInd]
            thisAge = self.model.listOfAgeCompartments[ageInd]
            younger = self.model.listOfAgeCompartments[ageInd-1]
            OddsRatio = self.data.ORstuntingProgression[ageName]
            numStuntedThisAge = 0.
            numStuntedYounger = 0.
            numNotStuntedThisAge = 0.
            numNotStuntedYounger = 0.
            for wastingCat in ["normal", "mild", "moderate", "high"]:
                for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
                    for stuntingCat in ["moderate","high"]:
                        numStuntedThisAge +=  thisAge.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize
                        numStuntedYounger +=  younger.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize
                    for stuntingCat in ["normal", "mild"]:
                        numNotStuntedThisAge += thisAge.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize
                        numNotStuntedYounger += younger.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize
            fracStuntedThisAge = numStuntedThisAge / (numStuntedThisAge + numNotStuntedThisAge + eps)
            fracStuntedYounger = numStuntedYounger / (numStuntedYounger + numNotStuntedYounger + eps)
            # solve quadratic equation ax**2 + bx + c = 0
            a = (1.-fracStuntedYounger) * (1.-OddsRatio)
            b = (OddsRatio-1)*fracStuntedThisAge - OddsRatio*fracStuntedYounger - (1.-fracStuntedYounger)
            c = fracStuntedThisAge
            det = sqrt(b**2 - 4.*a*c)
            soln1 = (-b + det)/(2.*a)
            soln2 = (-b - det)/(2.*a)
            # not sure what to do if both or neither are solutions
            if(soln1>0.)and(soln1<1.): p0 = soln1
            if(soln2>0.)and(soln2<1.): p0 = soln2
            self.probStuntedIfNotPreviously[ageName] = p0
            self.probStuntedIfPreviously[ageName]    = p0*OddsRatio/(1.-p0+OddsRatio*p0)


        
    # calculation of probabilities of birth outcome
    # given baseline maternalAge=18-34 years , birthOrder=second or third, timeBetweenBirths=>24 months 
    # P(birthOutcome | standard (maternalAge,birthOrder,timeBtwn)
    def getBaselineProbsBirthOutcome(self):
        # P(maternalAge,birthOrder,timeBtwn)
        probInterval = self.data.timeBetweenBirthsDist
        probAgeOrderInterval = {}
        for maternalAge in ["<18 years","18-34 years","35-49 years"]:
            probAgeOrderInterval[maternalAge] = {}
            for birthOrder in ["first","second or third","greater than third"]:
                probAgeOrderInterval[maternalAge][birthOrder] = {}
                probCircumstance = self.data.birthCircumstanceDist[maternalAge][birthOrder]
                for interval in ["first","<18 months","18-23 months","<24 months"]:
                    probAgeOrderInterval[maternalAge][birthOrder][interval] = 0.
                if birthOrder == "first":
                    probAgeOrderInterval[maternalAge][birthOrder]["first"] = probCircumstance 
                else:
                    probFirst = probInterval["first"]
                    for interval in ["<18 months","18-23 months","<24 months"]:
                        probTimeIfNotFirst = probInterval[interval] / (1-probFirst)
                        probAgeOrderInterval[maternalAge][birthOrder][interval] = probCircumstance * probTimeIfNotFirst
        # Probabilities for 3 of the birth outcomes
        sumProbOutcome = 0.
        # only need to calculate for first 3 birth outcomes, for which relative risks are provided
        for birthOutcome in ["Pre-term SGA","Pre-term AGA","Term SGA"]:
            summation = 0.
            for maternalAge in ["<18 years","18-34 years","35-49 years"]:
                for birthOrder in ["first","second or third","greater than third"]:
                    for interval in ["first","<18 months","18-23 months","<24 months"]:
                        P_bt = probAgeOrderInterval[maternalAge][birthOrder][interval]
                        RR_gb = self.data.RRbirthOutcomeByAgeAndOrder[birthOutcome][maternalAge][birthOrder]
                        RR_gt = self.data.RRbirthOutcomeByTime[birthOutcome][interval]
                        summation += P_bt * RR_gb * RR_gt
            self.baselineProbsBirthOutcome[birthOutcome] = self.data.birthOutcomeDist[birthOutcome] / summation
            # WARNING not sure if we should *just* calculate baseline or the overall probBirthOutcome
            # when in the code can we expect changes to RRs or P_bt via interventions?
            """
            self.probsBirthOutcome[birthOutcome] = 0.
            for maternalAge in ["<18 years","18-34 years","35-49 years"]:
                for birthOrder in ["first","second or third","greater than third"]:
                    for interval in ["first","<18 months","18-23 months","<24 months"]:
                        P_bt = probAgeOrderInterval[maternalAge][birthOrder][interval]
                        RR_gb = self.data.RRbirthOutcomeByAgeAndOrder[birthOutcome][maternalAge][birthOrder]
                        RR_gt = self.data.RRbirthOutcomeByTime[birthOutcome][interval]
                        self.probsBirthOutcome[birthOutcome] += baselineProbBirthOutcome * RR_gb * RR_gt * P_bt
            sumProbOutcome += self.probsBirthOutcome[birthOutcome]
            """
        self.baselineProbsBirthOutcome["Term AGA"] = 1. - sumProbOutcome

    


    def getBirthStuntingQuarticCoefficients(self):
        OR = [1.]*4
        OR[0] = 1.
        OR[1] = self.data.ORBirthOutcomeStunting["Term SGA"]
        OR[2] = self.data.ORBirthOutcomeStunting["Pre-term AGA"]
        OR[3] = self.data.ORBirthOutcomeStunting["Pre-term SGA"]
        FracBO = [0.]*4
        FracBO[1] = self.data.birthOutcomeDist["Term SGA"]    
        FracBO[2] = self.data.birthOutcomeDist["Pre-term AGA"]
        FracBO[3] = self.data.birthOutcomeDist["Pre-term SGA"]
        FracBO[0] = 1. - sum(FracBO[1:3])
        numNewborns        = 0.
        numNewbornsStunted = 0.
        for wastingCat in ["normal", "mild", "moderate", "high"]:
            for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
                for stuntingCat in ["normal","mild"]:
                    numNewborns +=self.model.listOfAgeCompartments[0].dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize
                for stuntingCat in ["moderate","high"]:
                    numNewborns +=self.model.listOfAgeCompartments[0].dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize
                    numNewbornsStunted +=self.model.listOfAgeCompartments[0].dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize
        FracStunted = float(numNewbornsStunted) / float(numNewborns)
        # [i] will refer to the three non-baseline birth outcomes
        A = FracBO[0]*(OR[1]-1.)*(OR[2]-1.)*(OR[3]-1.)
        B = (OR[1]-1.)*(OR[2]-1.)*(OR[3]-1.) * ( \
            sum( FracBO[0] / (OR[i]-1.)         for i in (1,2,3)) + \
            sum( OR[i] * FracBO[i] / (OR[i]-1.) for i in (1,2,3)) - \
            FracStunted )
        C = sum( FracBO[0] * (OR[i]-1.)         for i in (1,2,3)) + \
            sum( OR[i] * FracBO[i] * ((OR[1]-1.)+(OR[2]-1.)+(OR[3]-1.)-(OR[i]-1.)) for i in (1,2,3) ) - \
            sum( FracStunted*(OR[1]-1.)*(OR[2]-1.)*(OR[3]-1.)/(OR[i]-1.) for i in (1,2,3))
        D = FracBO[0] + \
            sum( OR[i] * FracBO[i] for i in (1,2,3)) - \
            sum( FracStunted * (OR[i]-1.) for i in (1,2,3))
        E = -FracStunted
        self.birthStuntingQuarticCoefficients = [A,B,C,D,E]



    # internal function to evaluate the quartic function for probability of stunting at birth at baseline birth outcome
    def evalQuartic(self,p0):
        from math import pow
        A,B,C,D,E = self.birthStuntingQuarticCoefficients
        return A*pow(p0,4) + B*pow(p0,3) + C*pow(p0,2) + D*p0 + E



    # SOLVE QUARTIC
    # p0 = Probability of Stunting at birth if Birth outcome = Term AGA
    def getProbStuntingAtBirthForBaselineBirthOutcome(self):
        eps = 0.001
        p0min = 0.
        p0max = 1.
        interval = p0max - p0min
        if self.evalQuartic(p0min)==0:
            self.baselineProbStuntingAtBirth = p0min
            return
        if self.evalQuartic(p0max)==0:
            self.baselineProbStuntingAtBirth = p0max
            return
        PositiveAtMin = self.evalQuartic(p0min)>0
        PositiveAtMax = self.evalQuartic(p0max)>0
        if(PositiveAtMin == PositiveAtMax): 
            raise ValueError("ERROR: Quartic function evaluated at 0 & 1 both on the same side")
        while interval > eps:
            p0x = (p0max-p0min)/2.
            if(self.evalQuartic(p0x)>0 == PositiveAtMin):
                p0min = p0x
                PositiveAtMin = self.evalQuartic(p0min)>0
            else:
                p0max = p0x
                PositiveAtMax = self.evalQuartic(p0max)>0
            interval = p0max - p0min
        self.baselineProbStuntingAtBirth = p0x




    def getProbsStuntingAtBirth(self):
        p0 = self.baselineProbStuntingAtBirth
        self.probsStuntingAtBirth["Term AGA"] = p0
        for birthOutcome in ["Pre-term SGA","Pre-term AGA","Term SGA"]:
            OR = self.data.ORBirthOutcomeStunting[birthOutcome]
            self.probsStuntingAtBirth[birthOutcome] = p0*OR / (1.-p0+OR*p0)
            pi = self.probsStuntingAtBirth[birthOutcome]
            if(pi<0. or pi>1.):
                raise ValueError("probability of stunting at birth, at outcome %s, is out of range (%f)"%(birthOutcome,pi))
            
            
