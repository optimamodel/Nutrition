# -*- coding: utf-8 -*-
"""
Created on Mon Feb 29 11:35:02 2016

@author: ruth
"""
from __future__ import division
from copy import deepcopy as dcp
import helper as helper

class Derived:
    def __init__(self, data, model, keyList):
        self.helper = helper.Helper()        
        self.data = dcp(data)
        self.initialModel = dcp(model)

        for key in keyList.keys():
            setattr(self, key, keyList[key])

        self.initialStuntingTrend = 0. # percentage decrease in stunting prevalence per year
        self.initialStuntingTrend = self.initialStuntingTrend / 100. * self.timestep # fractional decrease in stunting prevalence per timestep

        self.referenceMortality = {}
        self.probStuntedIfPrevStunted = {}
        self.fracStuntedIfDiarrhea = {}
        self.fracAnemicIfDiarrhea = {}
        self.fracWastedIfDiarrhea = {}
        self.probStuntedIfCovered = {}
        self.probCorrectlyBreastfedIfCovered = {}
        self.probStuntedComplementaryFeeding = {}
        self.probStuntedAtBirth = {}
        self.probWastedAtBirth = {}
        self.probAnemicIfCovered = {}
        self.probWastedIfCovered = {}

        self.stuntingUpdateAfterInterventions = {}
        self.wastingUpdateAfterInterventions = {}
        for ageName in self.ages:
            self.stuntingUpdateAfterInterventions[ageName] = 1.
            self.wastingUpdateAfterInterventions[ageName] = {}
            for wastingCat in self.wastedList:
                self.wastingUpdateAfterInterventions[ageName][wastingCat] = 1.

        self.setReferenceMortality()
        self.setProbStuntingProgression()
        self.setProbStuntedAtBirth()
        self.setProbWastedAtBirth()
        self.birthRate = 0.0
        self.pregnancyRate = 0.0
        self.fractionPregnancyAverted = 0.0
        self.baselineCoverageFP = 0.0
        self.setBirthPregnancyInfo()
        self.setBirthProbs()



    def setReferenceMortality(self):
        #Equation is:  LHS = RHS * X
        #we are solving for X
        # Calculate RHS for each age and cause
        RHS = {}
        for ageName in self.ages:
            RHS[ageName] = {}
            for cause in self.data.causesOfDeath:
                RHS[ageName][cause] = 0.
                for stuntingCat in self.stuntingList:
                    for wastingCat in self.wastingList:
                        for breastfeedingCat in self.breastfeedingList:
                            for anemiaStatus in self.anemiaList:
                                t1 = self.data.stuntingDistribution[ageName][stuntingCat]
                                t2 = self.data.wastingDistribution[ageName][wastingCat]
                                t3 = self.data.breastfeedingDistribution[ageName][breastfeedingCat]
                                t4 = self.data.anemiaDistribution[ageName][anemiaStatus]
                                t5 = self.data.RRdeathStunting[ageName][cause][stuntingCat]
                                t6 = self.data.RRdeathWasting[ageName][cause][wastingCat]
                                t7 = self.data.RRdeathBreastfeeding[ageName][cause][breastfeedingCat]
                                t8 = self.data.RRdeathAnemia[ageName][cause][anemiaStatus]
                                RHS[ageName][cause] += t1 * t2 * t3 * t4 * t5 * t6 * t7 * t8
        # RHS for newborns only
        ageName = "<1 month"
        for cause in self.data.causesOfDeath:
            RHS[ageName][cause] = 0.
            for breastfeedingCat in self.breastfeedingList:
                Pbf = self.data.breastfeedingDistribution[ageName][breastfeedingCat]
                RRbf = self.data.RRdeathBreastfeeding[ageName][cause][breastfeedingCat]
                for birthoutcome in self.birthOutcomes:
                    Pbo = self.data.birthOutcomeDist[birthoutcome]
                    RRbo = self.data.RRdeathByBirthOutcome[cause][birthoutcome]
                    for anemiaStatus in self.anemiaList:
                        Pan = self.data.anemiaDistribution[ageName][anemiaStatus]
                        RRan = self.data.RRdeathAnemia[ageName][cause][anemiaStatus]
                        RHS[ageName][cause] += Pbf * RRbf * Pbo * RRbo * Pan * RRan
        # Store total age population sizes
        AgePop = []
        for iAge in range(len(self.ages)):
            AgePop.append(self.initialModel.listOfAgeCompartments[iAge].getTotalPopulation())
        # Calculated total mortality by age (corrected for units)
        MortalityCorrected = {}
        LiveBirths = self.data.demographics["number of live births"]
        Mnew = self.data.rawMortality["neonatal"]
        Minfant = self.data.rawMortality["infant"]
        Mu5 = self.data.rawMortality["under 5"]
        # Newborns
        ageName = self.ages[0]
        m0 = Mnew*LiveBirths/1000./AgePop[0]
        MortalityCorrected[ageName] = m0
        # 1-5 months
        ageName = self.ages[1]
        m1 = (Minfant - Mnew)*LiveBirths/1000.*5./11./AgePop[1]
        MortalityCorrected[ageName] = m1
        # 6-12 months
        ageName = self.ages[2]
        m2 = (Minfant - Mnew)*LiveBirths/1000.*6./11./AgePop[2]
        MortalityCorrected[ageName] = m2
        # 12-24 months
        ageName = self.ages[3]
        m3 = (Mu5 - Minfant)*LiveBirths/1000.*1./4./AgePop[3]
        MortalityCorrected[ageName] = m3
        # 24-60 months
        ageName = self.ages[4]
        m4 = (Mu5 - Minfant)*LiveBirths/1000.*3./4./AgePop[4]
        MortalityCorrected[ageName] = m4
        # Calculate LHS for each age and cause of death then solve for X
        Xdictionary = {} 
        for ageName in self.ages:
            Xdictionary[ageName] = {}
            for cause in self.data.causesOfDeath:
                LHS_age_cause = MortalityCorrected[ageName] * self.data.causeOfDeathDist[ageName][cause]
                Xdictionary[ageName][cause] = LHS_age_cause / RHS[ageName][cause]
        self.referenceMortality = Xdictionary
        # now call function to set pregnant women reference mortality
        self.setReferencePregnantWomenMortality()
        
        
    def setReferencePregnantWomenMortality(self):
        #Equation is:  LHS = RHS * X
        #we are solving for X
        # Calculate RHS for each age and cause
        RHS = {}
        for ageName in self.pregnantWomenAges:
            RHS[ageName] = {}
            for cause in self.data.causesOfDeath:
                RHS[ageName][cause] = 0.
                for anemiaStatus in self.anemiaList:
                    t1 = self.data.anemiaDistribution[ageName][anemiaStatus]
                    t2 = self.data.RRdeathAnemia[ageName][cause][anemiaStatus]
                    RHS[ageName][cause] += t1 * t2
        # get age populations
        agePop = [compartment.getTotalPopulation() for compartment in self.initialModel.listOfPregnantWomenAgeCompartments]
        # Correct raw mortality for units (per 1000 live births)
        liveBirths = self.data.demographics['number of live births']
        # The following assumes we only have a single mortality rate for PW
        mortalityRate = self.data.rawMortality['maternal']
        mortalityCorrected = {}
        for index in range(len(self.pregnantWomenAges)):
            ageName = self.pregnantWomenAges[index]
            if index == 0:
                mortalityCorrected[ageName] = (mortalityRate * liveBirths / 1000.) * (4. / 34.) / agePop[index]
            else:
                mortalityCorrected[ageName] = (mortalityRate * liveBirths / 1000.) * (9. / 34.) / agePop[index]

        # Calculate LHS for each age and cause of death then solve for X
        Xdictionary = {}
        for ageName in self.pregnantWomenAges:
            Xdictionary[ageName] = {}
            for cause in self.data.causesOfDeath:
                LHS_age_cause = mortalityCorrected[ageName] * self.data.causeOfDeathDist[ageName][cause]
                Xdictionary[ageName][cause] = LHS_age_cause / RHS[ageName][cause]
        # add pregnant women reference mortality to dictionary
        self.referenceMortality.update(Xdictionary)
        
    def setBirthPregnancyInfo(self):
        for intervention in self.data.effectivenessFP:
            self.fractionPregnancyAverted += self.data.effectivenessFP[intervention] * self.data.distributionFP[intervention] * self.data.coverage['Family Planning']
            self.baselineCoverageFP = dcp(self.data.coverage['Family Planning'])
        numPregnant = dcp(self.data.demographics['number of pregnant women'])
        numWRA = dcp(self.initialModel.getTotalPopWRA())
        # num pregnant = rate * num WRA * (1 - fractionPregnancyAverted)
        rate = numPregnant/numWRA/(1.- self.fractionPregnancyAverted)
        # reduce rate by % difference between births and pregnancies to get birth rate
        projectedBirths = dcp(self.data.projectedBirths.values()) 
        projectedPWpop = dcp(self.data.projectedPWpop.values())
        percentDiff = [ai/bi for ai,bi in zip(projectedBirths, projectedPWpop)]
        averagePercentDiff = sum(percentDiff) / float(len(percentDiff))
        self.pregnancyRate = rate        
        self.birthRate = averagePercentDiff * rate  
        
        
    def updateFractionPregnaciesAverted(self, newCoverage, unMetNeedFP):
        maxCovFP = self.baselineCoverageFP + unMetNeedFP
        if newCoverage['Family Planning'] > maxCovFP:
            newCoverage['Family Planning'] = maxCovFP            
        # now calculate the new fraction of averted pregnancies 
        newFractionAverted = 0.            
        for intervention in self.data.effectivenessFP:
            newFractionAverted += self.data.effectivenessFP[intervention] * self.data.distributionFP[intervention] * newCoverage['Family Planning']                
        self.fractionPregnancyAverted = newFractionAverted
        
    def setBirthProbs(self):
        birthProb = {}
        for status in self.data.birthOutcomeDist:
            fracThisStatus = self.data.birthOutcomeDist[status]
            thisSum = 0.
            for ageOrder in self.data.ageOrderDist:
                fracAO = self.data.ageOrderDist[ageOrder]
                RRAO = self.data.RRageOrder[ageOrder]
                for interval in self.data.intervalDist:
                    fracInterval = self.data.intervalDist[interval]
                    RRinterval = self.data.RRinterval
                    thisSum += fracAO * RRAO * fracInterval * RRinterval
            birthProb[status] = fracThisStatus/thisSum        

    # Calculate probability of stunting in this age group given stunting in previous age-group
    def setProbStuntingProgression(self):
        numAgeGroups = len(self.ages)
        self.probStuntedIfPrevStunted["notstunted"] = {}
        self.probStuntedIfPrevStunted["yesstunted"] = {}
        for iAge in range(1, numAgeGroups):
            ageName = self.ages[iAge]
            thisAge = self.initialModel.listOfAgeCompartments[iAge]
            younger = self.initialModel.listOfAgeCompartments[iAge-1]
            OddsRatio = self.data.ORstuntingProgression[ageName]
            fracStuntedThisAge = thisAge.getStuntedFraction() #* self.initialStuntingTrend   
            fracStuntedYounger = younger.getStuntedFraction()
            pn, pc = self.solveQuadratic(OddsRatio, fracStuntedYounger, fracStuntedThisAge)
            self.probStuntedIfPrevStunted["notstunted"][ageName] = pn
            self.probStuntedIfPrevStunted["yesstunted"][ageName] = pc
        

    def setProbStuntedIfDiarrhea(self, currentIncidences, breastfeedingDistribution, stuntingDistribution):
        incidence = {}
        for ageName in self.ages:
            incidence[ageName] = currentIncidences[ageName]['Diarrhea']
        Z0 = self.getZa(incidence, breastfeedingDistribution)
        Zt = Z0 #this is true for the initialisation
        beta = self.getFracDiarrhea(Z0, Zt)
        risk = 'stunting'
        AO = self.getAverageOR(Zt, risk)
        numAgeGroups = len(self.ages)
        self.fracStuntedIfDiarrhea["nodia"] = {}
        self.fracStuntedIfDiarrhea["dia"] = {}
        for iAge in range(0, numAgeGroups):
            ageName = self.ages[iAge]
            #get fraction of people with diarrhea
            fracDiarrhea = 0.
            for breastfeedingCat in self.breastfeedingList:
                fracDiarrhea += beta[ageName][breastfeedingCat] * breastfeedingDistribution[ageName][breastfeedingCat]
            # get fraction stunted
            fracStuntedThisAge = self.helper.sumStuntedComponents(stuntingDistribution[ageName])
            pn, pc = self.solveQuadratic(AO[ageName], fracDiarrhea, fracStuntedThisAge)
            self.fracStuntedIfDiarrhea["nodia"][ageName] = pn
            self.fracStuntedIfDiarrhea["dia"][ageName]   = pc
            
    def setProbAnemicIfDiarrhea(self, currentIncidences, breastfeedingDistribution, anemiaDistribution):
        incidence = {}
        for ageName in self.ages:
            incidence[ageName] = currentIncidences[ageName]['Diarrhea']
        Z0 = self.getZa(incidence, breastfeedingDistribution)
        Zt = Z0 #this is true for the initialisation
        beta = self.getFracDiarrhea(Z0, Zt)
        risk = 'anemia'
        Yt = {}
        for ageName in self.ages:
            Yt[ageName] = Zt[ageName] * self.data.fracSevereDia
        AO = self.getAverageOR(Yt, risk)
        numAgeGroups = len(self.ages)
        self.fracAnemicIfDiarrhea["nodia"] = {}
        self.fracAnemicIfDiarrhea["dia"] = {}
        for iAge in range(0, numAgeGroups):
            ageName = self.ages[iAge]
            #get fraction of people with diarrhea
            fracDiarrhea = 0.
            for breastfeedingCat in self.breastfeedingList:
                fracDiarrhea += beta[ageName][breastfeedingCat] * breastfeedingDistribution[ageName][breastfeedingCat]
            # get fraction anemic 
            fracAnemicThisAge = anemiaDistribution[ageName]['anemic']
            pn, pc = self.solveQuadratic(AO[ageName], fracDiarrhea, fracAnemicThisAge)
            self.fracAnemicIfDiarrhea["nodia"][ageName] = pn
            self.fracAnemicIfDiarrhea["dia"][ageName]   = pc

    def setProbWastedIfDiarrhea(self, currentIncidences, breastfeedingDistribution, wastingDistribution):
        incidence = {}
        for ageName in self.ages:
            incidence[ageName] = currentIncidences[ageName]['Diarrhea']
        Z0 = self.getZa(incidence, breastfeedingDistribution)
        Zt = Z0 # true for initialisation
        beta = self.getFracDiarrhea(Z0, Zt)
        for wastingCat in self.wastedList:
            AO = self.getAverageOR(Zt, wastingCat)
            numAgeGroups = len(self.ages)
            self.fracWastedIfDiarrhea[wastingCat] = {}
            self.fracWastedIfDiarrhea[wastingCat]["nodia"] = {}
            self.fracWastedIfDiarrhea[wastingCat]["dia"] = {}
            for iAge in range(0, numAgeGroups):
                ageName = self.ages[iAge]
                fracDiarrhea = 0.
                for breastfeedingCat in self.breastfeedingList:
                    fracDiarrhea += beta[ageName][breastfeedingCat] * breastfeedingDistribution[ageName][breastfeedingCat]
                # fraction wasted
                fracThisCatThisAge = wastingDistribution[ageName][wastingCat]
                pn, pc = self.solveQuadratic(AO[ageName], fracDiarrhea, fracThisCatThisAge)
                self.fracWastedIfDiarrhea[wastingCat]["nodia"][ageName] = pn
                self.fracWastedIfDiarrhea[wastingCat]["dia"][ageName]   = pc

    def updateDiarrheaProbsNewZa(self, Zt):
        AOStunting = self.getAverageOR(Zt, 'stunting')
        AOwasting = {}
        for wastingCat in self.wastedList:
            AOwasting[wastingCat] = self.getAverageOR(Zt, wastingCat)
        Yt = {}
        for ageName in self.ages:
            Yt[ageName] = Zt[ageName] * self.data.fracSevereDia
        AOAnemia = self.getAverageOR(Yt, 'anemia')
        numAgeGroups = len(self.ages)
        for iAge in range(numAgeGroups):
            ageName = self.ages[iAge]
            # stunting
            AO = AOStunting
            Omega0  = self.fracStuntedIfDiarrhea["nodia"][ageName]
            self.fracStuntedIfDiarrhea["dia"][ageName] = Omega0 * AO[ageName] / (1. - Omega0 + AO[ageName]*Omega0)
            # wasting
            for wastingCat in self.wastedList:
                AO = AOwasting[wastingCat]
                Omega0 = self.fracWastedIfDiarrhea[wastingCat]["nodia"][ageName]
                self.fracWastedIfDiarrhea[wastingCat]["dia"][ageName] = Omega0 * AO[ageName] / (1. - Omega0 + AO[ageName]*Omega0)
            # anemia
            AO = AOAnemia
            Omega0  = self.fracAnemicIfDiarrhea["nodia"][ageName]
            self.fracAnemicIfDiarrhea["dia"][ageName] = Omega0 * AO[ageName] / (1. - Omega0 + AO[ageName]*Omega0)


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


    def getAverageOR(self, Za, risk):
        from math import pow
        AO = {}
        numAgeGroups = len(self.ages)
        for i in range(numAgeGroups):
            ageName = self.ages[i]
            RRnot = self.data.RRdiarrhea[ageName]["none"]
            if risk == 'stunting':
                OR = self.data.ORstuntingCondition[ageName]['Diarrhea']
            elif risk == 'anemia':
                OR = self.data.ORanemiaCondition[ageName]['Diarrhea']
            elif risk == 'MAM' or risk == 'SAM':
                OR = self.data.ORwastingCondition[risk][ageName]['Diarrhea']
            else:
                print 'risk factor is invalid'
            AO[ageName] = pow(OR, RRnot * Za[ageName] * self.ageGroupSpans[i])
        return AO   
        
        
    def getFracDiarrhea(self, Z0, Zt):
        beta = {}
        for ageName in self.ages:
            beta[ageName] = {}
            RRnot = self.data.RRdiarrhea[ageName]["none"]
            for breastfeedingCat in self.breastfeedingList:
                RDa = self.data.RRdiarrhea[ageName][breastfeedingCat]
                beta[ageName][breastfeedingCat] = 1. - (RRnot * Z0[ageName] - RDa * Zt[ageName]) / (RRnot * Z0[ageName]) 
                # RDa * Zt[ageName] / (RRnot * Z0[ageName])
        return beta        


    def getFracDiarrheaFixedZ(self):
        beta = {}
        for ageName in self.ages:
            beta[ageName] = {}
            RRnot = self.data.RRdiarrhea[ageName]["none"]
            for breastfeedingCat in self.breastfeedingList:
                RDa = self.data.RRdiarrhea[ageName][breastfeedingCat]
                beta[ageName][breastfeedingCat] = RDa/RRnot #1. - ((RRnot - RDa) / RRnot)   
        return beta        
        


    # Calculate probability of stunting in current age-group given coverage by intervention
    def setProbStuntedIfCovered(self, coverage, stuntingDistribution):
        numAgeGroups = len(self.ages)
        for intervention in self.data.interventionCompleteList:
            self.probStuntedIfCovered[intervention] = {}
            self.probStuntedIfCovered[intervention]["not covered"] = {}
            self.probStuntedIfCovered[intervention]["covered"]     = {}
            for iAge in range(numAgeGroups):
                ageName = self.ages[iAge]
                OddsRatio = self.data.ORstuntingIntervention[intervention][ageName]
                fracCovered = coverage[intervention]
                fracStuntedThisAge = self.helper.sumStuntedComponents(stuntingDistribution[ageName])
                pn, pc = self.solveQuadratic(OddsRatio, fracCovered, fracStuntedThisAge)
                self.probStuntedIfCovered[intervention]["not covered"][ageName] = pn
                self.probStuntedIfCovered[intervention]["covered"][ageName]     = pc

    # Calculate probability of being anemic in each population group given coverage by intervention
    def setProbAnemicIfCovered(self, coverage, anemiaDistribution):
        for intervention in self.data.interventionCompleteList:
            self.probAnemicIfCovered[intervention] = {}
            self.probAnemicIfCovered[intervention]["not covered"] = {}
            self.probAnemicIfCovered[intervention]["covered"] = {}
            for pop in self.allPops:
                fracAnemicThisPop = anemiaDistribution[pop]["anemic"]
                fracCovered = coverage[intervention] 
                # hidden IFAS interventions do not have corresponding RR/OR
                if ' with bed nets' in intervention:
                    thisIntervention = intervention.replace(" with bed nets", "")
                else:
                    thisIntervention = intervention    
                # get correct RR/OR
                relativeRisk = self.data.RRanemiaIntervention[pop].get(thisIntervention)
                if relativeRisk is not None: # have RR for this intervention
                    # for RR, solve linear equation for prob anemic not covered (pn) and covered (pc)
                    pn = fracAnemicThisPop/(relativeRisk*fracCovered + (1.- fracCovered))
                    pc = relativeRisk*pn
                else: # must be OR
                    oddsRatio = self.data.ORanemiaIntervention[pop][thisIntervention]
                    pn, pc = self.solveQuadratic(oddsRatio, fracCovered, fracAnemicThisPop)
                self.probAnemicIfCovered[intervention]["not covered"][pop] = pn
                self.probAnemicIfCovered[intervention]["covered"][pop] = pc

    # calculate probability of wasting in current age group given coverage by intervention
    def setProbWastedIfCovered(self, coverage, wastingDistribution):
        numAgeGroups = len(self.ages)
        for wastingCat in self.wastedList:
            self.probWastedIfCovered[wastingCat] = {}
            for intervention in self.data.interventionCompleteList:
                self.probWastedIfCovered[wastingCat][intervention] = {}
                self.probWastedIfCovered[wastingCat][intervention]["covered"] = {}
                self.probWastedIfCovered[wastingCat][intervention]["not covered"] = {}
                for iAge in range(numAgeGroups):
                        ageName = self.ages[iAge]
                        oddsRatio = self.data.ORwastingIntervention[wastingCat][ageName][intervention]
                        fracCovered = coverage[intervention]
                        fracThisCatThisAge = wastingDistribution[ageName][wastingCat]
                        pn, pc = self.solveQuadratic(oddsRatio, fracCovered, fracThisCatThisAge)
                        self.probWastedIfCovered[wastingCat][intervention]["not covered"][ageName] = pn
                        self.probWastedIfCovered[wastingCat][intervention]["covered"][ageName] = pc

    # Calculate probability of stunting in current age-group given coverage by intervention
    def setProbCorrectlyBreastfedIfCovered(self, coverage, breastfeedingDistribution):
        numAgeGroups = len(self.ages)
        for intervention in self.data.interventionCompleteList:
            self.probCorrectlyBreastfedIfCovered[intervention] = {}
            self.probCorrectlyBreastfedIfCovered[intervention]["not covered"] = {}
            self.probCorrectlyBreastfedIfCovered[intervention]["covered"]     = {}
            for i in range(numAgeGroups):
                ageName = self.ages[i]
                OddsRatio = self.data.ORappropriatebfIntervention[intervention][ageName]
                fracCovered = coverage[intervention]
                appropriatePractice = self.data.ageAppropriateBreastfeeding[ageName]
                fracCorrectlyBreastfedThisAge = breastfeedingDistribution[ageName][appropriatePractice]
                pn, pc = self.solveQuadratic(OddsRatio, fracCovered, fracCorrectlyBreastfedThisAge)
                self.probCorrectlyBreastfedIfCovered[intervention]["not covered"][ageName] = pn
                self.probCorrectlyBreastfedIfCovered[intervention]["covered"][ageName]     = pc


    def solveQuadratic(self, oddsRatio, fracA, fracB):
        # solves quadratic to calculate probabilities where e.g.:
        # fracA is fraction covered by intervention
        # fracB is fraction of pop. in a particular risk status
        from numpy import sqrt
        eps = 1.e-5
        a = (1. - fracA) * (1. - oddsRatio)
        b = (oddsRatio - 1) * fracB - oddsRatio * fracA - (1. - fracA)
        c = fracB
        det = sqrt(b ** 2 - 4. * a * c)
        if (abs(a) < eps):
            p0 = -c / b
        else:
            soln1 = (-b + det) / (2. * a)
            soln2 = (-b - det) / (2. * a)
            if (soln1 > 0.) and (soln1 < 1.): p0 = soln1
            if (soln2 > 0.) and (soln2 < 1.): p0 = soln2
        p1 = p0 * oddsRatio / (1. - p0 + oddsRatio * p0)
        return p0, p1

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
        FracStunted = self.initialModel.listOfAgeCompartments[0].getStuntedFraction() #* self.initialStuntingTrend
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
        
    def getBirthWastingQuarticCoefficients(self, wastingCat):
        FracBO = [0.]*4
        FracBO[1] = self.data.birthOutcomeDist["Term SGA"]
        FracBO[2] = self.data.birthOutcomeDist["Pre-term AGA"]
        FracBO[3] = self.data.birthOutcomeDist["Pre-term SGA"]
        FracBO[0] = 1. - sum(FracBO[1:3])
        OR = [1.]*4
        OR[0] = 1.
        OR[1] = self.data.ORwastingBirthOutcome[wastingCat]["Term SGA"]
        OR[2] = self.data.ORwastingBirthOutcome[wastingCat]["Pre-term AGA"]
        OR[3] = self.data.ORwastingBirthOutcome[wastingCat]["Pre-term SGA"]
        FracWasted = self.initialModel.listOfAgeCompartments[0].getWastedFraction(wastingCat)
        # [i] will refer to the three non-baseline birth outcomes
        A = FracBO[0]*(OR[1]-1.)*(OR[2]-1.)*(OR[3]-1.)
        B = (OR[1]-1.)*(OR[2]-1.)*(OR[3]-1.) * ( \
            sum( FracBO[0] / (OR[i]-1.)         for i in (1,2,3)) + \
            sum( OR[i] * FracBO[i] / (OR[i]-1.) for i in (1,2,3)) - \
            FracWasted )
        C = sum( FracBO[0] * (OR[i]-1.)         for i in (1,2,3)) + \
            sum( OR[i] * FracBO[i] * ((OR[1]-1.)+(OR[2]-1.)+(OR[3]-1.)-(OR[i]-1.)) for i in (1,2,3) ) - \
            sum( FracWasted*(OR[1]-1.)*(OR[2]-1.)*(OR[3]-1.)/(OR[i]-1.) for i in (1,2,3))
        D = FracBO[0] + \
            sum( OR[i] * FracBO[i] for i in (1,2,3)) - \
            sum( FracWasted * (OR[i]-1.) for i in (1,2,3))
        E = -FracWasted
        return [A,B,C,D,E]
        
    def getComplementaryFeedingQuarticCoefficients(self, stuntingDistribution, coverageArg):
        coverage = dcp(coverageArg)
        coEffs = {}
        # Fraction of population in each subset of food security and education
        X1 = self.data.demographics['fraction food insecure (default poor)']
        X2 = 1. 
        X3 = 0. 
        Ce  = coverage['Complementary feeding education']
        Cse = coverage['Public provision of complementary foods'] + coverage['Public provision of complementary foods with iron']
        if Cse > 0.95: #::warning:: this is current saturation coverage
            Cse = 0.95
        Frac = [0.]*4
        Frac[0] = X1*(1.-X2)*Ce + (1.-X1)*(1.-X3)*Ce + X1*(1.-X2)*(1.-Ce)*Cse
        Frac[1] = X1*(1.-X2)*(1.-Ce)*(1.-Cse) + (1.-X1)*(1.-X3)*(1.-Ce)
        Frac[2] = X1*X2*Cse + (1.-X1)*X3*Ce
        Frac[3] = X1*X2*(1.-Cse) + (1.-X1)*X3*(1.-Ce)
        for iAge in range(len(self.ages)): 
            ageName = self.ages[iAge]
            OR = [1.]*4
            OR[0] = 1.
            OR[1] = self.data.ORstuntingComplementaryFeeding[ageName]["Complementary feeding (food secure without promotion)"]
            OR[2] = self.data.ORstuntingComplementaryFeeding[ageName]["Complementary feeding (food insecure with promotion and supplementation)"]
            OR[3] = self.data.ORstuntingComplementaryFeeding[ageName]["Complementary feeding (food insecure with neither promotion nor supplementation)"]
            FracStunted = self.helper.sumStuntedComponents(stuntingDistribution[ageName])
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
            coEffs[ageName] = [A,B,C,D,E]
        return coEffs      



    # internal function to evaluate the quartic function for probability of stunting at birth at baseline birth outcome
    def evalQuartic(self, p0, coEffs):
        from math import pow
        A,B,C,D,E = coEffs
        return A*pow(p0,4) + B*pow(p0,3) + C*pow(p0,2) + D*p0 + E



    # SOLVE QUARTIC
    # p0 = Probability of Stunting/wasting at birth if Birth outcome = Term AGA
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
        for ageName in self.ages:
            baselineProbability[ageName] = self.getBaselineProbabilityViaQuartic(coEffs[ageName])
        return baselineProbability    


    def setProbStuntedAtBirth(self):
        coEffs = self.getBirthStuntingQuarticCoefficients()
        baselineProbStuntingAtBirth = self.getBaselineProbabilityViaQuartic(coEffs)        
        p0 = baselineProbStuntingAtBirth
        probStuntedAtBirth = {}
        probStuntedAtBirth["Term AGA"] = p0
        for birthOutcome in ["Pre-term SGA","Pre-term AGA","Term SGA"]:
            OR = self.data.ORstuntingBirthOutcome[birthOutcome]
            probStuntedAtBirth[birthOutcome] = p0*OR / (1.-p0+OR*p0)
            pi = probStuntedAtBirth[birthOutcome]
            if(pi<0. or pi>1.):
                raise ValueError("probability of stunting at birth, at outcome %s, is out of range (%f)"%(birthOutcome, pi))
        self.probStuntedAtBirth = probStuntedAtBirth        
           
    def setProbWastedAtBirth(self):
        probWastedAtBirth = {}
        for wastingCat in self.wastedList:
            coEffs = self.getBirthWastingQuarticCoefficients(wastingCat)
            p0 = self.getBaselineProbabilityViaQuartic(coEffs)
            probWastedAtBirth[wastingCat] = {}
            probWastedAtBirth[wastingCat]['Term AGA'] = p0
            for birthOutcome in ["Pre-term SGA","Pre-term AGA","Term SGA"]:
                probWastedAtBirth[wastingCat][birthOutcome] = {}
                OR = self.data.ORwastingBirthOutcome[wastingCat][birthOutcome]
                probWastedAtBirth[wastingCat][birthOutcome] = p0*OR / (1.-p0+OR*p0)
                pi = p0*OR / (1.-p0+OR*p0)
                if(pi<0. or pi>1.):
                    raise ValueError("probability of wasting at birth, at outcome %s, is out of range (%f)"%(birthOutcome, pi))
        self.probWastedAtBirth = probWastedAtBirth

    def setProbStuntedComplementaryFeeding(self, stuntingDistributionArg, coverageArg):
        coverage = dcp(coverageArg)
        stuntingDistribution  = dcp(stuntingDistributionArg)
        coEffs = self.getComplementaryFeedingQuarticCoefficients(stuntingDistribution, coverage)
        baselineProbStuntingComplementaryFeeding = self.getBaselineProbabilityViaQuarticByAge(coEffs)        
        probStuntedComplementaryFeeding = {}        
        for ageName in self.ages: 
            probStuntedComplementaryFeeding[ageName] = {}
            p0 = baselineProbStuntingComplementaryFeeding[ageName]
            probStuntedComplementaryFeeding[ageName]["Complementary feeding (food secure with promotion)"] = p0
            for group in self.data.foodSecurityGroups:
                OR = self.data.ORstuntingComplementaryFeeding[ageName][group]
                probStuntedComplementaryFeeding[ageName][group] = p0*OR / (1.-p0+OR*p0)
                pi = probStuntedComplementaryFeeding[ageName][group]
                if(pi<0. or pi>1.):
                    raise ValueError("probability of stunting complementary feeding, at outcome %s, age %s, is out of range (%f)"%(group, ageName, pi))
        self.probStuntedComplementaryFeeding = probStuntedComplementaryFeeding