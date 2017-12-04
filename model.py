# -*- coding: utf-8 -*-
"""
Created on Wed Feb 24 13:43:14 2016

@author: ruthpearson
"""
from __future__ import division
from copy import deepcopy as dcp

class Model:
    def __init__(self, listOfPregnantWomenAgeCompartments, listOfAgeCompartments, listOfReproductiveAgeCompartments, keyList):
        self.listOfPregnantWomenAgeCompartments = listOfPregnantWomenAgeCompartments
        self.listOfAgeCompartments = listOfAgeCompartments
        self.listOfReproductiveAgeCompartments = listOfReproductiveAgeCompartments
        for key in keyList.keys():
            setattr(self, key, keyList[key])
        self.year = 2017
        self.derived = None
        self.params = None
        import helper 
        self.thisHelper = helper.Helper()
        self.cumulativeAgingOutStunted = 0.0
        self.cumulativeAgingOutNotStunted = 0.0
        
    def setDerived(self, inputDerived):
        self.derived = inputDerived

       
    def setParams(self, inputParams):
        self.params = inputParams


    def getTotalNumberStunted(self):
        totalNumberStunted = 0.
        for ageGroup in self.listOfAgeCompartments:
            totalNumberStunted += ageGroup.getNumberStunted()
        return totalNumberStunted
        
    def getTotalStuntedFraction(self):
        totalNumberStunted = 0.
        totalPopSize = 0.
        for ageGroup in self.listOfAgeCompartments: 
            totalNumberStunted += ageGroup.getNumberStunted()
            totalPopSize += ageGroup.getTotalPopulation()
        return float(totalNumberStunted)/float(totalPopSize)
        
    def getTotalCumulativeDeathsChildren(self):
        totalCumulativeDeaths = 0
        for ageGroup in self.listOfAgeCompartments:
            totalCumulativeDeaths += ageGroup.getCumulativeDeaths()
        return totalCumulativeDeaths
        
    def getTotalCumulativeDeathsPW(self):
        totalCumulativeDeaths = 0
        for ageGroup in self.listOfPregnantWomenAgeCompartments:
            totalCumulativeDeaths += ageGroup.getCumulativeDeaths()
        return totalCumulativeDeaths    
        
    def getCumulativeAgingOutStunted(self):
        return self.cumulativeAgingOutStunted
        
    def getCumulativeAgingOutNotStunted(self):
        return self.cumulativeAgingOutNotStunted

    def getDALYs(self):
        DALYs = 0.
        numStuntedAt5 = self.getCumulativeAgingOutStunted()
        DALYs += numStuntedAt5 * 0.23 # * (self.thisHelper.keyList['lifeExpectancy'] - 5.) # 0.23 = disability weight
        for ageGroup in self.listOfAgeCompartments:
            cumulativeDeathsThisAge = ageGroup.getCumulativeDeaths()
            #DALYs += cumulativeDeathsThisAge * (self.thisHelper.keyList['lifeExpectancy'] - 2.5) # should be slightly different for each age
            DALYs += cumulativeDeathsThisAge * 33.3
        return DALYs
        
    def getAnemiaFractionChildren(self):
        totalNumberAnemic = self.getAnemiaNumberChildren()
        totalPopSize = self.getTotalPopChildren()
        return float(totalNumberAnemic)/float(totalPopSize)
        
    def getAnemiaNumberChildren(self):
        totalNumberAnemic = 0.
        for ageGroup in self.listOfAgeCompartments: 
            totalNumberAnemic += ageGroup.getNumberAnemic()
        return totalNumberAnemic   
        
    def getTotalPopChildren(self):
        totalPopSize = 0.
        for ageGroup in self.listOfAgeCompartments: 
            totalPopSize += ageGroup.getTotalPopulation()
        return totalPopSize
        
    def getAnemiaFractionWRA(self):
        totalNumberAnemic = self.getAnemiaNumberWRA()
        totalPopSize = self.getTotalPopWRA()
        return float(totalNumberAnemic)/float(totalPopSize)

    def getAnemiaNumberWRA(self):
        totalNumberAnemic = 0.
        for ageGroup in self.listOfReproductiveAgeCompartments: 
            totalNumberAnemic += ageGroup.getNumberAnemic()
        return totalNumberAnemic  
        
    def getTotalPopWRA(self):
        totalPopSize = 0.
        for ageGroup in self.listOfReproductiveAgeCompartments: 
            totalPopSize += ageGroup.getTotalPopulation()
        return totalPopSize    
    
    def getAnemiaFractionPregnant(self):
        totalNumberAnemic = self.getAnemiaNumberPregnant()
        totalPopSize = self.getTotalPopPregnant()
        return float(totalNumberAnemic)/float(totalPopSize)

    def getTotalPopPregnant(self):
        totalPopSize = 0.
        for ageGroup in self.listOfPregnantWomenAgeCompartments:
            totalPopSize += ageGroup.getTotalPopulation()
        return totalPopSize

    def getAnemiaNumberPregnant(self):
        totalNumberAnemic = 0.
        for ageGroup in self.listOfPregnantWomenAgeCompartments:
            totalNumberAnemic += ageGroup.getNumberAnemic()
        return totalNumberAnemic    
        
    def getAnemiaFractionEveryone(self):
        totalNumberAnemic = 0.
        totalPopSize = 0.
        totalNumberAnemic += self.getAnemiaNumberWRA()
        totalPopSize += self.getTotalPopWRA()
        totalNumberAnemic += self.getAnemiaNumberChildren()
        totalPopSize += self.getTotalPopChildren()
        totalNumberAnemic += self.getAnemiaNumberPregnant()
        totalPopSize += self.getTotalPopPregnant()
        return float(totalNumberAnemic)/float(totalPopSize) 
        
    def getAnemiaNumberEveryone(self):
        totalNumberAnemic = 0.
        totalNumberAnemic += self.getAnemiaNumberWRA()
        totalNumberAnemic += self.getAnemiaNumberChildren()
        totalNumberAnemic += self.getAnemiaNumberPregnant()
        return totalNumberAnemic    

    def getTotalNumberWasted(self):
        totalWasted = 0.
        for ageGroup in self.listOfAgeCompartments:
            totalWasted += ageGroup.getNumberWasted()
        return totalWasted

    def getTotalWastedFraction(self):
        totalNumberWasted = self.getTotalNumberWasted()
        totalPopSize = self.getTotalPopChildren()
        return float(totalNumberWasted)/float(totalPopSize)

    def getTotalInWastingCat(self, wastingCat):
        totalNumber = 0.
        for ageGroup in self.listOfAgeCompartments:
            totalNumber += ageGroup.getNumberInWastingCat(wastingCat)
        return totalNumber

    def getFractionInWastingCat(self, wastingCat):
        totalInCat = self.getTotalInWastingCat(wastingCat)
        totalPopSize = self.getTotalPopChildren()
        return float(totalInCat)/float(totalPopSize)

    def getWastingIncidence(self):
        return self.params.incidences

    def getOutcome(self, outcome):
        outcomeValue = None
        if outcome == 'deaths children':
            outcomeValue = self.getTotalCumulativeDeathsChildren()
        elif outcome == 'deaths PW':
            outcomeValue = self.getTotalCumulativeDeathsPW()
        elif outcome == 'deaths':
            outcomeValue = self.getTotalCumulativeDeathsChildren() + self.getTotalCumulativeDeathsPW()
        elif outcome == 'stunting':
            outcomeValue = self.getCumulativeAgingOutStunted()
        elif outcome == 'thrive':
            outcomeValue = self.getCumulativeAgingOutNotStunted()
        elif outcome == 'wasting_prev':
            outcomeValue = self.getTotalWastedFraction()
        elif outcome == 'SAM_prev':
            outcomeValue = self.getFractionInWastingCat('SAM')
        elif outcome == 'MAM_prev':
            outcomeValue = self.getFractionInWastingCat('MAM')
        elif outcome == 'DALYs':
            outcomeValue = self.getDALYs()
        elif outcome == 'stunting prev':
            outcomeValue = self.getTotalStuntedFraction()
        elif outcome == 'anemia frac children':
            outcomeValue = self.getAnemiaFractionChildren()
        elif outcome == 'anemia frac WRA':
            outcomeValue = self.getAnemiaFractionWRA()
        elif outcome == 'anemia frac pregnant':
            outcomeValue = self.getAnemiaFractionPregnant()
        elif outcome == 'anemia frac everyone':
            outcomeValue = self.getAnemiaFractionEveryone()
        elif outcome == 'anemia children':
            outcomeValue = self.getAnemiaNumberChildren()
        elif outcome == 'anemia WRA':
            outcomeValue = self.getAnemiaNumberWRA()
        elif outcome == 'anemia pregnant':
            outcomeValue = self.getAnemiaNumberPregnant()
        elif outcome == 'anemia everyone':
            outcomeValue = self.getAnemiaNumberEveryone()    
        return outcomeValue



    def updateCoverages(self, newCoverageArg):
        # newCoverage is a dictionary of coverages by intervention        
        newCoverage = dcp(self.params.coverage)
        newCoverage.update(newCoverageArg)

        # call initialisation of probabilities related to interventions
        self.derived.setProbStuntedIfCovered(self.params.coverage, self.params.stuntingDistribution)
        self.derived.setProbAnemicIfCovered(self.params.coverage, self.params.anemiaDistribution)
        self.derived.setProbWastedIfCovered(self.params.coverage, self.params.wastingDistribution)
        self.derived.setProbCorrectlyBreastfedIfCovered(self.params.coverage, self.params.breastfeedingDistribution)
        self.derived.setProbStuntedIfDiarrhea(self.params.incidences, self.params.breastfeedingDistribution, self.params.stuntingDistribution)
        self.derived.setProbAnemicIfDiarrhea(self.params.incidences, self.params.breastfeedingDistribution, self.params.anemiaDistribution)
        self.derived.setProbWastedIfDiarrhea(self.params.incidences, self.params.breastfeedingDistribution, self.params.wastingDistribution)
        self.derived.setProbStuntedComplementaryFeeding(self.params.stuntingDistribution, self.params.coverage)
        self.derived.updateFractionPregnaciesAverted(self.params.coverage)

        # add all constraints to coverages
        constrainedCoverage = self.params.addCoverageConstraints(newCoverage, self.listOfAgeCompartments, self.listOfReproductiveAgeCompartments)
        newCoverage = dcp(constrainedCoverage)

        # get combined reductions from all interventions
        mortalityUpdate = self.params.getMortalityUpdate(newCoverage)
        stuntingUpdate = self.params.getStuntingUpdate(newCoverage)
        anemiaUpdate = self.params.getAnemiaUpdate(newCoverage, self.thisHelper)
        wastingUpdate, fromSAMtoMAMupdate, fromMAMtoSAMupdate = self.params.getWastingPrevalenceUpdate(newCoverage)
        incidenceUpdate = self.params.getIncidenceUpdate(newCoverage)
        birthUpdate = self.params.getBirthOutcomeUpdate(newCoverage)
        newFracCorrectlyBreastfed = self.params.getAppropriateBFNew(newCoverage)
        stuntingUpdateComplementaryFeeding = self.params.getStuntingUpdateComplementaryFeeding(newCoverage)

        # MORTALITY
        #update mortality for each population
        for pop in self.ages + self.pregnantWomenAges:
            for cause in self.params.causesOfDeath:
                # update reference mortality
                self.derived.referenceMortality[pop][cause] *= mortalityUpdate[pop][cause]        
            
        # BREASTFEEDING
        for ageGroup in self.listOfAgeCompartments:
            ageName = ageGroup.name
            SumBefore = self.derived.getDiarrheaRiskSum(ageName, self.params.breastfeedingDistribution)
            correctPractice = self.params.ageAppropriateBreastfeeding[ageName]
            agePop = ageGroup.getTotalPopulation()
            numCorrectBefore   = ageGroup.getNumberCorrectlyBreastfed(correctPractice)
            numCorrectAfter    = agePop * newFracCorrectlyBreastfed[ageName]
            numShifting        = numCorrectAfter - numCorrectBefore
            numIncorrectBefore = agePop - numCorrectBefore
            fracCorrecting = 0.
            if numIncorrectBefore > 0.01:
                fracCorrecting = numShifting / numIncorrectBefore
            self.params.breastfeedingDistribution[ageName][correctPractice] = newFracCorrectlyBreastfed[ageName] # update breastfeeding distribution
            incorrectPractices = [practice for practice in self.breastfeedingList if practice!=correctPractice]
            for practice in incorrectPractices:
                self.params.breastfeedingDistribution[ageName][practice] *= 1. - fracCorrecting
            ageGroup.distribute(self.params.stuntingDistribution, self.params.wastingDistribution, self.params.breastfeedingDistribution, self.params.anemiaDistribution)
            SumAfter = self.derived.getDiarrheaRiskSum(ageName, self.params.breastfeedingDistribution)
            self.params.incidences[ageName]['Diarrhea'] *= SumAfter / SumBefore # update incidence of diarrhea
        beta = self.derived.getFracDiarrheaFixedZ()
        stuntingUpdateDueToBreastfeeding, dummyAnemia, dummyWasting = self.params.getUpdatesDueToIncidence(beta)

        # DIARRHEA AND WASTING INCIDENCE
        incidencesBefore = {}
        incidencesAfter = {}
        for condition in ['Diarrhea', 'MAM', 'SAM']:
            incidencesBefore[condition] = {}
            incidencesAfter[condition] = {}
            for ageGroup in self.listOfAgeCompartments:
                ageName = ageGroup.name
                incidencesBefore[condition][ageName] = self.params.incidences[ageName][condition]
                self.params.incidences[ageName][condition] *= incidenceUpdate[ageName][condition]
                incidencesAfter[condition][ageName] = self.params.incidences[ageName][condition]
        # diarrhea
        diaIncidenceBefore = incidencesBefore['Diarrhea']
        diaIncidenceAfter = incidencesAfter['Diarrhea']
        # get flow on effects to stunting, anemia and wasting due to changing diarrhea incidence
        Z0 = self.derived.getZa(diaIncidenceBefore, self.params.breastfeedingDistribution)
        Zt = self.derived.getZa(diaIncidenceAfter,  self.params.breastfeedingDistribution)
        beta = self.derived.getFracDiarrhea(Z0, Zt)
        # update probabilities given new incidence
        self.derived.updateDiarrheaProbsNewZa(Zt)
        stuntingUpdateDueToIncidence, anemiaUpdateDueToIncidence, wastingUpdateDueToDiarrheaIncidence = self.params.getUpdatesDueToIncidence(beta)
        # wasting
        wastingUpdateDueToWastingIncidence = {}
        for wastingCat in self.wastedList:
            wastingIncidenceBefore = incidencesBefore[wastingCat]
            wastingIncidenceAfter = incidencesAfter[wastingCat]
            # impact of wasting incidence on wasting prevalence (prevention interventions)
            wastingUpdateDueToWastingIncidence[wastingCat] = self.params.getWastingUpdateDueToWastingIncidence(wastingIncidenceBefore, wastingIncidenceAfter)

        # STUNTING
        for ageGroup in self.listOfAgeCompartments:
            ageName = ageGroup.name
            totalUpdate = stuntingUpdate[ageName] * stuntingUpdateDueToIncidence[ageName] * stuntingUpdateComplementaryFeeding[ageName] *stuntingUpdateDueToBreastfeeding[ageName]
            #save total stunting update for use in apply births and apply aging
            self.derived.stuntingUpdateAfterInterventions[ageName] *= totalUpdate
            #update stunting    
            oldProbStunting = ageGroup.getStuntedFraction()
            newProbStunting = oldProbStunting * totalUpdate
            self.params.stuntingDistribution[ageName] = self.thisHelper.restratify(newProbStunting)
            ageGroup.distribute(self.params.stuntingDistribution, self.params.wastingDistribution, self.params.breastfeedingDistribution, self.params.anemiaDistribution)

        # ANEMIA
        # Children
        for ageGroup in self.listOfAgeCompartments:
            ageName = ageGroup.name
            oldProbAnemia = ageGroup.getAnemicFraction()
            newProbAnemia = oldProbAnemia * anemiaUpdate[ageName] * anemiaUpdateDueToIncidence[ageName]
            self.params.anemiaDistribution[ageName]['anemic'] = newProbAnemia
            self.params.anemiaDistribution[ageName]['not anemic'] = 1. - newProbAnemia
            ageGroup.distribute(self.params.stuntingDistribution, self.params.wastingDistribution, self.params.breastfeedingDistribution, self.params.anemiaDistribution)

        # Women of reproductive age
        for ageGroup in self.listOfReproductiveAgeCompartments:
            ageName = ageGroup.name
            oldProbAnemia = ageGroup.getAnemicFraction()
            newProbAnemia = oldProbAnemia * anemiaUpdate[ageName] 
            self.params.anemiaDistribution[ageName]["anemic"] = newProbAnemia
            self.params.anemiaDistribution[ageName]["not anemic"] = 1. - newProbAnemia
            ageGroup.distributeAnemicPopulation(self.params.anemiaDistribution)

        # Pregnant Women
        for ageGroup in self.listOfPregnantWomenAgeCompartments:
            ageName = ageGroup.name
            oldProbAnemia = ageGroup.getAnemicFraction()
            newProbAnemia = oldProbAnemia * anemiaUpdate[ageName]
            self.params.anemiaDistribution[ageName]['anemic'] = newProbAnemia
            self.params.anemiaDistribution[ageName]['not anemic'] = 1. - newProbAnemia
            ageGroup.distributePopulation(self.params.anemiaDistribution)
        
        # WASTING
        constrainedWastingUpdate = self.params.addWastingInterventionConstraints(wastingUpdateDueToWastingIncidence)
        for ageGroup in self.listOfAgeCompartments:
            newProbWasted = 0.
            ageName = ageGroup.name
            # probability of being in either SAM or MAM for this age
            for wastingCat in self.wastedList: # 'SAM' must come first
                totalUpdateThisCatAndAge = wastingUpdate[ageName][wastingCat] * wastingUpdateDueToDiarrheaIncidence[ageName][wastingCat] * constrainedWastingUpdate[ageName][wastingCat] * \
                                            fromSAMtoMAMupdate[ageName][wastingCat] * fromMAMtoSAMupdate[ageName][wastingCat]
                # save for use in apply births
                self.derived.wastingUpdateAfterInterventions[ageName][wastingCat] *= totalUpdateThisCatAndAge
                # update overall wasting in this category
                oldProbThisCat = ageGroup.getWastedFraction(wastingCat)
                newProbThisCat = oldProbThisCat * totalUpdateThisCatAndAge
                self.params.wastingDistribution[ageName][wastingCat] = newProbThisCat
                newProbWasted += newProbThisCat
            # normality constraint on non-wasted proportions
            wastingDist = self.thisHelper.restratify(newProbWasted)
            for nonWastingCat in self.nonWastedList:
                self.params.wastingDistribution[ageName][nonWastingCat] = wastingDist[nonWastingCat]
            ageGroup.distribute(self.params.stuntingDistribution, self.params.wastingDistribution, self.params.breastfeedingDistribution, self.params.anemiaDistribution)
        # BIRTH OUTCOME
        for outcome in self.birthOutcomes:
            self.params.birthOutcomeDist[outcome] *= birthUpdate[outcome]
        self.params.birthOutcomeDist['Term AGA'] = 1 - (self.params.birthOutcomeDist['Pre-term SGA'] + self.params.birthOutcomeDist['Pre-term AGA'] + self.params.birthOutcomeDist['Term SGA'])    
            
        # UPDATE MORTALITY AFTER HAVING CHANGED: underlyingMortality and birthOutcomeDist
        self.updateMortalityRate()    

        # set newCoverages as the coverages in interventions
        self.params.coverage = newCoverage

            
            
    def updateMortalityRate(self):
        # Newborns first
        ageGroup = self.listOfAgeCompartments[0]
        ageName = ageGroup.name
        for breastfeedingCat in self.breastfeedingList:
            count = 0.
            for cause in self.params.causesOfDeath:
                Rb = self.params.RRdeathBreastfeeding[ageName][cause][breastfeedingCat]
                for outcome in self.birthOutcomes:
                    pbo = self.params.birthOutcomeDist[outcome]
                    Rbo = self.params.RRdeathByBirthOutcome[cause][outcome]
                    count += Rb * pbo * Rbo * self.derived.referenceMortality[ageName][cause]
            for stuntingCat in self.stuntingList:
                for wastingCat in self.wastingList:
                    for anemiaStatus in self.anemiaList:
                        ageGroup.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus].mortalityRate = count
        # over 1 months
        for ageGroup in self.listOfAgeCompartments[1:]:
            ageName = ageGroup.name
            for stuntingCat in self.stuntingList:
                for wastingCat in self.wastingList:
                    for breastfeedingCat in self.breastfeedingList:
                        for anemiaStatus in self.anemiaList:
                            count = 0.
                            for cause in self.params.causesOfDeath:
                                t1 = self.derived.referenceMortality[ageName][cause]
                                t2 = self.params.RRdeathStunting[ageName][cause][stuntingCat]
                                t3 = self.params.RRdeathWasting[ageName][cause][wastingCat]
                                t4 = self.params.RRdeathBreastfeeding[ageName][cause][breastfeedingCat]
                                t5 = self.params.RRdeathAnemia[ageName][cause][anemiaStatus]
                                count += t1 * t2 * t3 * t4 * t5
                            ageGroup.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus].mortalityRate = count
        # pregnant women
        for ageGroup in self.listOfPregnantWomenAgeCompartments:
            ageName = ageGroup.name
            for anemiaStatus in self.anemiaList:
                count = 0
                for cause in self.params.causesOfDeath:
                    t1 = self.derived.referenceMortality[ageName][cause]
                    t2 = self.params.RRdeathAnemia[ageName][cause][anemiaStatus]
                    count += t1 * t2
                ageGroup.dictOfBoxes[anemiaStatus].mortalityRate = count


    

    def applyMortality(self):
        for ageGroup in self.listOfAgeCompartments:
            for stuntingCat in self.stuntingList:
                for wastingCat in self.wastingList:
                    for breastfeedingCat in self.breastfeedingList:
                        for anemiaStatus in self.anemiaList:
                            thisBox = ageGroup.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus]
                            deaths = thisBox.populationSize * thisBox.mortalityRate * self.timestep
                            thisBox.populationSize -= deaths
                            thisBox.cumulativeDeaths += deaths

    def applyPregnantWomanMortality(self):
        for ageGroup in self.listOfPregnantWomenAgeCompartments:
            for anemiaStatus in self.anemiaList:
                thisBox = ageGroup.dictOfBoxes[anemiaStatus]
                deaths = thisBox.populationSize * thisBox.mortalityRate
                thisBox.cumulativeDeaths += deaths

    def applyAging(self):
        numCompartments = len(self.listOfAgeCompartments)
        # calculate how many people are aging out of each box
        agingOut = [None]*numCompartments
        for ind in range(0, numCompartments):
            thisCompartment = self.listOfAgeCompartments[ind]
            agingOut[ind] = {}
            for wastingCat in self.wastingList:
                agingOut[ind][wastingCat] = {}
                for breastfeedingCat in self.breastfeedingList:
                    agingOut[ind][wastingCat][breastfeedingCat] = {}
                    for stuntingCat in self.stuntingList:
                        agingOut[ind][wastingCat][breastfeedingCat][stuntingCat] = {}
                        for anemiaStatus in self.anemiaList:
                            thisBox = thisCompartment.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus]
                            agingOut[ind][wastingCat][breastfeedingCat][stuntingCat][anemiaStatus] = thisBox.populationSize * thisCompartment.agingRate 
        oldest = self.listOfAgeCompartments[numCompartments-1]
        countAgingOutStunted = oldest.getNumberStunted() * oldest.agingRate
        countAgingOutNotStunted = oldest.getNumberNotStunted() * oldest.agingRate
        self.cumulativeAgingOutStunted += countAgingOutStunted
        self.cumulativeAgingOutNotStunted += countAgingOutNotStunted                
        # first age group does not have aging in
        newborns = self.listOfAgeCompartments[0]
        for wastingCat in self.wastingList:
            for breastfeedingCat in self.breastfeedingList:
                for stuntingCat in self.stuntingList:
                    for anemiaStatus in self.anemiaList:
                        newbornBox = newborns.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus]
                        newbornBox.populationSize -= agingOut[0][wastingCat][breastfeedingCat][stuntingCat][anemiaStatus]
        # for older age groups, you need to decide if people stayed stunted from previous age group
        for ind in range(1, numCompartments):
            ageName = self.ages[ind]
            thisAgeCompartment = self.listOfAgeCompartments[ind]
            # calculate how many of those aging in from younger age group are stunted (binary)
            numAgingIn = {}
            numAgingIn["notstunted"] = 0.
            numAgingIn["yesstunted"] = 0.
            for prevBF in self.breastfeedingList:
                for prevWT in self.wastingList:
                    for prevAN in self.anemiaList:
                        numAgingIn["notstunted"] += agingOut[ind-1][prevWT][prevBF]["normal"][prevAN] + agingOut[ind-1][prevWT][prevBF]["mild"][prevAN]
                        numAgingIn["yesstunted"] += agingOut[ind-1][prevWT][prevBF]["moderate"][prevAN] + agingOut[ind-1][prevWT][prevBF]["high"][prevAN]
            # calculate which of those aging in are moving into a stunted category (4 categories)
            numAgingInStratified = {}
            for stuntingCat in self.stuntingList:
                numAgingInStratified[stuntingCat] = 0.
            for prevStunt in ["yesstunted", "notstunted"]:
                totalProbStunt = self.derived.probStuntedIfPrevStunted[prevStunt][ageName] * self.derived.stuntingUpdateAfterInterventions[ageName]
                restratifiedProbBecomeStunted = self.thisHelper.restratify(min(1., totalProbStunt))
                for stuntingCat in self.stuntingList:
                    numAgingInStratified[stuntingCat] += restratifiedProbBecomeStunted[stuntingCat] * numAgingIn[prevStunt]
            # distribute those aging in amongst those stunting categories but also breastfeeding, wasting and anemia
            for wastingCat in self.wastingList:
                paw = self.params.wastingDistribution[ageName][wastingCat]
                for breastfeedingCat in self.breastfeedingList:
                    pab = self.params.breastfeedingDistribution[ageName][breastfeedingCat]
                    for anemiaStatus in self.anemiaList:
                        paa = self.params.anemiaDistribution[ageName][anemiaStatus]
                        for stuntingCat in self.stuntingList:
                            thisBox = thisAgeCompartment.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus]
                            thisBox.populationSize -= agingOut[ind][wastingCat][breastfeedingCat][stuntingCat][anemiaStatus]
                            thisBox.populationSize += numAgingInStratified[stuntingCat] * pab * paw * paa
            # gaussianise
            stuntingDistributionNow = thisAgeCompartment.getStuntingDistribution()            
            probStunting = self.thisHelper.sumStuntedComponents(stuntingDistributionNow)
            #probStunting = thisAgeCompartment.getStuntedFraction()
            self.params.stuntingDistribution[ageName] = self.thisHelper.restratify(probStunting)
            thisAgeCompartment.distribute(self.params.stuntingDistribution, self.params.wastingDistribution, self.params.breastfeedingDistribution, self.params.anemiaDistribution)
            
    def updateWRApopulation(self):
        """Uses projected figures to determine the population of WRA not pregnant in a given age band and year
        warning: PW pop must be updated first."""
        #assuming WRA and PW have same age bands
        numCompartments = len(self.listOfReproductiveAgeCompartments)
        for indx in range(numCompartments):
            WRAcompartment = self.listOfReproductiveAgeCompartments[indx]
            ageName = WRAcompartment.name
            projectedWRApopThisAgeAndYear = self.params.projectedWRApopByAge[ageName][self.year]
            PWcompartment = self.listOfPregnantWomenAgeCompartments[indx]
            totalPWpopThisAgeAndYear = PWcompartment.getTotalPopulation()
            nonpregnantWRApopThisAgeAndYear = projectedWRApopThisAgeAndYear - totalPWpopThisAgeAndYear
            # distribute over risk factors
            anemiaDistribution = WRAcompartment.getAnemiaDistribution()
            for anemiaStatus in self.anemiaList:
                WRAbox = WRAcompartment.dictOfBoxes[anemiaStatus]
                WRAbox.populationSize = nonpregnantWRApopThisAgeAndYear * anemiaDistribution[anemiaStatus]

    def updatePWpopulation(self):
        """Use prenancy rate to distribute PW into age groups.
        Distribute into age bands by age distribution, assumed constant over time."""
        numCompartments = len(self.listOfPregnantWomenAgeCompartments)
        numWRA = self.getTotalPopWRA()
        PWPop = self.derived.pregnancyRate * numWRA * (1. - self.derived.fractionPregnancyAverted)
        for index in range(numCompartments):
            thisCompartment = self.listOfPregnantWomenAgeCompartments[index]
            ageName = thisCompartment.name
            popThisAge = PWPop * self.params.PWageDistribution[ageName]
            anemiaDistribution = thisCompartment.getAnemiaDistribution()
            for anemiaStatus in self.anemiaList:
                thisBox = thisCompartment.dictOfBoxes[anemiaStatus]
                thisBox.populationSize = popThisAge * anemiaDistribution[anemiaStatus] # distributed based on current anemia distribution


    def applyBirths(self):
        # num annual births = birth rate x num WRA x (1 - frac preg averted)
        numWRA = self.getTotalPopWRA()
        annualBirths = self.derived.birthRate * numWRA * (1. - self.derived.fractionPregnancyAverted)
        # calculate total number of new babies
        numNewBabies = annualBirths * self.timestep
        # convenient names
        ageGroup = self.listOfAgeCompartments[0]
        ageName  = ageGroup.name
        # restratify stunting and wasting
        restratifiedStuntingAtBirth = {}
        restratifiedWastingAtBirth = {}
        for outcome in self.birthOutcomes:
            totalProbStunted = self.derived.probStuntedAtBirth[outcome] * self.derived.stuntingUpdateAfterInterventions['<1 month']
            restratifiedStuntingAtBirth[outcome] = self.thisHelper.restratify(totalProbStunted)
            restratifiedWastingAtBirth[outcome] = {}
            totalProbWasted = 0.
            # distribute proportions for wasting categories
            for wastingCat in self.wastedList:
                probWastedThisCat = self.derived.probWastedAtBirth[wastingCat][outcome] * self.derived.wastingUpdateAfterInterventions['<1 month'][wastingCat]
                restratifiedWastingAtBirth[outcome][wastingCat] = probWastedThisCat
                totalProbWasted += probWastedThisCat
            # normality constraint on non-wasted proportions
            for nonWastingCat in self.nonWastedList:
                wastingDist = self.thisHelper.restratify(totalProbWasted)
                restratifiedWastingAtBirth[outcome][nonWastingCat] = wastingDist[nonWastingCat]
        # sum over birth outcome for full stratified stunting and wasting fractions, then apply to birth distribution
        stuntingFractions = {}
        wastingFractions = {}
        for wastingCat in self.wastingList:
            wastingFractions[wastingCat] = 0.
            for outcome in self.birthOutcomes:
                wastingFractions[wastingCat] += restratifiedWastingAtBirth[outcome][wastingCat] * self.params.birthOutcomeDist[outcome]
        for stuntingCat in self.stuntingList:
            stuntingFractions[stuntingCat] = 0.
            for outcome in self.birthOutcomes:
                stuntingFractions[stuntingCat] += restratifiedStuntingAtBirth[outcome][stuntingCat] * self.params.birthOutcomeDist[outcome]
        for wastingCat in self.wastingList:
            for stuntingCat in self.stuntingList:
                for breastfeedingCat in self.breastfeedingList:
                    for anemiaStatus in self.anemiaList:
                        ageGroup.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus].populationSize += numNewBabies * self.params.breastfeedingDistribution[ageName][breastfeedingCat] * \
                                                                                                                            self.params.anemiaDistribution[ageName][anemiaStatus] *\
                                                                                                                            stuntingFractions[stuntingCat] * wastingFractions[wastingCat]

    def applyAgingAndBirths(self):
        # aging must happen before births
        self.applyAging()
        self.applyBirths()

    def updateRiskDistributions(self):
        for ageGroup in self.listOfAgeCompartments:
            ageName = ageGroup.name
            self.params.stuntingDistribution[ageName]      = ageGroup.getStuntingDistribution()
            self.params.wastingDistribution[ageName]       = ageGroup.getWastingDistribution()
            self.params.breastfeedingDistribution[ageName] = ageGroup.getBreastfeedingDistribution()
            self.params.anemiaDistribution[ageName] = ageGroup.getAnemiaDistribution()

    def updateYearlyRiskDistributions(self):
        womenPops = self.listOfReproductiveAgeCompartments + self.listOfPregnantWomenAgeCompartments
        for ageGroup in womenPops:
            ageName = ageGroup.name
            self.params.anemiaDistribution[ageName] = ageGroup.getAnemiaDistribution()

    def moveOneTimeStep(self):
        self.applyMortality() 
        self.applyAgingAndBirths()
        self.updateRiskDistributions()

    def moveModelOneYear(self):
        # monthly progession
        for month in range(12):
            self.moveOneTimeStep()
        self.applyPregnantWomanMortality()
        self.updatePWpopulation()
        self.updateWRApopulation()
        self.updateYearlyRiskDistributions()
        self.year += 1

