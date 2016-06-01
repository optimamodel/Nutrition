# -*- coding: utf-8 -*-
"""
Created on Mon Feb 29 11:35:02 2016

@author: ruth
"""
from __future__ import division
from copy import deepcopy as dcp

class Constants:
    def __init__(self, data, model, keyList):
        self.data = dcp(data)
        self.model = dcp(model)
        self.ages,self.birthOutcomes,self.wastingList,self.stuntingList,self.breastfeedingList = keyList
        
        self.underlyingMortalities = {}
        self.probStuntedIfPrevStunted = {}
        self.fracStuntedIfDiarrhea = {}
        self.probStuntedIfCovered = {}
        self.probAppropriatelyBreastfedIfCovered = {}
        self.probsStuntingComplementaryFeeding = {}
        self.probsStuntingAtBirth = {}
        
        self.initialStuntingTrend = -0. # percentage decrease in stunting prevalence per year
        self.initialStuntingTrend = self.initialStuntingTrend / 100. * self.model.timestep # fractional decrease in stunting prevalence per timestep
        self.FractionFoodSecure = 0.5 # eventually this will come from data somehow
        self.stuntingUpdateAfterInterventions = {}
        for age in self.ages:
            self.stuntingUpdateAfterInterventions[age] = 1.

        self.getUnderlyingMortalities()
        self.getProbStuntingProgression()
        self.getProbsStuntingAtBirth()


    def getUnderlyingMortalities(self):
        #Equation is:  LHS = RHS * X
        #we are solving for X
        # Calculate RHS for each age and cause
        RHS = {}
        for age in self.ages:
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
        for ageInd in range(1, numAgeGroups):
            ageName = self.ages[ageInd]
            thisAge = self.model.listOfAgeCompartments[ageInd]
            younger = self.model.listOfAgeCompartments[ageInd-1]
            OddsRatio = self.data.ORstuntingProgression[ageName]
            fracStuntedThisAge = thisAge.getStuntedFraction() + self.initialStuntingTrend
            fracStuntedYounger = younger.getStuntedFraction()
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
            test1 = fracStuntedYounger*self.probStuntedIfPrevStunted["yesstunted"][ageName] + (1.-fracStuntedYounger)*self.probStuntedIfPrevStunted["notstunted"][ageName]
            #print "Test: F*p1 * (1-F)*p2 = %g = %g?"%(test1, fracStuntedThisAge)
        

    def getFracStuntedIfDiarrhea(self, currentIncidences, breastfeedingDistribution, stuntingDistribution):
        incidence = {}
        for ageName in self.ages:
            incidence[ageName] = currentIncidences[ageName]['Diarrhea']
        Z0 = self.getZa(incidence, breastfeedingDistribution)
        Zt = Z0 #this is true for the initialisation
        beta = self.getBetaGivenZ0AndZt(Z0, Zt)
        AO = self.getAOGivenZa(Zt)
        from numpy import sqrt    
        eps = 1.e-5
        numAgeGroups = len(self.model.listOfAgeCompartments)        
        self.fracStuntedIfDiarrhea["nodia"] = {}
        self.fracStuntedIfDiarrhea["dia"] = {}
        for ageInd in range(0, numAgeGroups):
            ageName = self.ages[ageInd]
            #get fraction of people with diarrhea
            fracDiarrhea = 0.
            for breastfeedingCat in self.breastfeedingList:
                fracDiarrhea += beta[ageName][breastfeedingCat] * breastfeedingDistribution[ageName][breastfeedingCat]
            # get fraction stunted
            fracStuntedThisAge = stuntingDistribution[ageName]['high'] + stuntingDistribution[ageName]['moderate'] # + self.initialStuntingTrend
            # solve quadratic equation ax**2 + bx + c = 0
            a = (1. - fracDiarrhea) * (1. - AO[ageName])
            b = (AO[ageName] - 1.) * fracStuntedThisAge - AO[ageName] * fracDiarrhea - (1. - fracDiarrhea)
            c = fracStuntedThisAge
            det = sqrt(b**2 - 4.*a*c)
            if(abs(a)<eps):
                p0 = -c/b
            else:
                soln1 = (-b + det)/(2.*a)
                soln2 = (-b - det)/(2.*a)
                # not sure what to do if both or neither are solutions
                if(soln1>0.)and(soln1<1.): p0 = soln1
                if(soln2>0.)and(soln2<1.): p0 = soln2
            self.fracStuntedIfDiarrhea["nodia"][ageName] = p0
            self.fracStuntedIfDiarrhea["dia"][ageName]   = p0 * AO[ageName] / (1. - p0 + AO[ageName] * p0)
            


    def getDiarrheaRiskSum(self, ageName, breastfeedingDistribution):
        bfDistribution = dcp(breastfeedingDistribution)
        riskSum = 0.
        for breastfeedingCat in self.breastfeedingList:
            RDa = self.data.RRdiarrhea[ageName][breastfeedingCat]
            pab  = bfDistribution[ageName][breastfeedingCat]
            riskSum += RDa * pab
        return riskSum


    def getZa(self, incidence, breastfeedingDistribution):
        bfDistribution = dcp(breastfeedingDistribution)
        Za = {}
        for ageName in self.ages:
            riskSum = self.getDiarrheaRiskSum(ageName, bfDistribution)
            Za[ageName] = incidence[ageName] / riskSum
        return Za     


    def getAOGivenZa(self, Za):
        from math import pow
        AO = {}
        for ageName in self.ages:
            RRnot = self.data.RRdiarrhea[ageName]["none"]
            AO[ageName] = pow(self.data.ORstuntingCondition[ageName]['Diarrhea'], RRnot * Za[ageName])
        return AO    
        
        
    def getBetaGivenZ0AndZt(self, Z0, Zt):
        beta = {}
        for ageName in self.ages:
            beta[ageName] = {}
            RRnot = self.data.RRdiarrhea[ageName]["none"]
            for breastfeedingCat in self.breastfeedingList:
                RDa = self.data.RRdiarrhea[ageName][breastfeedingCat]
                beta[ageName][breastfeedingCat] = 1. - ((RRnot * Z0[ageName] - RDa * Zt[ageName]) / RRnot * Z0[ageName])   
        return beta        



    # Calculate probability of stunting in current age-group given coverage by intervention
    def getProbStuntedIfCoveredByIntervention(self, interventionCoverages, stuntingDistribution):
        from numpy import sqrt 
        eps = 1.e-5
        numAgeGroups = len(self.model.listOfAgeCompartments)
        for intervention in self.data.interventionList:
            self.probStuntedIfCovered[intervention] = {}
            self.probStuntedIfCovered[intervention]["not covered"] = {}
            self.probStuntedIfCovered[intervention]["covered"]     = {}
            for ageInd in range(numAgeGroups):
                ageName = self.ages[ageInd]
                OddsRatio = self.data.ORstuntingIntervention[ageName][intervention]
                fracCovered = interventionCoverages[intervention]
                fracStuntedThisAge = stuntingDistribution[ageName]['high'] + stuntingDistribution[ageName]['moderate']
                # solve quadratic equation ax**2 + bx + c = 0
                a = (1.-fracCovered) * (1.-OddsRatio)
                b = (OddsRatio-1)*fracStuntedThisAge - OddsRatio*fracCovered - (1.-fracCovered)
                c = fracStuntedThisAge
                det = sqrt(b**2 - 4.*a*c)
                if(abs(a)<eps):
                    p0 = -c/b
                else:
                    soln1 = (-b + det)/(2.*a)
                    soln2 = (-b - det)/(2.*a)
                    if(soln1>0.)and(soln1<1.): p0 = soln1
                    if(soln2>0.)and(soln2<1.): p0 = soln2
                self.probStuntedIfCovered[intervention]["not covered"][ageName] = p0
                self.probStuntedIfCovered[intervention]["covered"][ageName]     = p0*OddsRatio/(1.-p0+OddsRatio*p0)



    # Calculate probability of stunting in current age-group given coverage by intervention
    def getProbAppropriatelyBreastfedIfCoveredByIntervention(self, interventionCoverages, breastfeedingDistribution):
        from numpy import sqrt 
        eps = 1.e-5
        numAgeGroups = len(self.model.listOfAgeCompartments)
        for intervention in self.data.interventionList:
            self.probAppropriatelyBreastfedIfCovered[intervention] = {}
            self.probAppropriatelyBreastfedIfCovered[intervention]["not covered"] = {}
            self.probAppropriatelyBreastfedIfCovered[intervention]["covered"]     = {}
            for ageInd in range(numAgeGroups):
                ageName = self.ages[ageInd]
                OddsRatio = self.data.ORappropriatebfIntervention[ageName][intervention]
                fracCovered = interventionCoverages[intervention]
                appropriatePractice = self.data.ageAppropriateBreastfeeding[ageName]
                fracAppropriatelyBreastfedThisAge = breastfeedingDistribution[ageName][appropriatePractice]
                # solve quadratic equation ax**2 + bx + c = 0
                a = (1.-fracCovered) * (1.-OddsRatio)
                b = (OddsRatio-1)*fracAppropriatelyBreastfedThisAge - OddsRatio*fracCovered - (1.-fracCovered)
                c = fracAppropriatelyBreastfedThisAge
                det = sqrt(b**2 - 4.*a*c)
                if(abs(a)<eps):
                    p0 = -c/b
                else:
                    soln1 = (-b + det)/(2.*a)
                    soln2 = (-b - det)/(2.*a)
                    if(soln1>0.)and(soln1<1.): p0 = soln1
                    if(soln2>0.)and(soln2<1.): p0 = soln2
                self.probAppropriatelyBreastfedIfCovered[intervention]["not covered"][ageName] = p0
                self.probAppropriatelyBreastfedIfCovered[intervention]["covered"][ageName]     = p0*OddsRatio/(1.-p0+OddsRatio*p0)
                #print "Test: F*p1 * (1-F)*p2 = %g = %g?"%((1.-fracCovered)*p0 + fracCovered*p0*OddsRatio/(1.-p0+OddsRatio*p0), fracAppropriatelyBreastfedThisAge)


    def getBirthStuntingQuarticCoefficients(self):
        OR = [1.]*4
        OR[0] = 1.
        OR[1] = self.data.ORstuntingBirthOutcome["Term SGA"]
        OR[2] = self.data.ORstuntingBirthOutcome["Pre-term AGA"]
        OR[3] = self.data.ORstuntingBirthOutcome["Pre-term SGA"]
        FracBO = [0.]*4
        FracBO[1] = self.data.birthOutcomeDist["Term SGA"]    
        FracBO[2] = self.data.birthOutcomeDist["Pre-term AGA"]
        FracBO[3] = self.data.birthOutcomeDist["Pre-term SGA"]
        FracBO[0] = 1. - sum(FracBO[1:3])
        FracStunted = self.model.listOfAgeCompartments[0].getStuntedFraction() + self.initialStuntingTrend
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
        return [A,B,C,D,E]
        
        
    def getComplementaryFeedingQuarticCoefficients(self, stuntingDistribution, interventionCoverages):
        coEffs = {}
        for ageGroup in range(len(self.ages)): 
            age = self.ages[ageGroup]
            OR = [1.]*4
            OR[0] = 1.
            OR[1] = self.data.ORstuntingComplementaryFeeding[age]["Complementary feeding (food secure without promotion)"]
            OR[2] = self.data.ORstuntingComplementaryFeeding[age]["Complementary feeding (food insecure with promotion and supplementation)"]
            OR[3] = self.data.ORstuntingComplementaryFeeding[age]["Complementary feeding (food insecure with neither promotion nor supplementation)"]
            FracSecure = self.FractionFoodSecure
            FracCovered = interventionCoverages['Complementary feeding']            
            Frac = [0.]*4
            Frac[0] = FracSecure * FracCovered    
            Frac[1] = FracSecure * (1 - FracCovered)
            Frac[2] = (1 - FracSecure) * FracCovered
            Frac[3] = (1 - FracSecure) * (1 - FracCovered)
            FracStunted = stuntingDistribution[age]['high'] + stuntingDistribution[age]['moderate'] # + self.initialStuntingTrend
            # [i] will refer to the three non-baseline birth outcomes
            A = Frac[0]*(OR[1]-1.)*(OR[2]-1.)*(OR[3]-1.)
            B = (OR[1]-1.)*(OR[2]-1.)*(OR[3]-1.) * ( \
                sum( Frac[0] / (OR[i]-1.)         for i in (1,2,3)) + \
                sum( OR[i] * Frac[i] / (OR[i]-1.) for i in (1,2,3)) - \
                FracStunted )
            C = sum( Frac[0] * (OR[i]-1.)         for i in (1,2,3)) + \
                sum( OR[i] * Frac[i] * ((OR[1]-1.)+(OR[2]-1.)+(OR[3]-1.)-(OR[i]-1.)) for i in (1,2,3) ) - \
                sum( FracStunted*(OR[1]-1.)*(OR[2]-1.)*(OR[3]-1.)/(OR[i]-1.) for i in (1,2,3))
            D = Frac[0] + \
                sum( OR[i] * Frac[i] for i in (1,2,3)) - \
                sum( FracStunted * (OR[i]-1.) for i in (1,2,3))
            E = -FracStunted
            coEffs[age] = [A,B,C,D,E]
        return coEffs      



    # internal function to evaluate the quartic function for probability of stunting at birth at baseline birth outcome
    def evalQuartic(self, p0, coEffs):
        from math import pow
        A,B,C,D,E = coEffs
        return A*pow(p0,4) + B*pow(p0,3) + C*pow(p0,2) + D*p0 + E




    # SOLVE QUARTIC
    # p0 = Probability of Stunting at birth if Birth outcome = Term AGA
    def getBaselineProbabilityViaQuartic(self, coEffs):
        from numpy import sqrt, isnan
        baselineProbability = 0        
        # if any CoEffs are nan then baseline prob is -E (initial % stunted)
        if isnan(coEffs).any():
            baselineProbability = -coEffs[4]
            return baselineProbability
        tolerance = 0.00001
        p0min = 0.
        p0max = 1.
        interval = p0max - p0min
        if self.evalQuartic(p0min, coEffs)==0:
            baselineProbability = p0min
            return baselineProbability
        if self.evalQuartic(p0max, coEffs)==0:
            baselineProbability = p0max
            return baselineProbability
        PositiveAtMin = self.evalQuartic(p0min, coEffs)>0
        PositiveAtMax = self.evalQuartic(p0max, coEffs)>0
        if(PositiveAtMin == PositiveAtMax): 
            raise ValueError("ERROR: Quartic function evaluated at 0 & 1 both on the same side")
        while interval > tolerance:
            p0x = (p0max+p0min)/2.
            PositiveAtP0 = self.evalQuartic(p0x, coEffs)>0
            if(PositiveAtP0 == PositiveAtMin):
                p0min = p0x
                PositiveAtMin = self.evalQuartic(p0min, coEffs)>0
            else:
                p0max = p0x
                PositiveAtMax = self.evalQuartic(p0max, coEffs)>0
            interval = p0max - p0min
        baselineProbability = p0x
        # Check 2nd deriv has no solutions between 0 and 1
        A,B,C,D,E = coEffs 
        AA = 4.*3.*A
        BB = 3.*2.*B
        CC = 2.*C
        det = sqrt(BB**2 - 4.*AA*CC)
        soln1 = (-BB + det)/(2.*AA)
        soln2 = (-BB - det)/(2.*AA)
        if((soln1>0.)and(soln1<1.)):
            print "Warning problem with solving Quartic, see soln1"
        if((soln2>0.)and(soln2<1.)):
            print "Warning problem with solving Quartic, see soln2"
        return baselineProbability
        
        
    def getBaselineProbabilityViaQuarticByAge(self, coEffs):
        #CoEffs are a dictionary of coefficients by age
        baselineProbability = {}        
        for age in self.ages:
            baselineProbability[age] = self.getBaselineProbabilityViaQuartic(coEffs[age])
        return baselineProbability    


    def getProbsStuntingAtBirth(self):
        coEffs = self.getBirthStuntingQuarticCoefficients()
        baselineProbStuntingAtBirth = self.getBaselineProbabilityViaQuartic(coEffs)        
        p0 = baselineProbStuntingAtBirth
        probsStuntingAtBirth = {}
        probsStuntingAtBirth["Term AGA"] = p0
        for birthOutcome in ["Pre-term SGA","Pre-term AGA","Term SGA"]:
            OR = self.data.ORstuntingBirthOutcome[birthOutcome]
            probsStuntingAtBirth[birthOutcome] = p0*OR / (1.-p0+OR*p0)
            pi = probsStuntingAtBirth[birthOutcome]
            if(pi<0. or pi>1.):
                raise ValueError("probability of stunting at birth, at outcome %s, is out of range (%f)"%(birthOutcome, pi))
        self.probsStuntingAtBirth = probsStuntingAtBirth        
                
    def getProbsStuntingComplementaryFeeding(self, stuntingDistribution, interventionCoverages):
        coEffs = self.getComplementaryFeedingQuarticCoefficients(stuntingDistribution, interventionCoverages)
        baselineProbStuntingComplementaryFeeding = self.getBaselineProbabilityViaQuarticByAge(coEffs)        
        probsStuntingComplementaryFeeding = {}        
        for age in self.ages: 
            probsStuntingComplementaryFeeding[age] = {}
            p0 = baselineProbStuntingComplementaryFeeding[age]
            probsStuntingComplementaryFeeding[age]["Complementary feeding (food secure with promotion)"] = p0
            for group in self.data.complementsList:
                OR = self.data.ORstuntingComplementaryFeeding[age][group]
                probsStuntingComplementaryFeeding[age][group] = p0*OR / (1.-p0+OR*p0)
                pi = probsStuntingComplementaryFeeding[age][group]
                if(pi<0. or pi>1.):
                    raise ValueError("probability of stunting complementary feeding, at outcome %s, age %s, is out of range (%f)"%(group, age, pi))            
        self.probsStuntingComplementaryFeeding = probsStuntingComplementaryFeeding    
            
