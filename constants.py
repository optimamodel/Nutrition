# -*- coding: utf-8 -*-
"""
Created on Mon Feb 29 11:35:02 2016

@author: ruth
"""
from __future__ import division

class Constants:
    def __init__(self, data, model, keyList):
        self.data = data
        self.model = model
        self.ages,self.birthOutcomes,self.wastingList,self.stuntingList,self.breastfeedingList = keyList
        
        self.underlyingMortalities = {}
        self.probStuntedIfPrevStunted = {}
        self.fracStuntedIfDiarrhea = {}
        self.fracStuntedIfZinc = {}
        #self.baselineProbsBirthOutcome = {}  
        self.probsBirthOutcome = {}  
        self.birthStuntingQuarticCoefficients = []
        self.baselineProbStuntingAtBirth = 0.
        self.probsStuntingAtBirth = {}

        self.getUnderlyingMortalities()
        self.getProbStuntingProgression()
        self.getFracStuntingGivenDiarrhea()
        self.getFracStuntingGivenZinc()
        #self.getBaselineProbsBirthOutcome()
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
                for stuntingCat in self.stuntingList:
                    for wastingCat in self.wastingList:
                        for breastfeedingCat in self.breastfeedingList:
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
            RHS[age][cause] = 0.
            for breastfeedingCat in self.breastfeedingList:
                Pbf = self.data.breastfeedingDistribution[age][breastfeedingCat]
                RRbf = self.data.RRBreastfeeding[age][cause][breastfeedingCat]
                for birthoutcome in self.birthOutcomes:
                    Pbo = self.data.birthOutcomeDist[birthoutcome]
                    RRbo = self.data.RRdeathByBirthOutcome[cause][birthoutcome]
                    RHS[age][cause] += Pbf * RRbf * Pbo * RRbo
        # Store total age population sizes
        AgePop = []
        for ageInd in range(len(self.ages)):
            AgePop.append(0.)
            for stuntingCat in self.stuntingList:
                for wastingCat in self.wastingList:
                    for breastfeedingCat in self.breastfeedingList:
                        AgePop[ageInd] += self.model.listOfAgeCompartments[ageInd].dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize
        # Calculated total mortality by age (corrected for units)
        MortalityCorrected = {}
        # note that mortality rate have currently been pre-divided by 1000
        # Newborns
        age = self.ages[0]
        Mnew = self.data.totalMortality[age]
        m1 = Mnew
        MortalityCorrected[age] = m1
        # 1-5 months
        age = self.ages[1]
        Minfant = self.data.totalMortality[age]
        #Frac2 = (1.-Minfant)/(1.-m1)
        #m2 = 1. - pow(Frac2,1./11.)
        m2 = (Minfant - Mnew)*AgePop[0]/(AgePop[1]+AgePop[2])
        MortalityCorrected[age] = m2
        # 6-12 months
        age = self.ages[2]
        m3 = m2
        MortalityCorrected[age] = m3
        # 12-24 months
        age = self.ages[3]
        Mu5 = self.data.totalMortality[age]
        #Frac4 = (1.-Mu5)/(1.-m1)/(Frac2)
        #m4 = 1. - pow(Frac4,1./48.)
        m4 = (Mu5 - Minfant)*AgePop[0]/(AgePop[3]+AgePop[4])
        MortalityCorrected[age] = m4
        # 24-60 months
        age = self.ages[4]
        m5 = m4
        MortalityCorrected[age] = m5
        # Calculate LHS for each age and cause of death then solve for X
        Xdictionary = {} 
        for age in self.ages:
            Xdictionary[age] = {}
            for cause in self.data.causesOfDeath:
                LHS_age_cause = MortalityCorrected[age] * self.data.causeOfDeathDist[age][cause]
                Xdictionary[age][cause] = LHS_age_cause / RHS[age][cause]
        self.underlyingMortalities = Xdictionary
        


    # Calculate probability of stunting in this age group given stunting in previous age-group
    def getProbStuntingProgression(self):
        from numpy import sqrt 
        numAgeGroups = len(self.ages)
        self.probStuntedIfPrevStunted["notstunted"] = {}
        self.probStuntedIfPrevStunted["yesstunted"] = {}
        eps = 1.e-5
        for ageInd in range(1, numAgeGroups):
            ageName = self.ages[ageInd]
            thisAge = self.model.listOfAgeCompartments[ageInd]
            younger = self.model.listOfAgeCompartments[ageInd-1]
            OddsRatio = self.data.ORstuntingProgression[ageName]
            numStuntedThisAge = 0.
            numStuntedYounger = 0.
            numNotStuntedThisAge = 0.
            numNotStuntedYounger = 0.
            for wastingCat in self.wastingList:
                for breastfeedingCat in self.breastfeedingList:
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
            b = (OddsRatio-1.)*fracStuntedThisAge - OddsRatio*fracStuntedYounger - (1.-fracStuntedYounger)
            c = fracStuntedThisAge
            det = sqrt(b**2 - 4.*a*c)
            soln1 = (-b + det)/(2.*a)
            soln2 = (-b - det)/(2.*a)
            # not sure what to do if both or neither are solutions
            if(soln1>0.)and(soln1<1.): p0 = soln1
            if(soln2>0.)and(soln2<1.): p0 = soln2
            self.probStuntedIfPrevStunted["notstunted"][ageName] = p0
            self.probStuntedIfPrevStunted["yesstunted"][ageName] = p0*OddsRatio/(1.-p0+OddsRatio*p0)
        



    # Calculate probability of stunting in current age-group given diarrhea incidence
    def getFracStuntingGivenDiarrhea(self):
        from numpy import sqrt 
        from math import pow
        numAgeGroups = len(self.model.listOfAgeCompartments)
        self.fracStuntedIfDiarrhea["nodia"] = {}
        self.fracStuntedIfDiarrhea["dia"] = {}
        for ageInd in range(0,numAgeGroups):
            ageName = self.ages[ageInd]
            thisAge = self.model.listOfAgeCompartments[ageInd]
            sum = 0.
            for breastfeedingCat in self.breastfeedingList:
                RDa = self.data.RRdiarrhea[ageName][breastfeedingCat]
                pab  = self.data.breastfeedingDistribution[ageName][breastfeedingCat]
                sum += RDa * pab
            Za = self.data.incidenceDiarrhea[ageName] / sum
            # population odds ratio = AO (see Eqn 3.9)
            RRnot = self.data.RRdiarrhea[ageName]["none"]
            AO = pow(self.data.ORdiarrhea[ageName],RRnot*Za) #/thisAge.agingRate)
            # instead have fraction of children of age a who are experiencing diarrhea
            fracDiarrhea = 0.
            for breastfeedingCat in self.breastfeedingList:
                RDa = self.data.RRdiarrhea[ageName][breastfeedingCat]
                beta = 1. - (RRnot-RDa)/(RRnot) #(RRnot*Za-RDa*Za)/(RRnot*Za)
                pab  = self.data.breastfeedingDistribution[ageName][breastfeedingCat]
                fracDiarrhea += beta * pab
            # fraction stunted
            fracStuntedThisAge = thisAge.getStuntedFraction()
            # solve quadratic equation ax**2 + bx + c = 0
            a = (1.-fracDiarrhea) * (1.-AO)
            b = (AO-1.)*fracStuntedThisAge - AO*fracDiarrhea - (1.-fracDiarrhea)
            c = fracStuntedThisAge
            det = sqrt(b**2 - 4.*a*c)
            soln1 = (-b + det)/(2.*a)
            soln2 = (-b - det)/(2.*a)
            # not sure what to do if both or neither are solutions
            if(soln1>0.)and(soln1<1.): p0 = soln1
            if(soln2>0.)and(soln2<1.): p0 = soln2
            self.fracStuntedIfDiarrhea["nodia"][ageName] = p0
            self.fracStuntedIfDiarrhea["dia"][ageName]   = p0*AO/(1.-p0+AO*p0)
            #print "Test: F*p1 * (1-F)*p2 = %g = %g?"%((fracDiarrhea*p0 + (1.-fracDiarrhea)*p0*AO/(1.-p0+AO*p0)), fracStuntedThisAge)





    # Calculate probability of stunting in current age-group given coverage by zinc
    def getFracStuntingGivenZinc(self):
        from numpy import sqrt 
        numAgeGroups = len(self.model.listOfAgeCompartments)
        self.fracStuntedIfZinc["nozinc"] = {}
        self.fracStuntedIfZinc["zinc"] = {}
        for ageInd in range(0,numAgeGroups):
            ageName = self.ages[ageInd]
            thisAge = self.model.listOfAgeCompartments[ageInd]
            OddsRatio = self.data.ORstuntingZinc[ageName]
            # instead have fraction of children of age a who have enough zinc
            fracZinc = self.data.interventionCoveragesCurrent["Zinc supplementation"]
            #fracZinc = 0.
            # fraction stunted
            fracStuntedThisAge = thisAge.getStuntedFraction()
            # solve quadratic equation ax**2 + bx + c = 0
            a = (1.-fracZinc) * (1.-OddsRatio)
            b = (OddsRatio-1)*fracStuntedThisAge - OddsRatio*fracZinc - (1.-fracZinc)
            c = fracStuntedThisAge
            det = sqrt(b**2 - 4.*a*c)
            soln1 = (-b + det)/(2.*a)
            soln2 = (-b - det)/(2.*a)
            # not sure what to do if both or neither are solutions
            if(soln1>0.)and(soln1<1.): p0 = soln1
            if(soln2>0.)and(soln2<1.): p0 = soln2
            self.fracStuntedIfZinc["nozinc"][ageName] = p0
            self.fracStuntedIfZinc["zinc"][ageName]   = p0*OddsRatio/(1.-p0+OddsRatio*p0)
            #print "Test: F*p1 * (1-F)*p2 = %g = %g?"%((fracZinc*p0 + (1.-fracZinc)*p0*OddsRatio/(1.-p0+OddsRatio*p0)), fracStuntedThisAge)



    # Calculate probability of stunting in current age-group given coverage by intervention
    def getProbStuntedIfCoveredByIntervention(self):
        # input interventionList? oddsRatioList? currentCoverageList?
        from numpy import sqrt 
        numAgeGroups = len(self.model.listOfAgeCompartments)
        self.probStuntedIfCovered["nozinc"] = {}
        self.probStuntedIfCovered["zinc"] = {}
        for ageInd in range(0,numAgeGroups):
            ageName = self.ages[ageInd]
            thisAge = self.model.listOfAgeCompartments[ageInd]
            OddsRatio = self.data.ORstuntingZinc[ageName]
            # instead have fraction of children of age a who have enough zinc
            #fracZinc = self.data.InterventionCoveragesCurrent["Zinc supplementation"]
            fracZinc = 0.
            # fraction stunted
            fracStuntedThisAge = thisAge.getStuntedFraction()
            # solve quadratic equation ax**2 + bx + c = 0
            a = (1.-fracZinc) * (1.-OddsRatio)
            b = (OddsRatio-1)*fracStuntedThisAge - OddsRatio*fracZinc - (1.-fracZinc)
            c = fracStuntedThisAge
            det = sqrt(b**2 - 4.*a*c)
            soln1 = (-b + det)/(2.*a)
            soln2 = (-b - det)/(2.*a)
            # not sure what to do if both or neither are solutions
            if(soln1>0.)and(soln1<1.): p0 = soln1
            if(soln2>0.)and(soln2<1.): p0 = soln2
            self.probStuntedIfCovered["nozinc"][ageName] = p0
            self.probStuntedIfCovered["zinc"][ageName]   = p0*OddsRatio/(1.-p0+OddsRatio*p0)
            #print "Test: F*p1 * (1-F)*p2 = %g = %g?"%((fracZinc*p0 + (1.-fracZinc)*p0*OddsRatio/(1.-p0+OddsRatio*p0)), fracStuntedThisAge)




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
        for wastingCat in self.wastingList:
            for breastfeedingCat in self.breastfeedingList:
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
    def evalQuartic(self, p0):
        from math import pow
        A,B,C,D,E = self.birthStuntingQuarticCoefficients
        return A*pow(p0,4) + B*pow(p0,3) + C*pow(p0,2) + D*p0 + E




    # SOLVE QUARTIC
    # p0 = Probability of Stunting at birth if Birth outcome = Term AGA
    def getProbStuntingAtBirthForBaselineBirthOutcome(self):
        from numpy import sqrt 
        tolerance = 0.00001
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
        while interval > tolerance:
            p0x = (p0max+p0min)/2.
            PositiveAtP0 = self.evalQuartic(p0x)>0
            if(PositiveAtP0 == PositiveAtMin):
                p0min = p0x
                PositiveAtMin = self.evalQuartic(p0min)>0
            else:
                p0max = p0x
                PositiveAtMax = self.evalQuartic(p0max)>0
            interval = p0max - p0min
        self.baselineProbStuntingAtBirth = p0x
        # Check 2nd deriv has no solutions between 0 and 1
        #print "Quartic   at %g = %g"%(p0x,self.evalQuartic(p0x))
        A,B,C,D,E = self.birthStuntingQuarticCoefficients
        AA = 4.*3.*A
        BB = 3.*2.*B
        CC = 2.*C
        det = sqrt(BB**2 - 4.*AA*CC)
        soln1 = (-BB + det)/(2.*AA)
        soln2 = (-BB - det)/(2.*AA)
        # check that no solution between 0 and 1
        #print "Two solutions are %g and %g"%(soln1,soln2)
        




    def getProbsStuntingAtBirth(self):
        p0 = self.baselineProbStuntingAtBirth
        self.probsStuntingAtBirth["Term AGA"] = p0
        for birthOutcome in ["Pre-term SGA","Pre-term AGA","Term SGA"]:
            OR = self.data.ORBirthOutcomeStunting[birthOutcome]
            self.probsStuntingAtBirth[birthOutcome] = p0*OR / (1.-p0+OR*p0)
            pi = self.probsStuntingAtBirth[birthOutcome]
            if(pi<0. or pi>1.):
                raise ValueError("probability of stunting at birth, at outcome %s, is out of range (%f)"%(birthOutcome, pi))
            
            
