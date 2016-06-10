# -*- coding: utf-8 -*-
"""
Created on Wed Feb 24 13:43:14 2016

@author: ruthpearson
"""
from __future__ import division

class FertileWomen:
    def __init__(self, birthRate, populationSize, annualPercentPopGrowth):
        self.birthRate = birthRate
        self.populationSize = populationSize
        self.annualPercentPopGrowth = annualPercentPopGrowth
        
class Box:
    def __init__(self, stuntCat, wasteCat, breastfeedingCat, populationSize, mortalityRate):
        self.stuntCat =  stuntCat
        self.wasteCat = wasteCat
        self.breastfeedingCat = breastfeedingCat
        self.populationSize = populationSize
        self.mortalityRate = mortalityRate
        self.cumulativeDeaths = 0

class AgeCompartment:
    def __init__(self, name, dictOfBoxes, agingRate, keyList):
        self.name = name  
        self.dictOfBoxes = dictOfBoxes
        self.agingRate = agingRate
        self.ages, self.birthOutcomeList, self.wastingList, self.stuntingList, self.breastfeedingList = keyList

    def getTotalPopulation(self):
        totalSum = 0.
        for stuntingCat in self.stuntingList:
            for wastingCat in self.wastingList:
                for breastfeedingCat in self.breastfeedingList:
                    thisBox = self.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat] 
                    totalSum += thisBox.populationSize
        return totalSum

    def getStuntedFraction(self):
        NumberStunted = 0.
        for stuntingCat in ["moderate", "high"]:
            for wastingCat in self.wastingList:
                for breastfeedingCat in self.breastfeedingList:
                    NumberStunted += self.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize
        NumberTotal = self.getTotalPopulation()
        return float(NumberStunted)/float(NumberTotal)

    def getNumberStunted(self):
        NumberStunted = 0.
        for stuntingCat in ["moderate", "high"]:
            for wastingCat in self.wastingList:
                for breastfeedingCat in self.breastfeedingList:
                    NumberStunted += self.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize
        return NumberStunted


    def getCumulativeDeaths(self):
        totalSum = 0.
        for stuntingCat in self.stuntingList:
            for wastingCat in self.wastingList:
                for breastfeedingCat in self.breastfeedingList:
                    totalSum += self.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].cumulativeDeaths
        return totalSum


    def getStuntingDistribution(self):
        totalPop = self.getTotalPopulation()
        returnDict = {}
        for stuntingCat in self.stuntingList:
            returnDict[stuntingCat] = 0.
            for wastingCat in self.wastingList:
                for breastfeedingCat in self.breastfeedingList:
                    returnDict[stuntingCat] += self.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize / totalPop
        return returnDict

    def getWastingDistribution(self):
        totalPop = self.getTotalPopulation()
        returnDict = {}
        for wastingCat in self.wastingList:
            returnDict[wastingCat] = 0.
            for stuntingCat in self.stuntingList:
                for breastfeedingCat in self.breastfeedingList:
                    returnDict[wastingCat] += self.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize / totalPop
        return returnDict

    def getBreastfeedingDistribution(self):
        totalPop = self.getTotalPopulation()
        returnDict = {}
        for breastfeedingCat in self.breastfeedingList:
            returnDict[breastfeedingCat] = 0.
            for wastingCat in self.wastingList:
                for stuntingCat in self.stuntingList:
                    returnDict[breastfeedingCat] += self.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize / totalPop
        return returnDict

    def getNumberAppropriatelyBreastfed(self,practice):
        NumberAppropriatelyBreastfed = 0.
        for stuntingCat in self.stuntingList:
            for wastingCat in self.wastingList:
                NumberAppropriatelyBreastfed += self.dictOfBoxes[stuntingCat][wastingCat][practice].populationSize
        return NumberAppropriatelyBreastfed

    def distribute(self, stuntingDist, wastingDist, breastfeedingDist):
        ageName = self.name
        totalPop = self.getTotalPopulation()
        for stuntingCat in self.stuntingList:
            for wastingCat in self.wastingList:
                for breastfeedingCat in self.breastfeedingList:
                    self.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize = stuntingDist[ageName][stuntingCat] * wastingDist[ageName][wastingCat] * breastfeedingDist[ageName][breastfeedingCat] * totalPop


        
class Model:
    def __init__(self, name, fertileWomen, listOfAgeCompartments, keyList, timestep):
        self.name = name
        self.fertileWomen = fertileWomen
        self.listOfAgeCompartments = listOfAgeCompartments
        self.ages, self.birthOutcomeList, self.wastingList, self.stuntingList, self.breastfeedingList = keyList
        self.timestep = timestep
        self.itime = 0
        self.constants = None
        self.params = None
        import helper as helperCode
        self.helper = helperCode.Helper()
        
        
    def setConstants(self, inputConstants):
        self.constants = inputConstants

       
    def setParams(self, inputParams):
        self.params = inputParams


    def updateCoverages(self, newCoverage):
        #newCoverage is a dictionary of coverages by intervention        
        
        # call initialisation of probabilities related to interventions
        self.constants.getProbStuntedIfCoveredByIntervention(self.params.interventionCoverages, self.params.stuntingDistribution)
        self.constants.getProbAppropriatelyBreastfedIfCoveredByIntervention(self.params.interventionCoverages, self.params.breastfeedingDistribution)        
        self.constants.getFracStuntedIfDiarrhea(self.params.incidences, self.params.breastfeedingDistribution, self.params.stuntingDistribution)        
        self.constants.getProbsStuntingComplementaryFeeding(self.params.stuntingDistribution, self.params.interventionCoverages)        
        
        # get combined reductions from all interventions
        mortalityUpdate = self.params.getMortalityUpdate(newCoverage)
        stuntingUpdate = self.params.getStuntingUpdate(newCoverage)
        incidenceUpdate = self.params.getIncidenceUpdate(newCoverage)
        birthUpdate = self.params.getBirthOutcomeUpdate(newCoverage)
        appropriatebfFracNew = self.params.getAppropriateBFNew(newCoverage)
        stuntingUpdateComplementaryFeeding = self.params.getStuntingUpdateComplementaryFeeding(newCoverage)
        
        # MORTALITY
        for ageGroup in self.listOfAgeCompartments:
            ageName = ageGroup.name
            #update mortality            
            for cause in self.params.causesOfDeath:
                self.constants.underlyingMortalities[ageName][cause] *= mortalityUpdate[ageName][cause]        
            
        # BREASTFEEDING
        for ageGroup in self.listOfAgeCompartments:
            ageName = ageGroup.name
            SumBefore = self.constants.getDiarrheaRiskSum(ageName, self.params.breastfeedingDistribution)
            appropriatePractice = self.params.ageAppropriateBreastfeeding[ageName]
            totalPop = ageGroup.getTotalPopulation()
            numAppropriateBefore    = ageGroup.getNumberAppropriatelyBreastfed(appropriatePractice)
            numAppropriateAfter     = totalPop * appropriatebfFracNew[ageName]
            numShifting           = numAppropriateAfter - numAppropriateBefore
            numNotAppropriateBefore = totalPop - numAppropriateBefore
            fracShiftingNotAppropriate = 0.
            if numNotAppropriateBefore > 0.01:
                fracShiftingNotAppropriate = numShifting / numNotAppropriateBefore
            self.params.breastfeedingDistribution[ageName][appropriatePractice] = appropriatebfFracNew[ageName]
            BFlistNotAppropriate = [cat for cat in self.breastfeedingList if cat!=appropriatePractice]
            for cat in BFlistNotAppropriate:
                self.params.breastfeedingDistribution[ageName][cat] *= 1. - fracShiftingNotAppropriate
            ageGroup.distribute(self.params.stuntingDistribution, self.params.wastingDistribution, self.params.breastfeedingDistribution)
            SumAfter = self.constants.getDiarrheaRiskSum(ageName, self.params.breastfeedingDistribution)
            self.params.incidences[ageName]['Diarrhea'] = self.params.incidences[ageName]['Diarrhea'] / SumBefore * SumAfter

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
        # WARNING since incidences have been updated by breastfeeding, then the following two lines should have params.breastfeedingDist
        Z0 = self.constants.getZa(incidencesBefore, self.params.breastfeedingDistribution)
        Zt = self.constants.getZa(incidencesAfter,  self.params.breastfeedingDistribution)
        #Z0 = self.constants.getZa(incidencesBefore, self.constants.data.breastfeedingDistribution)
        #Zt = self.constants.getZa(incidencesAfter,  self.constants.data.breastfeedingDistribution)
        beta = self.constants.getBetaGivenZ0AndZt(Z0, Zt)
        stuntingUpdateDueToIncidence = self.params.getIncidenceStuntingUpdateGivenBeta(beta)
        
        # STUNTING
        for ageGroup in self.listOfAgeCompartments:
            ageName = ageGroup.name
            totalUpdate = stuntingUpdate[ageName] * stuntingUpdateDueToIncidence[ageName] * stuntingUpdateComplementaryFeeding[ageName]
            #save total stunting update for use in apply births and apply aging
            self.constants.stuntingUpdateAfterInterventions[ageName] *= totalUpdate
            #update stunting    
            oldProbStunting = ageGroup.getStuntedFraction()
            newProbStunting = oldProbStunting * totalUpdate
            self.params.stuntingDistribution[ageName] = self.helper.restratify(newProbStunting)
            ageGroup.distribute(self.params.stuntingDistribution, self.params.wastingDistribution, self.params.breastfeedingDistribution)
            
        # BIRTH OUTCOME
        for outcome in self.birthOutcomeList:
            self.params.birthOutcomeDist[outcome] *= birthUpdate[outcome]
        self.params.birthOutcomeDist['Term AGA'] = 1 - (self.params.birthOutcomeDist['Pre-term SGA'] + self.params.birthOutcomeDist['Pre-term AGA'] + self.params.birthOutcomeDist['Term SGA'])    
            
        # UPDATE MORTALITY AFTER HAVING CHANGED: underlyingMortality and birthOutcomeDist
        self.updateMortalityRate()    

        # set newCoverages as the coverages in interventions
        self.params.interventionCoverages = newCoverage

            
            
    def updateMortalityRate(self):
        # Newborns first
        ageCompartment = self.listOfAgeCompartments[0]
        age = ageCompartment.name
        for breastfeedingCat in self.breastfeedingList:
            count = 0.
            for cause in self.params.causesOfDeath:
                Rb = self.params.RRBreastfeeding[age][cause][breastfeedingCat]
                for outcome in self.birthOutcomeList:
                    pbo = self.params.birthOutcomeDist[outcome]
                    Rbo = self.params.RRdeathByBirthOutcome[cause][outcome]
                    count += Rb * pbo * Rbo * self.constants.underlyingMortalities[age][cause]
            for stuntingCat in self.stuntingList:
                for wastingCat in self.wastingList:
                    ageCompartment.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].mortalityRate = count
        # over 1 months
        for ageCompartment in self.listOfAgeCompartments[1:]:
            age = ageCompartment.name
            for stuntingCat in self.stuntingList:
                for wastingCat in self.wastingList:
                    for breastfeedingCat in self.breastfeedingList:
                        count = 0.
                        for cause in self.params.causesOfDeath:
                            t1 = self.constants.underlyingMortalities[age][cause]
                            t2 = self.params.RRStunting[age][cause][stuntingCat]
                            t3 = self.params.RRWasting[age][cause][wastingCat]
                            t4 = self.params.RRBreastfeeding[age][cause][breastfeedingCat]
                            count += t1 * t2 * t3 * t4                            
                        ageCompartment.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].mortalityRate = count

    

    def applyMortality(self):
        for ageCompartment in self.listOfAgeCompartments:
            for stuntingCat in self.stuntingList:
                for wastingCat in self.wastingList:
                    for breastfeedingCat in self.breastfeedingList:
                        thisBox = ageCompartment.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat]
                        deaths = thisBox.populationSize * thisBox.mortalityRate * self.timestep
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
                        thisBox = thisCompartment.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat] 
                        agingOut[ind][wastingCat][breastfeedingCat][stuntingCat] = thisBox.populationSize * thisCompartment.agingRate #*self.timestep
        # first age group does not have aging in
        newborns = self.listOfAgeCompartments[0]
        for wastingCat in self.wastingList:
            for breastfeedingCat in self.breastfeedingList:
                for stuntingCat in self.stuntingList:
                    newbornBox = newborns.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat]
                    newbornBox.populationSize -= agingOut[0][wastingCat][breastfeedingCat][stuntingCat]
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
                    numAgingIn["notstunted"] += agingOut[ind-1][prevWT][prevBF]["normal"] + agingOut[ind-1][prevWT][prevBF]["mild"]
                    numAgingIn["yesstunted"] += agingOut[ind-1][prevWT][prevBF]["moderate"] + agingOut[ind-1][prevWT][prevBF]["high"]
            # calculate which of those aging in are moving into a stunted category (4 categories)
            numAgingInStratified = {}
            for stuntingCat in self.stuntingList:
                numAgingInStratified[stuntingCat] = 0.
            for prevStunt in ["yesstunted", "notstunted"]:
                totalProbStunt = self.constants.probStuntedIfPrevStunted[prevStunt][ageName] * self.constants.stuntingUpdateAfterInterventions[ageName]
                restratifiedProbBecomeStunted = self.helper.restratify(totalProbStunt)
                for stuntingCat in self.stuntingList:
                    numAgingInStratified[stuntingCat] += restratifiedProbBecomeStunted[stuntingCat] * numAgingIn[prevStunt]
            # distribute those aging in amongst those stunting categories but also breastfeeding and wasting
            for wastingCat in self.wastingList:
                paw = self.params.wastingDistribution[ageName][wastingCat]
                for breastfeedingCat in self.breastfeedingList:
                    pab = self.params.breastfeedingDistribution[ageName][breastfeedingCat]
                    for stuntingCat in self.stuntingList:
                        thisBox = thisAgeCompartment.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat]
                        thisBox.populationSize -= agingOut[ind][wastingCat][breastfeedingCat][stuntingCat]
                        thisBox.populationSize += numAgingInStratified[stuntingCat] * pab * paw

            # gaussianise
            stuntingDistributionNow = thisAgeCompartment.getStuntingDistribution()            
            probStunting = stuntingDistributionNow['high'] + stuntingDistributionNow['moderate']
            self.params.stuntingDistribution[ageName] = self.helper.restratify(probStunting)
            thisAgeCompartment.distribute(self.params.stuntingDistribution, self.params.wastingDistribution, self.params.breastfeedingDistribution)


    def applyBirths(self):
        # calculate total number of new babies
        birthRate = self.fertileWomen.birthRate  #WARNING: assuming per pre-determined timestep
        numWomen  = self.fertileWomen.populationSize
        numNewBabies = numWomen * birthRate * self.timestep
        self.fertileWomen.populationSize *= (1.+self.fertileWomen.annualPercentPopGrowth*self.timestep)
        # convenient names
        ageCompartment = self.listOfAgeCompartments[0]
        ageName         = ageCompartment.name
        # restratify Stunting
        restratifiedStuntingAtBirth = {}
        for outcome in self.birthOutcomeList:
            restratifiedStuntingAtBirth[outcome] = self.helper.restratify(self.constants.probsStuntingAtBirth[outcome])
        # sum over birth outcome for full stratified stunting fractions, then apply to birth distribution
        stuntingFractions = {}
        for stuntingCat in self.stuntingList:
            stuntingFractions[stuntingCat] = 0.
            for outcome in self.birthOutcomeList:
                stuntingFractions[stuntingCat] += restratifiedStuntingAtBirth[outcome][stuntingCat] * self.params.birthOutcomeDist[outcome]
            for wastingCat in self.wastingList:
                for breastfeedingCat in self.breastfeedingList:
                    ageCompartment.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize += numNewBabies * self.params.wastingDistribution[ageName][wastingCat] * self.params.breastfeedingDistribution[ageName][breastfeedingCat] * stuntingFractions[stuntingCat]

        #now reduce stunting due to interventions
        oldProbStunting = ageCompartment.getStuntedFraction()
        newProbStunting = oldProbStunting * self.constants.stuntingUpdateAfterInterventions['<1 month']
        self.params.stuntingDistribution[ageName] = self.helper.restratify(newProbStunting)
        ageCompartment.distribute(self.params.stuntingDistribution, self.params.wastingDistribution, self.params.breastfeedingDistribution)

    def applyAgingAndBirths(self):
        # aging must happen before births
        self.applyAging()
        self.applyBirths()

    def updateRiskDistributions(self):
        for ageCompartment in self.listOfAgeCompartments:
            ageName = ageCompartment.name
            self.params.stuntingDistribution[ageName]      = ageCompartment.getStuntingDistribution()
            self.params.wastingDistribution[ageName]       = ageCompartment.getWastingDistribution()
            self.params.breastfeedingDistribution[ageName] = ageCompartment.getBreastfeedingDistribution()


    def moveOneTimeStep(self):
        self.applyMortality() 
        self.applyAgingAndBirths()
        self.updateRiskDistributions()
        self.itime += 1

