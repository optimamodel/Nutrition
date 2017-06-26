# -*- coding: utf-8 -*-
"""
Created on Wed Feb 24 13:43:14 2016

@author: ruthpearson
"""
from __future__ import division
from copy import deepcopy as dcp

class Model:
    def __init__(self, pregnantWomen, listOfAgeCompartments, listOfReproductiveAgeCompartments, keyList):
        self.pregnantWomen = pregnantWomen
        self.listOfAgeCompartments = listOfAgeCompartments
        self.listOfReproductiveAgeCompartments = listOfReproductiveAgeCompartments
        for key in keyList.keys():
            setattr(self, key, keyList[key])
        self.itime = 0
        self.derived = None
        self.params = None
        import helper 
        self.helper = helper.Helper()
        self.cumulativeAgingOutStunted = 0.0
        self.cumulativeAgingOutNotStunted = 0.0
        
    def setDerived(self, inputDerived):
        self.derived = inputDerived

       
    def setParams(self, inputParams):
        self.params = inputParams


    def getTotalNumberStunted(self):
        totalNumberStunted = 0
        for ageGroup in self.listOfAgeCompartments:
            totalNumberStunted += ageGroup.getNumberStunted()
        return totalNumberStunted
        
    def getTotalStuntedFraction(self):
        totalNumberStunted = 0.
        totalPopSize = 0
        for ageGroup in self.listOfAgeCompartments: 
            totalNumberStunted += ageGroup.getNumberStunted()
            totalPopSize += ageGroup.getTotalPopulation()
        return float(totalNumberStunted)/float(totalPopSize)
        
    def getTotalCumulativeDeaths(self):
        totalCumulativeDeaths = 0
        for ageGroup in self.listOfAgeCompartments:
            totalCumulativeDeaths += ageGroup.getCumulativeDeaths()
        return totalCumulativeDeaths
        
    def getCumulativeAgingOutStunted(self):
        return self.cumulativeAgingOutStunted
        
    def getCumulativeAgingOutNotStunted(self):
        return self.cumulativeAgingOutNotStunted

    def getDALYs(self):
        DALYs = 0.0
        numStuntedAt5 = self.getCumulativeAgingOutStunted()
        DALYs += numStuntedAt5 * 0.23 # * (self.helper.keyList['lifeExpectancy'] - 5.) # 0.23 = disability weight
        for ageGroup in self.listOfAgeCompartments:
            cumulativeDeathsThisAge = ageGroup.getCumulativeDeaths()
            #DALYs += cumulativeDeathsThisAge * (self.helper.keyList['lifeExpectancy'] - 2.5) # should be slightly different for each age
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
        totalPopSize = 0
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
        totalPopSize = 0
        for ageGroup in self.listOfReproductiveAgeCompartments: 
            totalPopSize += ageGroup.getTotalPopulation()
        return totalPopSize    
    
    def getAnemiaFractionPregnant(self):
        totalNumberAnemic = self.pregnantWomen.getNumberAnemic()
        totalPopSize = self.pregnantWomen.getTotalPopulation()
        return float(totalNumberAnemic)/float(totalPopSize)
        
    def getAnemiaNumberPregnant(self):
        totalNumberAnemic = self.pregnantWomen.getNumberAnemic()
        return totalNumberAnemic    
        
    def getAnemiaFractionEveryone(self):
        totalNumberAnemic = 0.
        totalPopSize = 0
        totalNumberAnemic += self.getAnemiaNumberWRA()
        totalPopSize += self.getTotalPopWRA()
        totalNumberAnemic += self.getAnemiaNumberChildren()
        totalPopSize += self.getTotalPopChildren()
        totalNumberAnemic += self.pregnantWomen.getNumberAnemic()
        totalPopSize += self.pregnantWomen.getTotalPopulation()
        return float(totalNumberAnemic)/float(totalPopSize) 
        
    def getAnemiaNumberEveryone(self):
        totalNumberAnemic = 0.
        totalNumberAnemic += self.getAnemiaNumberWRA()
        totalNumberAnemic += self.getAnemiaNumberChildren()
        totalNumberAnemic += self.pregnantWomen.getNumberAnemic()
        return totalNumberAnemic    

    def getOutcome(self, outcome):
        outcomeValue = None
        if outcome == 'deaths':
            outcomeValue = self.getTotalCumulativeDeaths()
        elif outcome == 'stunting':
            outcomeValue = self.getCumulativeAgingOutStunted()
        elif outcome == 'thrive':
            outcomeValue = self.getCumulativeAgingOutNotStunted()    
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


    def getDiagnostics(self, verbose=False):
        newborns = self.listOfAgeCompartments[0]
        fracStuntedNew = newborns.getStuntedFraction()
        popsizeU5    = 0.
        numStuntedU5 = 0.
        for ageGroup in self.listOfAgeCompartments:
            numStuntedU5 += ageGroup.getNumberStunted()
            popsizeU5    += ageGroup.getTotalPopulation()
        fracStuntedU5 = numStuntedU5 / popsizeU5
        if verbose:
            print "\n     DIAGNOSTICS"
            print "stunting prevalence in newborns = %g%%"%(fracStuntedNew*100.)
            print "stunting prevalence in under 5s = %g%%"%(fracStuntedU5 *100.)
            print "populations size of    under 5s = %g  "%(popsizeU5)
            for ageGroup in self.listOfAgeCompartments:
                #for ageName in self.ages:
                ageName = ageGroup.name
                print "For age %s olds..."%(ageName)
                print "... incidence of diarrhea is %g"%(self.params.incidences[ageName]['Diarrhea'])
                print "... breastfeeding distribution"
                print ageGroup.getBreastfeedingDistribution()
                print "... mortality"
                print ageGroup.getMortality()
        return fracStuntedNew, fracStuntedU5, popsizeU5


    def updateCoverages(self, newCoverageArg):
        # newCoverage is a dictionary of coverages by intervention        
        newCoverage = dcp(self.params.coverage)
        newCoverage.update(newCoverageArg)

        # call initialisation of probabilities related to interventions
        self.derived.setProbStuntedIfCovered(self.params.coverage, self.params.stuntingDistribution)
        self.derived.setProbCorrectlyBreastfedIfCovered(self.params.coverage, self.params.breastfeedingDistribution)
        self.derived.setProbStuntedIfDiarrhea(self.params.incidences, self.params.breastfeedingDistribution, self.params.stuntingDistribution)
        self.derived.setProbStuntedComplementaryFeeding(self.params.stuntingDistribution, self.params.coverage)
        self.derived.setProbAnemicIfCovered(self.params.coverage, self.params.anemiaDistribution, self.params.fracAnemicExposedMalaria, self.params.fracAnemicNotPoor, self.params.fracAnemicPoor)
        
        # get combined reductions from all interventions
        mortalityUpdate = self.params.getMortalityUpdate(newCoverage)
        pregnantWomenMortalityUpdate = self.params.getPregnantWomenMortalityUpdate(newCoverage)
        stuntingUpdate = self.params.getStuntingUpdate(newCoverage)
        anemiaUpdate, malariaReduction = self.params.getAnemiaUpdate(newCoverage)
        incidenceUpdate = self.params.getIncidenceUpdate(newCoverage)
        birthUpdate = self.params.getBirthOutcomeUpdate(newCoverage)
        newFracCorrectlyBreastfed = self.params.getAppropriateBFNew(newCoverage)
        stuntingUpdateComplementaryFeeding = self.params.getStuntingUpdateComplementaryFeeding(newCoverage)
        

        # MORTALITY
        # add the pregnant women mortality update to the mortality update for pregnant women
        for cause in self.params.causesOfDeath:
            mortalityUpdate['pregnant women'][cause] *= 1. - pregnantWomenMortalityUpdate[cause]
        #update mortality for each population
        for pop in self.allPops:
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
        stuntingUpdateDueToBreastfeeding = self.params.getStuntingUpdateDueToIncidence(beta)

        # INCIDENCE
        incidencesBefore = {}
        incidencesAfter = {}  
        for ageGroup in self.listOfAgeCompartments:
            ageName = ageGroup.name
            #update incidence
            incidencesBefore[ageName] = self.params.incidences[ageName]['Diarrhea']
            self.params.incidences[ageName]['Diarrhea'] *= incidenceUpdate[ageName]['Diarrhea']
            incidencesAfter[ageName] = self.params.incidences[ageName]['Diarrhea']
        # get flow on effect to stunting due to changing incidence
        Z0 = self.derived.getZa(incidencesBefore, self.params.breastfeedingDistribution)
        Zt = self.derived.getZa(incidencesAfter,  self.params.breastfeedingDistribution)
        beta = self.derived.getFracDiarrhea(Z0, Zt)
        self.derived.updateProbStuntedIfDiarrheaNewZa(Zt)
        stuntingUpdateDueToIncidence = self.params.getStuntingUpdateDueToIncidence(beta)
        
        # STUNTING
        for ageGroup in self.listOfAgeCompartments:
            ageName = ageGroup.name
            totalUpdate = stuntingUpdate[ageName] * stuntingUpdateDueToIncidence[ageName] * stuntingUpdateComplementaryFeeding[ageName] *stuntingUpdateDueToBreastfeeding[ageName]
            #save total stunting update for use in apply births and apply aging
            self.derived.stuntingUpdateAfterInterventions[ageName] *= totalUpdate
            #update stunting    
            oldProbStunting = ageGroup.getStuntedFraction()
            newProbStunting = oldProbStunting * totalUpdate
            self.params.stuntingDistribution[ageName] = self.helper.restratify(newProbStunting)
            ageGroup.distribute(self.params.stuntingDistribution, self.params.wastingDistribution, self.params.breastfeedingDistribution, self.params.anemiaDistribution)

        # ANEMIA
        # note: apply anemia update for general population to all other populations

        # General population
        pop = 'general population'
        oldProbAnemia = self.params.anemiaDistribution[pop]["anemic"]
        newProbAnemia = oldProbAnemia * anemiaUpdate[pop]
        self.params.anemiaDistribution[pop]["anemic"] = newProbAnemia
        self.params.anemiaDistribution[pop]["not anemic"] = 1. - newProbAnemia

        # Children
        for ageGroup in self.listOfAgeCompartments:
            ageName = ageGroup.name
            oldProbAnemia = ageGroup.getAnemicFraction()
            newProbAnemia = oldProbAnemia * anemiaUpdate[ageName] * anemiaUpdate['general population']
            self.params.anemiaDistribution[ageName]['anemic'] = newProbAnemia
            self.params.anemiaDistribution[ageName]['not anemic'] = 1. - newProbAnemia
            ageGroup.distribute(self.params.stuntingDistribution, self.params.wastingDistribution, self.params.breastfeedingDistribution, self.params.anemiaDistribution)

        # Women of reproductive age
        for ageGroup in self.listOfReproductiveAgeCompartments:
            ageName = ageGroup.name
            # update anemia
            oldProbAnemia = ageGroup.getAnemicFraction()
            newProbAnemia = oldProbAnemia * anemiaUpdate[ageName] * anemiaUpdate['general population']
            self.params.anemiaDistribution[ageName]["anemic"] = newProbAnemia
            self.params.anemiaDistribution[ageName]["not anemic"] = 1. - newProbAnemia
            ageGroup.distributeAnemicPopulation(self.params.anemiaDistribution)

        # Pregnant Women
        pop = 'pregnant women'
        # add the reduction from IPTp to anemia update for pregnant women
        numberExposedMalaria = self.pregnantWomen.getTotalPopulation() * self.params.fracExposedMalaria[pop]
        numberAnemicExposedMalaria = numberExposedMalaria * self.params.fracAnemicExposedMalaria[pop]
        totalAnemicPopulation = self.pregnantWomen.getTotalPopulation() * self.params.anemiaDistribution[pop]["anemic"]
        thisReduction = malariaReduction[pop] * numberAnemicExposedMalaria / totalAnemicPopulation
        anemiaUpdate[pop] *= 1. - thisReduction   
        # update anemia probability
        oldProbAnemia = self.pregnantWomen.getAnemicFraction()
        newProbAnemia = oldProbAnemia * anemiaUpdate[pop] * anemiaUpdate['general population']
        self.params.anemiaDistribution[pop]['anemic'] = newProbAnemia
        self.params.anemiaDistribution[pop]['not anemic'] = 1. - newProbAnemia
        self.pregnantWomen.distributePopulation(self.params.anemiaDistribution, self.params.deliveryDistribution)
        # update fraction anemic exposed to malaria
        oldFracAnemiaMalaria = self.params.fracAnemicExposedMalaria[pop]
        malariaUpdate = 1. - malariaReduction[pop]
        newFracAnemiaMalaria = oldFracAnemiaMalaria * malariaUpdate
        self.params.fracAnemicExposedMalaria[pop] = newFracAnemiaMalaria
        

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
        for anemiaStatus in self.anemiaList:
            for deliveryStatus in self.deliveryList:
                count = 0
                for cause in self.params.causesOfDeath:
                    t1 = self.derived.referenceMortality['pregnant women'][cause]
                    t2 = self.params.RRdeathAnemia['pregnant women'][cause][anemiaStatus]
                    count += t1 * t2
                # in absense of risks distribute mortality between delivery groups based on population fraction # TODO is there an issue with below calculation?
                self.pregnantWomen.dictOfBoxes[anemiaStatus][deliveryStatus].mortalityRate = count *  self.params.deliveryDistribution[deliveryStatus]
        # women of reproductive age
        for ageGroup in self.listOfReproductiveAgeCompartments:
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

    def applyWRAMortality(self):
        for ageGroup in self.listOfReproductiveAgeCompartments:
            for anemiaStatus in self.anemiaList:
                thisBox = ageGroup.dictOfBoxes[anemiaStatus]
                deaths = thisBox.populationSize * thisBox.mortalityRate
                thisBox.populationSize -= deaths
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
                restratifiedProbBecomeStunted = self.helper.restratify(min(1., totalProbStunt))
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
            probStunting = self.helper.sumStuntedComponents(stuntingDistributionNow)
            #probStunting = thisAgeCompartment.getStuntedFraction()
            self.params.stuntingDistribution[ageName] = self.helper.restratify(probStunting)
            thisAgeCompartment.distribute(self.params.stuntingDistribution, self.params.wastingDistribution, self.params.breastfeedingDistribution, self.params.anemiaDistribution)
            
    def applyWRAaging(self):
        numCompartments = len(self.listOfReproductiveAgeCompartments)
        # calculate how many people are aging out of each box
        agingOut = [None]*numCompartments
        for ind in range(0, numCompartments):
            thisCompartment = self.listOfReproductiveAgeCompartments[ind]
            agingOut[ind] = {}
            for status in self.anemiaList:
                thisBox = thisCompartment.dictOfBoxes[status]
                agingOut[ind][status] = thisBox.populationSize * thisCompartment.agingRate 
        # add the new 15 -19 year olds
        thisCompartment = self.listOfReproductiveAgeCompartments[0]
        for status in self.anemiaList:
            thisBox = thisCompartment.dictOfBoxes[status]
            thisBox.populationSize += thisBox.populationSize * self.derived.annualGrowth15to19  
        # update all other reproductive population sizes
        # (15-19 years happened separately above)        
        for ind in range(1, numCompartments):
            thisCompartment = self.listOfReproductiveAgeCompartments[ind]
            for status in self.anemiaList:
                thisBox = thisCompartment.dictOfBoxes[status]
                # add those aging in
                thisBox.populationSize += agingOut[ind-1][status]
                # remove those aging out
                thisBox.populationSize -= agingOut[ind][status]
                

    def applyBirths(self):
        # calculate total number of new babies
        birthRate = self.pregnantWomen.birthRate  #WARNING: assuming per pre-determined timestep
        numWomen  = self.pregnantWomen.getTotalPopulation()
        numNewBabies = numWomen * birthRate * self.timestep
        # convenient names
        ageGroup = self.listOfAgeCompartments[0]
        ageName  = ageGroup.name
        # restratify Stunting
        restratifiedStuntingAtBirth = {}
        for outcome in self.birthOutcomes:
            totalProbStunted = self.derived.probStuntedAtBirth[outcome] * self.derived.stuntingUpdateAfterInterventions['<1 month']
            restratifiedStuntingAtBirth[outcome] = self.helper.restratify(totalProbStunted)
        # sum over birth outcome for full stratified stunting fractions, then apply to birth distribution
        stuntingFractions = {}
        for stuntingCat in self.stuntingList:
            stuntingFractions[stuntingCat] = 0.
            for outcome in self.birthOutcomes:
                stuntingFractions[stuntingCat] += restratifiedStuntingAtBirth[outcome][stuntingCat] * self.params.birthOutcomeDist[outcome]
            for wastingCat in self.wastingList:
                for breastfeedingCat in self.breastfeedingList:
                    for anemiaStatus in self.anemiaList:
                        ageGroup.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus].populationSize += numNewBabies * self.params.wastingDistribution[ageName][wastingCat] * \
                                                                                                                        self.params.breastfeedingDistribution[ageName][breastfeedingCat] * self.params.anemiaDistribution[ageName][anemiaStatus] *\
                                                                                                                        stuntingFractions[stuntingCat]

    def applyAgingAndBirths(self):
        # aging must happen before births
        self.applyAging()
        self.applyBirths()
        
    def progressPregnantWomen(self):
        # applyBirths() must happen first
        currentPopulationSize = self.pregnantWomen.getTotalPopulation()
        newPopulationSize = currentPopulationSize * (1. + self.pregnantWomen.annualGrowth * self.timestep)
        for anemiaStatus in self.anemiaList:
            for deliveryStatus in self.deliveryList:
                # calculate deaths (do this before pop size updated)
                deaths = self.pregnantWomen.dictOfBoxes[anemiaStatus][deliveryStatus].populationSize * self.pregnantWomen.dictOfBoxes[anemiaStatus][deliveryStatus].mortalityRate * self.timestep
                self.pregnantWomen.dictOfBoxes[anemiaStatus][deliveryStatus].cumulativeDeaths += deaths
                #update population sizes
                self.pregnantWomen.dictOfBoxes[anemiaStatus][deliveryStatus].populationSize = newPopulationSize * self.params.deliveryDistribution[deliveryStatus] * self.params.anemiaDistribution['pregnant women'][anemiaStatus]
        # TODO update delivery distribution?
        self.params.anemiaDistribution['pregnant women'] = self.pregnantWomen.getAnemiaDistribution()

    def updateRiskDistributions(self):
        for ageGroup in self.listOfAgeCompartments:
            ageName = ageGroup.name
            self.params.stuntingDistribution[ageName]      = ageGroup.getStuntingDistribution()
            self.params.wastingDistribution[ageName]       = ageGroup.getWastingDistribution()
            self.params.breastfeedingDistribution[ageName] = ageGroup.getBreastfeedingDistribution()
            self.params.anemiaDistribution[ageName] = ageGroup.getAnemiaDistribution()
            # when delivery distributions are altered, will need to update those here too

    def updateYearlyRiskDistributions(self):
        for ageGroup in self.listOfReproductiveAgeCompartments:
            ageName = ageGroup.name
            self.params.anemiaDistribution[ageName] = ageGroup.getAnemiaDistribution()

    def moveOneTimeStep(self):
        self.applyMortality() 
        self.applyAgingAndBirths()
        self.progressPregnantWomen()
        self.updateRiskDistributions()
        
    def moveModelOneYear(self):
        # monthly progession
        for month in range(12):
            self.moveOneTimeStep()
        # yearly progression
        self.applyWRAMortality()
        self.applyWRAaging()
        self.updateYearlyRiskDistributions()

