# -*- coding: utf-8 -*-
"""
Created on Mon Feb 29 11:35:02 2016

@author: ruth
"""

class Constants:
    def __init__(self, data, model):
        self.data = data
        self.model = model
        
        self.underlyingMortalities = {}
        self.probStuntedIfPrevStunted = {}
        self.probStuntedIfDiarrhoea = {}
        self.probStunted = {}
        self.baselineProbsBirthOutcome = {}  
        self.probsBirthOutcome = {}  
        self.birthStuntingQuarticCoefficients = []
        self.baselineProbStuntingAtBirth = 0.
        self.probsStuntingAtBirth = {}

        self.getUnderlyingMortalities()
        self.getProbStuntingProgression()
        self.getProbStuntingDiarrhoea()
        self.getProbStunting()
        self.getBaselineProbsBirthOutcome()
        self.getBirthStuntingQuarticCoefficients()
        self.getProbStuntingAtBirthForBaselineBirthOutcome()
        self.getProbsStuntingAtBirth()


    def getUnderlyingMortalities(self):
        #Equation is:  LHS = RHS * X
        #we are solving for X
        # Calculate RHS for each age and cause
        RHS = {}
        for age in self.data.ages:
            RHS[age] = {}
            for cause in self.data.causesOfDeath:
                RHS[age][cause] = 0.
                for stuntingCat in ["normal", "mild", "moderate", "high"]:
                    for wastingCat in ["normal", "mild", "moderate", "high"]:
                        for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
                            t1 = self.data.stuntingDistribution[age][stuntingCat]
                            t2 = self.data.wastingDistribution[age][wastingCat] 
                            t3 = self.data.breastfeedingDistribution[age][breastfeedingCat]
                            t4 = self.data.RRStunting[age][cause][stuntingCat]
                            t5 = self.data.RRWasting[age][cause][wastingCat]
                            t6 = self.data.RRBreastfeeding[age][cause][breastfeedingCat]
                            RHS[age][cause] += t1 * t2 * t3 * t4 * t5 * t6
        # RHS for newborns only
        age = "<1 month"
        for cause in self.data.causesOfDeath:
            for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
                Pbf = self.data.breastfeedingDistribution[age][breastfeedingCat]
                RRbf = self.data.RRBreastfeeding[age][cause][breastfeedingCat]
                for birthoutcome in self.model.birthOutcomes:
                    Pbo = self.data.birthOutcomeDist[birthoutcome]
                    RRbo = self.data.RRdeathByBirthOutcome[cause][birthoutcome]
                    RHS[age][cause] += Pbf * RRbf * Pbo * RRbo
        # Calculated total mortality by age (corrected for units)
        MortalityCorrected = {}
        # note that mortality rate have currently been pre-divided by 1000
        # Newborns
        age = self.data.ages[0]
        Mnew = self.data.totalMortality[age]
        m1 = Mnew
        MortalityCorrected[age] = m1
        # 1-5 months
        age = self.data.ages[1]
        Minfant = self.data.totalMortality[age]
        Frac2 = (1.-Minfant)/(1.-m1)
        m2 = 1. - pow(Frac2,1./11.)
        #m2 = 1. - Frac2**(1./11.)
        MortalityCorrected[age] = m2
        # 6-12 months
        age = self.data.ages[2]
        m3 = m2
        MortalityCorrected[age] = m3
        # 12-24 months
        age = self.data.ages[3]
        Mu5 = self.data.totalMortality[age]
        Frac4 = (1.-Mu5)/(1.-m1)/(Frac2)
        #m4 = 1. - pow(Frac4,1./48.)
        m4 = 1. - Frac4**(1./48.)
        MortalityCorrected[age] = m4
        # 24-60 months
        age = self.data.ages[4]
        m5 = m4
        MortalityCorrected[age] = m5
        # Calculate LHS for each age and cause of death then solve for X
        Xdictionary = {} 
        for age in self.data.ages:
            Xdictionary[age] = {}
            for cause in self.data.causesOfDeath:
                LHS_age_cause = MortalityCorrected[age] * self.data.causeOfDeathDist[age][cause]
                Xdictionary[age][cause] = LHS_age_cause / RHS[age][cause]
        self.underlyingMortalities = Xdictionary
    


    def getProbStuntingProgression(self):
        from numpy import sqrt 
        numAgeGroups = len(self.model.listOfAgeCompartments)
        # probability of stunting progression
        self.probStuntedIfPrevStunted["notstunted"] = {}
        self.probStuntedIfPrevStunted["yesstunted"] = {}
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
            self.probStuntedIfPrevStunted["notstunted"][ageName] = p0
            self.probStuntedIfPrevStunted["yesstunted"][ageName] = p0*OddsRatio/(1.-p0+OddsRatio*p0)
        


    def getProbStuntingDiarrhoea(self):
        from numpy import sqrt 
        from math import pow
        numAgeGroups = len(self.model.listOfAgeCompartments)
        # probability of stunting progression
        self.probStuntedIfDiarrhoea["nodia"] = {}
        self.probStuntedIfDiarrhoea["dia"] = {}
        eps = 1.e-5
        for ageInd in range(1,numAgeGroups):
            ageName = self.data.ages[ageInd]
            thisAge = self.model.listOfAgeCompartments[ageInd]
            younger = self.model.listOfAgeCompartments[ageInd-1]
            Za = self.data.InciDiarrhoea[ageName]
            # population odds ratio = AO (see Eqn 3.9)
            RRnot = self.data.RRdiarrhoea[ageName]["none"]
            AO = pow(self.data.ORdiarrhoea[ageName],RRnot*Za/thisAge.agingRate)
            # instead have beta fracDiarrhoea
            fracDiarrhoea = 0.
            for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
                RDa = self.data.RRdiarrhoea[ageName][breastfeedingCat]
                fracDiarrhoea += 1. - (RRnot*Za-RDa*Za)/(RRnot*Za)
            # fraction stunted
            numStuntedThisAge = 0.
            numNotStuntedThisAge = 0.
            for wastingCat in ["normal", "mild", "moderate", "high"]:
                for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
                    for stuntingCat in ["moderate","high"]:
                        numStuntedThisAge    += thisAge.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize
                    for stuntingCat in ["normal", "mild"]:
                        numNotStuntedThisAge += thisAge.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize
            fracStuntedThisAge = numStuntedThisAge / (numStuntedThisAge + numNotStuntedThisAge + eps)
            # solve quadratic equation ax**2 + bx + c = 0
            a = (1.-fracDiarrhoea) * (1.-AO)
            b = (AO-1)*fracStuntedThisAge - AO*fracDiarrhoea - (1.-fracDiarrhoea)
            c = fracStuntedThisAge
            det = sqrt(b**2 - 4.*a*c)
            soln1 = (-b + det)/(2.*a)
            soln2 = (-b - det)/(2.*a)
            # not sure what to do if both or neither are solutions
            if(soln1>0.)and(soln1<1.): p0 = soln1
            if(soln2>0.)and(soln2<1.): p0 = soln2
            self.probStuntedIfDiarrhoea["nodia"][ageName] = p0
            self.probStuntedIfDiarrhoea["dia"][ageName]   = p0*AO/(1.-p0+AO*p0)



    def getProbStunting(self):
        numAgeGroups = len(self.model.listOfAgeCompartments)
        for ageInd in range(1,numAgeGroups):
            ageName = self.data.ages[ageInd]
            self.probStunted[ageName] = {}
            for prevStunt in ["notstunted","yesstunted"]:
                self.probStunted[ageName][prevStunt] = {}
                for prevDiarr in ["nodia","dia"]:
                    self.probStunted[ageName][prevStunt][prevDiarr] = 1. - (1.-self.probStuntedIfPrevStunted[prevStunt][ageName])*(1.-self.probStuntedIfDiarrhoea[prevDiarr][ageName])


        
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
            
            
