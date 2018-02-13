from itertools import product
from copy import deepcopy as dcp

class Box:
    def __init__(self, populationSize):
        self.populationSize = populationSize
        self.mortalityRate = None
        self.cumulativeDeaths = 0

class NonPWAgeGroup:
    def __init__(self, age, populationSize, boxes, anaemiaDist, birthOutcomeDist, birthAgeDist, birthIntervalDist, constants):
        self.age = age
        # self.populationSize = populationSize
        self.boxes = dcp(boxes)
        self.anaemiaDist = dcp(anaemiaDist)
        self.birthOutcomeDist = dcp(birthOutcomeDist)
        self.birthAgeDist = dcp(birthAgeDist)
        self.birthIntervalDist = dcp(birthIntervalDist)
        self.const = constants
        self.probConditionalCoverage = {}
        self.annualPrevChange = {}
        self._setStorageForUpdates()
        self._setBirthProbs()

    def _setStorageForUpdates(self):
        self.anaemiaUpdate = 1.
        self.birthAgeUpdate = {}
        for BA in self.const.birthAges:
            self.birthAgeUpdate[BA] = 1.

    def _setBirthProbs(self):
        """
        Setting the probability of each birth outcome.
        :return:
        """
        self.birthProb = {}
        for outcome, frac in self.birthOutcomeDist.iteritems():
            thisSum = 0.
            for ageOrder, fracAO in self.birthAgeDist.iteritems():
                RRAO = self.const.RRageOrder[ageOrder][outcome]
                for interval, fracInterval in self.birthIntervalDist.iteritems():
                    RRinterval = self.const.RRinterval[interval][outcome]
                    thisSum += fracAO * RRAO * fracInterval * RRinterval
            self.birthProb[outcome] = thisSum

    def getAgeGroupPopulation(self):
        return sum(self.boxes[anaemiaCat].populationSize for anaemiaCat in self.const.anaemiaList)

    def getAgeGroupNumberAnaemic(self):
        for anaemiaCat in self.const.anaemicList:
            return self.boxes[anaemiaCat].populationSize

    def getFracAnaemic(self):
        return self.getAgeGroupNumberAnaemic() / self.getAgeGroupPopulation()

    def getFracRisk(self, risk):
        return self.getFracAnaemic()

    def updateAnaemiaDist(self):
        totalPop = self.getAgeGroupPopulation()
        for anaemiaCat in self.const.anaemiaList:
            self.anaemiaDist[anaemiaCat] = self.boxes[anaemiaCat].populationSize / totalPop

    def redistributePopulation(self):
        for anaemiaCat in self.const.anaemiaList:
            self.boxes[anaemiaCat].populationSize = self.anaemiaDist[anaemiaCat] * self.getAgeGroupPopulation()

class PWAgeGroup:
    def __init__(self, age, populationSize, boxes, anaemiaDist, ageingRate, constants):
        self.age = age
        # self.populationSize = populationSize
        self.boxes = dcp(boxes)
        self.anaemiaDist = dcp(anaemiaDist)
        self.ageingRate = ageingRate
        self.const = constants
        self.probConditionalCoverage = {}
        self.annualPrevChange = {}
        self._setStorageForUpdates()

    def _setStorageForUpdates(self):
        self.anaemiaUpdate = 1.
        # this update will impact Newborn age group
        self.birthUpdate = {}
        for BO in self.const.birthOutcomes:
            self.birthUpdate[BO] = 1.
        self.mortalityUpdate = {}
        for cause in self.const.causesOfDeath:
            self.mortalityUpdate[cause] = 1.

    def getAgeGroupPopulation(self):
        return sum(self.boxes[anaemiaCat].populationSize for anaemiaCat in self.const.anaemiaList)

    def getAgeGroupNumberAnaemic(self):
        for anaemiaCat in self.const.anaemicList:
            return self.boxes[anaemiaCat].populationSize

    def getFracAnaemic(self):
        return self.getAgeGroupNumberAnaemic() / self.getAgeGroupPopulation()

    def getFracRisk(self, risk):
        return self.getFracAnaemic()

    def updateAnaemiaDist(self):
        totalPop = self.getAgeGroupPopulation()
        for anaemiaCat in self.const.anaemiaList:
            self.anaemiaDist[anaemiaCat] = self.boxes[anaemiaCat].populationSize / totalPop

    def redistributePopulation(self):
        for anaemiaCat in self.const.anaemiaList:
            self.boxes[anaemiaCat].populationSize = self.anaemiaDist[anaemiaCat] * self.getAgeGroupPopulation()

class ChildAgeGroup(object):
    def __init__(self, age, populationSize, boxes, anaemiaDist, incidences, stuntingDist, wastingDist, BFdist,
                 ageingRate, constants):
        self.age = age
        # self.populationSize = populationSize
        self.boxes = dcp(boxes)
        self.anaemiaDist = dcp(anaemiaDist)
        self.stuntingDist = dcp(stuntingDist)
        self.wastingDist = dcp(wastingDist)
        self.bfDist = dcp(BFdist)
        self.incidences = dcp(incidences)
        self.const = constants
        self.correctBF = self.const.correctBF[age]
        self.incorrectBF = list(set(self.const.bfList) - {self.correctBF})
        self.ageingRate = ageingRate
        self.probConditionalCoverage = {}
        self.probConditionalDiarrhoea = {}
        self.probConditionalStunting = {}
        self.programEffectiveness = {}
        self.annualPrevChange = {}
        self._setStorageForUpdates()
        self._updatesForAgeingAndBirths()

    def _updatesForAgeingAndBirths(self):
        """
        Stunting & wasting have impact on births and ageing, which needs to be adjusted at each time step
        :return:
        """
        self.continuedStuntingImpact = 1.
        self.continuedWastingImpact = {}
        for wastingCat in self.const.wastedList:
            self.continuedWastingImpact[wastingCat] = 1.

    def _setStorageForUpdates(self):
        # storing updates
        self.stuntingUpdate = 1.
        self.anaemiaUpdate = 1.
        self.bfUpdate = {}
        self.diarrhoeaUpdate = {}
        self.bfPracticeUpdate = self.bfDist[self.correctBF]
        for risk in ['Stunting', 'Anaemia'] + self.const.wastedList:
            self.bfUpdate[risk] = 1.
        self.mortalityUpdate = {}
        for cause in self.const.causesOfDeath:
            self.mortalityUpdate[cause] = 1.
        self.diarrhoeaIncidenceUpdate = 1.
        self.diarrhoeaUpdate = {}
        for risk in self.const.wastedList + ['Stunting', 'Anaemia']:
            self.diarrhoeaUpdate[risk] = 1.
        self.wastingPreventionUpdate = {}
        self.wastingTreatmentUpdate = {}
        for wastingCat in self.const.wastedList:
            self.wastingPreventionUpdate[wastingCat] = 1.
            self.wastingTreatmentUpdate[wastingCat] = 1.

    ###### POPULATION CALCULATIONS ######
    # TODO: would like to re-write for better implementation

    def getAgeGroupPopulation(self):
        totalPop = 0
        for stuntingCat in self.const.stuntingList:
            for wastingCat in self.const.wastingList:
                for bfCat in self.const.bfList:
                    for anaemiaCat in self.const.anaemiaList:
                        totalPop += self.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize
        return totalPop

    def getAgeGroupNumberStunted(self):
        numStunted = 0
        for stuntingCat in self.const.stuntedList:
            for wastingCat in self.const.wastingList:
                for bfCat in self.const.bfList:
                    for anaemiaCat in self.const.anaemiaList:
                        numStunted += self.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize
        return numStunted

    def getAgeGroupNumberNotStunted(self):
        numNotStunted = 0
        for stuntingCat in self.const.notStuntedList:
            for wastingCat in self.const.wastingList:
                for bfCat in self.const.bfList:
                    for anaemiaCat in self.const.anaemiaList:
                        numNotStunted += self.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize
        return numNotStunted

    def getAgeGroupNumberHealthy(self):
        numHealthly = 0
        for stuntingCat in self.const.notStuntedList:
            for wastingCat in self.const.nonWastedList:
                for bfCat in self.const.bfList:
                    for anaemiaCat in self.const.nonAnaemicList:
                        numHealthly += self.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize
        return numHealthly

    def getStuntingDistribution(self):
        totalPop = self.getAgeGroupPopulation()
        returnDict = {}
        for stuntingCat in self.const.stuntingList:
            returnDict[stuntingCat] = 0.
            for wastingCat in self.const.wastingList:
                for breastfeedingCat in self.const.bfList:
                    for anemiaStatus in self.const.anaemiaList:
                        returnDict[stuntingCat] += self.boxes[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus].populationSize / totalPop
        return returnDict

    def getWastingDistribution(self):
        totalPop = self.getAgeGroupPopulation()
        returnDict = {}
        for wastingCat in self.const.wastingList:
            returnDict[wastingCat] = 0.
            for stuntingCat in self.const.stuntingList:
                for breastfeedingCat in self.const.bfList:
                    for anemiaStatus in self.const.anaemiaList:
                        returnDict[wastingCat] += self.boxes[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus].populationSize / totalPop
        return returnDict

    def getAgeGroupNumberAnaemic(self):
        numAnaemic = 0
        for stuntingCat in self.const.stuntingList:
            for wastingCat in self.const.wastingList:
                for bfCat in self.const.bfList:
                    for anaemiaCat in self.const.anaemicList:
                        numAnaemic += self.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize
        return numAnaemic

    def getAgeGroupNumberWasted(self, wastingCat):
        numWasted = 0
        for stuntingCat in self.const.stuntingList:
            for bfCat in self.const.bfList:
                for anaemiaCat in self.const.anaemiaList:
                    numWasted += self.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize
        return numWasted

    def getCumulativeDeaths(self):
        deaths = 0
        for stuntingCat in self.const.stuntingList:
            for wastingCat in self.const.wastingList:
                for bfCat in self.const.bfList:
                    for anaemiaCat in self.const.anaemiaList:
                        deaths += self.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].cumulativeDeaths
        return deaths

    def getStuntedFrac(self):
        return self.getAgeGroupNumberStunted() / self.getAgeGroupPopulation()

    def getAnaemicFrac(self):
        return self.getAgeGroupNumberAnaemic() / self.getAgeGroupPopulation()

    def getWastedFrac(self, wastingCat):
        return self.getAgeGroupNumberWasted(wastingCat) /self.getAgeGroupPopulation()

    def getFracRisk(self, risk):
        if risk == 'Stunting':
            return self.getStuntedFrac()
        elif risk == 'Anaemia':
            return self.getAnaemicFrac()

    def getRiskFromDist(self, risk):
        if risk == 'Stunting':
            return self.stuntingDist['high'] + self.stuntingDist['moderate']
        elif risk == 'Anaemia':
            return self.anaemiaDist['anaemic']

    def getNumberCorrectlyBF(self):
        numCorrect = 0
        for stuntingCat in self.const.stuntingList:
            for wastingCat in self.const.wastingList:
                for anaemiaCat in self.const.anaemiaList:
                    numCorrect += self.boxes[stuntingCat][wastingCat][self.correctBF][anaemiaCat].populationSize
        return numCorrect

    def redistributePopulation(self):
        totalPop = self.getAgeGroupPopulation()
        for stuntingCat in self.const.stuntingList:
            for wastingCat in self.const.wastingList:
                for bfCat in self.const.bfList:
                    for anaemiaCat in self.const.anaemiaList:
                        self.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize = self.stuntingDist[stuntingCat] * \
                                                                                                self.wastingDist[wastingCat] * \
                                                                                                self.bfDist[bfCat] * \
                                                                                                self.anaemiaDist[anaemiaCat] * totalPop

    def updateStuntingDist(self):
        totalPop = self.getAgeGroupPopulation()
        for stuntingCat in self.const.stuntingList:
            self.stuntingDist[stuntingCat] = 0
            for wastingCat in self.const.wastingList:
                for breastfeedingCat in self.const.bfList:
                    for anemiaStatus in self.const.anaemiaList:
                        self.stuntingDist[stuntingCat] += self.boxes[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus].populationSize / totalPop

    def updateWastingDist(self):
        totalPop = self.getAgeGroupPopulation()
        for wastingCat in self.const.wastingList:
            self.wastingDist[wastingCat] = 0
            for stuntingCat in self.const.stuntingList:
                for breastfeedingCat in self.const.bfList:
                    for anaemiaCat in self.const.anaemiaList:
                        self.wastingDist[wastingCat] += self.boxes[stuntingCat][wastingCat][breastfeedingCat][
                                                                  anaemiaCat].populationSize / totalPop
    def updateAnaemiaDist(self):
        totalPop = self.getAgeGroupPopulation()
        for anaemiaCat in self.const.anaemiaList:
            self.anaemiaDist[anaemiaCat] = 0
            for stuntingCat in self.const.stuntingList:
                for wastingCat in self.const.wastingList:
                    for breastfeedingCat in self.const.bfList:
                        self.anaemiaDist[anaemiaCat] += self.boxes[stuntingCat][wastingCat][breastfeedingCat][
                                                              anaemiaCat].populationSize / totalPop

    def updateBFDist(self):
        totalPop = self.getAgeGroupPopulation()
        for bfCat in self.const.bfList:
            self.bfDist[bfCat] = 0
            for stuntingCat in self.const.stuntingList:
                for wastingCat in self.const.wastingList:
                    for anaemiaCat in self.const.anaemiaList:
                        self.bfDist[bfCat] += self.boxes[stuntingCat][wastingCat][bfCat][
                                                              anaemiaCat].populationSize / totalPop

    def _getFracDiarrhoeaFixedZ(self):
        beta = {}
        RRnot = self.const.RRdiarrhoea['none'][self.age]
        for bfCat in self.const.bfList:
            RDa = self.const.RRdiarrhoea[bfCat][self.age]
            beta[bfCat] = RDa/RRnot
        return beta

    def _getFracDiarrhoea(self, Z0, Zt):
        beta = {}
        RRnot = self.const.RRdiarrhoea["none"][self.age]
        for bfCat in self.const.bfList:
            RDa = self.const.RRdiarrhoea[bfCat][self.age]
            beta[bfCat] = 1. - (RRnot * Z0 - RDa * Zt) / \
                          (RRnot * Z0)
            # RDa * Zt[age] / (RRnot * Z0[age])
        return beta

    def _getZa(self):
        riskSum = self._getDiarrhoeaRiskSum()
        incidence = self.incidences['Diarrhoea']
        return incidence / riskSum

    def _getDiarrhoeaRiskSum(self):
        return sum(self.const.RRdiarrhoea[bfCat][self.age] * self.bfDist[bfCat] for bfCat in self.const.bfList)

    def _getAverageOR(self, Za, risk):
        from math import pow
        RRnot = self.const.RRdiarrhoea['none'][self.age]
        if risk == 'Stunting':
            OR = self.const.ORcondition['OR stunting by condition']['Diarrhoea'][self.age]
        elif risk == 'Anaemia':
            OR = self.const.ORcondition['OR anaemia by condition']['Severe diarrhoea'][self.age]
        elif risk == 'MAM' or risk == 'SAM':
            OR = self.const.ORcondition['OR '+risk+' by condition']['Diarrhoea'][self.age]
        else:
            print 'risk factor is invalid'
        AO = pow(OR, RRnot * Za * 1./self.ageingRate)
        return AO

    def _updateProbConditionalDiarrhoea(self, Zt):
        # stunting and anaemia
        AO = {}
        for risk in ['Stunting', 'Anaemia']:
            if risk == 'Anaemia':
                AO[risk] = self._getAverageOR(Zt * self.const.demographics['fraction severe diarrhoea'], risk)
            else:
                AO[risk] = self._getAverageOR(Zt, risk)
            Omega0 = self.probConditionalDiarrhoea[risk]['no diarrhoea']
            self.probConditionalDiarrhoea[risk]['diarrhoea'] = Omega0 * AO[risk] / (1. - Omega0 + AO[risk] * Omega0)
        # wasting cats
        for wastingCat in self.const.wastedList:
            AO = self._getAverageOR(Zt, wastingCat)
            Omega0 = self.probConditionalDiarrhoea[wastingCat]['no diarrhoea']
            self.probConditionalDiarrhoea[wastingCat]['diarrhoea'] = Omega0 * AO / (1. - Omega0 + AO * Omega0)

    # def restratify(self, fractionYes): # TODO: may not be the best place for this. Model?
    #     # Going from binary stunting/wasting to four fractions
    #     # Yes refers to more than 2 standard deviations below the global mean/median
    #     # in our notes, fractionYes = alpha
    #     invCDFalpha = norm.ppf(fractionYes)
    #     fractionHigh     = norm.cdf(invCDFalpha - 1.)
    #     fractionModerate = fractionYes - norm.cdf(invCDFalpha - 1.)
    #     fractionMild     = norm.cdf(invCDFalpha + 1.) - fractionYes
    #     fractionNormal   = 1. - norm.cdf(invCDFalpha + 1.)
    #     restratification = {}
    #     restratification["normal"] = fractionNormal
    #     restratification["mild"] = fractionMild
    #     restratification["moderate"] = fractionModerate
    #     restratification["high"] = fractionHigh
    #     return restratification


class Newborn(ChildAgeGroup):
    def __init__(self, age, populationSize, boxes, anaemiaDist, incidences, stuntingDist, wastingDist, BFdist,
                 ageingRate, constants, birthDist):
        """
        This is the <1 month age group, distinguished from the other age groups by birth outcomes, spacing etc etc.
        """
        super(Newborn, self).__init__(age, populationSize, boxes, anaemiaDist, incidences, stuntingDist, wastingDist, BFdist,
                 ageingRate, constants)
        self.birthDist = birthDist
        self.probRiskAtBirth = {}
        self.birthUpdate = {}
        for BO in self.const.birthOutcomes:
            self.birthUpdate[BO] = 1.


class Population(object):
    def __init__(self, name, project, constants):
        self.name = name
        self.project = dcp(project) # TODO: may not want to dcp all this -- only really want to get distribution data from project
        self.const = constants
        self.previousCov = None
        self.populationAreas = self.project.populationAreas
        self.riskDist = {}
        self.stuntingDist = self.project.riskDistributions['Stunting'] # TODO: error here b/c not using new distributions
        self.anaemiaDist= self.project.riskDistributions['Anaemia']
        self.bfDist = self.project.riskDistributions['Breastfeeding']
        self.wastingDist = self.project.riskDistributions['Wasting']
        self.birthDist = self.project.birthDist
        self.incidences = self.project.incidences
        self.RRdiarrhoea = self.project.RRdeath['Child diarrhoea']['Diarrhoea incidence']
        self.ORcondition = self.project.ORcondition
        self.boxes = {}

    def getDistribution(self, risk):
        return self.project.riskDistributions[risk]

    def _solveQuadratic(self, oddsRatio, fracA, fracB):
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

class Children(Population):
    def __init__(self, name, project, constants):
        super(Children, self).__init__(name, project, constants)
        self.ageGroups = []
        self._makePopSizes()
        self._makeBoxes()
        self._setChildrenReferenceMortality()
        self._updateMortalityRates()
        self._setProgramEffectiveness()
        self._setAnnualPrevChange()
        self._setCorrectBFpractice()
        self._setProbConditionalStunting()
        self._setProbStuntedAtBirth()
        self._setProbWastedAtBirth()

    ##### DATA WRANGLING ######

    def _setConditionalProbabilities(self):
        # self._setProbConditionalCoverage()
        self._setProbStuntedIfCovered()
        self._setProbAnaemicIfCovered()
        self._setProbWastedIfCovered()
        self._setProbCorrectlyBreastfedIfCovered()
        # self._setProbConditionalDiarrhoea()
        self._setProbStuntedIfDiarrhoea()
        self._setProbAnaemicIfDiarrhoea()
        self._setProbWastedIfDiarrhoea()

    def _setConditionalDiarrhoea(self):
        self._setProbStuntedIfDiarrhoea()
        self._setProbAnaemicIfDiarrhoea()
        self._setProbWastedIfDiarrhoea()

    def _makePopSizes(self):
        # for children less than 1 year, annual live births
        monthlyBirths = self.const.demographics['number of live births'] / 12.
        popSize = [pop * monthlyBirths for pop in self.const.childAgeSpans[:3]]
        # children > 1 year, who are not counted in annual 'live births'
        months = sum(self.const.childAgeSpans[3:])
        popRemainder = self.const.demographics['population U5'] - monthlyBirths * 12.
        monthlyRate = popRemainder/months
        popSize += [pop * monthlyRate for pop in self.const.childAgeSpans[3:]]
        self.popSizes = {age:pop for age, pop in zip(self.const.childAges, popSize)}

    def _makeBoxes(self):
        for idx in range(len(self.project.childAges)):
            age = self.project.childAges[idx]
            popSize = self.popSizes[age]
            boxes = {}
            stuntingDist = self.stuntingDist[age]
            stuntingDist = self.restratify(sum(stuntingDist[cat] for cat in self.const.stuntedList))
            anaemiaDist = self.anaemiaDist[age]
            wastingDist = self.wastingDist[age]
            probWasted = sum(wastingDist[cat] for cat in self.const.wastedList)
            nonWastingDist = self.restratify(probWasted)
            for cat in self.const.nonWastedList:
                wastingDist[cat] = nonWastingDist[cat]
            bfDist = self.bfDist[age]
            birthDist = self.birthDist
            incidences = self.project.incidences[age] # TODO: do this adjustment elsewhere, same as restratifying
            incidences = {condition: incidence * self.const.timestep for condition, incidence in incidences.iteritems()}
            ageingRate = 1./self.const.childAgeSpans[idx]
            for stuntingCat in self.const.stuntingList:
                boxes[stuntingCat] = {}
                for wastingCat in self.const.wastingList:
                    boxes[stuntingCat][wastingCat] = {}
                    for bfCat in self.const.bfList:
                        boxes[stuntingCat][wastingCat][bfCat] = {}
                        for anaemiaCat in self.const.anaemiaList:
                            thisPop = popSize * stuntingDist[stuntingCat] * anaemiaDist[anaemiaCat] * \
                                      wastingDist[wastingCat] * bfDist[bfCat]
                            boxes[stuntingCat][wastingCat][bfCat][anaemiaCat] = Box(thisPop)
            if age == '<1 month': # <1 month age group has slightly different functionality
                self.ageGroups.append(Newborn(age, popSize, boxes,
                                           anaemiaDist, incidences, stuntingDist, wastingDist, bfDist,
                                                ageingRate, self.const, birthDist))
            else:
                self.ageGroups.append(ChildAgeGroup(age, popSize, boxes,
                                           anaemiaDist, incidences, stuntingDist, wastingDist, bfDist,
                                                ageingRate, self.const))

    def _setChildrenReferenceMortality(self):
        # Equation is:  LHS = RHS * X
        # we are solving for X
        # Calculate RHS for each age and cause
        RHS = {}
        for age in self.const.childAges:
            RHS[age] = {}
            for cause in self.project.causesOfDeath:
                RHS[age][cause] = 0.
                for stuntingCat in self.const.stuntingList:
                    for wastingCat in self.const.wastingList:
                        for bfCat in self.const.bfList:
                            for anaemiaCat in self.const.anaemiaList:
                                t1 = self.stuntingDist[age][stuntingCat]
                                t2 = self.wastingDist[age][wastingCat]
                                t3 = self.bfDist[age][bfCat]
                                t4 = self.anaemiaDist[age][anaemiaCat]
                                t5 = self.project.RRdeath['Stunting'][cause][stuntingCat][age]
                                t6 = self.project.RRdeath['Wasting'][cause][wastingCat][age]
                                t7 = self.project.RRdeath['Breastfeeding'][cause][bfCat][age]
                                t8 = self.project.RRdeath['Anaemia'][cause][anaemiaCat][age]
                                RHS[age][cause] += t1 * t2 * t3 * t4 * t5 * t6 * t7 * t8
        # RHS for newborns only
        age = '<1 month'
        for cause in self.project.causesOfDeath:
            RHS[age][cause] = 0.
            for breastfeedingCat in self.const.bfList:
                Pbf = self.bfDist[age][breastfeedingCat]
                RRbf = self.project.RRdeath['Breastfeeding'][cause][breastfeedingCat][age]
                for birthoutcome in self.const.birthOutcomes:
                    Pbo = self.birthDist[birthoutcome]
                    RRbo = self.project.RRdeath['Birth outcomes'][cause][birthoutcome]
                    for anemiaStatus in self.const.anaemiaList:
                        Pan = self.anaemiaDist[age][anemiaStatus]
                        RRan = self.project.RRdeath['Anaemia'][cause][anemiaStatus][age]
                        RHS[age][cause] += Pbf * RRbf * Pbo * RRbo * Pan * RRan
        # calculate total mortality by age (corrected for units)
        AgePop = [age.getAgeGroupPopulation() for age in self.ageGroups]
        MortalityCorrected = {}
        LiveBirths = self.project.demographics["number of live births"]
        Mnew = self.project.mortalityRates["neonatal mortality"]
        Minfant = self.project.mortalityRates["infant mortality"]
        Mu5 = self.project.mortalityRates["under 5 mortality"]
        # Newborns
        ageName = self.ageGroups[0].age
        m0 = Mnew * LiveBirths / 1000. / AgePop[0]
        MortalityCorrected[ageName] = m0
        # 1-5 months
        ageName = self.ageGroups[1].age
        m1 = (Minfant - Mnew) * LiveBirths / 1000. * 5. / 11. / AgePop[1]
        MortalityCorrected[ageName] = m1
        # 6-12 months
        ageName = self.ageGroups[2].age
        m2 = (Minfant - Mnew) * LiveBirths / 1000. * 6. / 11. / AgePop[2]
        MortalityCorrected[ageName] = m2
        # 12-24 months
        ageName = self.ageGroups[3].age
        m3 = (Mu5 - Minfant) * LiveBirths / 1000. * 1. / 4. / AgePop[3]
        MortalityCorrected[ageName] = m3
        # 24-60 months
        ageName = self.ageGroups[4].age
        m4 = (Mu5 - Minfant) * LiveBirths / 1000. * 3. / 4. / AgePop[4]
        MortalityCorrected[ageName] = m4
        # Calculate LHS for each age and cause of death then solve for X
        for ageGroup in self.ageGroups:
            ageGroup.referenceMortality = {}
            age = ageGroup.age
            for cause in self.const.causesOfDeath:
                LHS_age_cause = MortalityCorrected[age] * self.project.deathDist[cause][age]
                ageGroup.referenceMortality[cause] = LHS_age_cause / RHS[age][cause]

    def _updateMortalityRates(self):
        # Newborns first
        ageGroup = self.ageGroups[0]
        age = ageGroup.age
        for bfCat in self.const.bfList:
            count = 0.
            for cause in self.project.causesOfDeath:
                Rb = self.project.RRdeath['Breastfeeding'][cause][bfCat][age]
                for outcome in self.const.birthOutcomes:
                    pbo = ageGroup.birthDist[outcome]
                    Rbo = self.project.RRdeath['Birth outcomes'][cause][outcome]
                    count += Rb * pbo * Rbo * ageGroup.referenceMortality[cause]
            for stuntingCat in self.const.stuntingList:
                for wastingCat in self.const.wastingList:
                    for anaemiaCat in self.const.anaemiaList:
                        ageGroup.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].mortalityRate = count
        # over 1 months
        for ageGroup in self.ageGroups[1:]:
            age = ageGroup.age
            for stuntingCat in self.const.stuntingList:
                for wastingCat in self.const.wastingList:
                    for bfCat in self.const.bfList:
                        for anaemiaCat in self.const.anaemiaList:
                            count = 0.
                            for cause in self.project.causesOfDeath:
                                t1 = ageGroup.referenceMortality[cause]
                                t2 = self.project.RRdeath['Stunting'][cause][stuntingCat][age]
                                t3 = self.project.RRdeath['Wasting'][cause][wastingCat][age]
                                t4 = self.project.RRdeath['Breastfeeding'][cause][bfCat][age]
                                t5 = self.project.RRdeath['Anaemia'][cause][anaemiaCat][age]
                                count += t1 * t2 * t3 * t4 * t5
                            ageGroup.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].mortalityRate = count

    def getTotalPopulation(self):
        return sum(ageGroup.getAgeGroupPopulation() for ageGroup in self.ageGroups)

    def getTotalNumberStunted(self):
        return sum(ageGroup.getAgeGroupNumberStunted() for ageGroup in self.ageGroups)

    def getTotalFracStunted(self):
        totalStunted = self.getTotalNumberStunted()
        totalPop = self.getTotalPopulation()
        return totalStunted / totalPop

    def getTotalNumberAnaemic(self):
        return sum(ageGroup.getAgeGroupNumberAnaemic() for ageGroup in self.ageGroups)

    def getTotalFracAnaemic(self):
        totalAnaemia = self.getTotalNumberAnaemic()
        totalPop = self.getTotalPopulation()
        return totalAnaemia / totalPop

    def getTotalNumberWasted(self, wastingCat):
        return sum(ageGroup.getAgeGroupNumberWasted(wastingCat) for ageGroup in self.ageGroups)

    def getTotalFracWasted(self):
        totalWasted = sum(self.getTotalNumberWasted(wastingCat) for wastingCat in self.const.wastedList)
        totalPop = self.getTotalPopulation()
        return totalWasted / totalPop

    def getFracWastingCat(self, wastingCat):
        totalThisCat = self.getTotalNumberWasted(wastingCat)
        totalPop = self.getTotalPopulation()
        return totalThisCat/totalPop

    def restratify(self, fractionYes):
        from scipy.stats import norm
        # Going from binary stunting/wasting to four fractions
        # Yes refers to more than 2 standard deviations below the global mean/median
        # in our notes, fractionYes = alpha
        invCDFalpha = norm.ppf(fractionYes)
        fractionHigh     = norm.cdf(invCDFalpha - 1.)
        fractionModerate = fractionYes - norm.cdf(invCDFalpha - 1.)
        fractionMild     = norm.cdf(invCDFalpha + 1.) - fractionYes
        fractionNormal   = 1. - norm.cdf(invCDFalpha + 1.)
        restratification = {}
        restratification["normal"] = fractionNormal
        restratification["mild"] = fractionMild
        restratification["moderate"] = fractionModerate
        restratification["high"] = fractionHigh
        return restratification

    def getFracStuntedGivenAge(self, age):
        ageMap = {'<1 month': 0, '1-5 months': 1, '6-11 months': 2, '12-23 months': 3, '24-59 months': 4}
        indx = ageMap[age]
        thisAge = self.ageGroups[indx]
        return thisAge.getStuntedFrac()

    def _replaceRiskList(self, index, newList):
        """replaces one risk list in a list of risk lists. index is the position of list to replace """
        alteredList = self.const.allRisks[:]
        alteredList[index] = newList
        return alteredList

    def _setProbConditionalStunting(self):
        """Calculate the probability of stunting given previous stunting between age groups"""
        for indx in range(1, len(self.ageGroups)):
            ageGroup = self.ageGroups[indx]
            thisAge = ageGroup.age
            prevAgeGroup = self.ageGroups[indx-1]
            OR = self.project.ORcondition['Stunting progression'][thisAge]
            fracStuntedThisAge = ageGroup.getStuntedFrac()
            fracStuntedPrev = prevAgeGroup.getStuntedFrac()
            pn, pc = self._solveQuadratic(OR, fracStuntedPrev, fracStuntedThisAge)
            ageGroup.probConditionalStunting['stunted'] = pc
            ageGroup.probConditionalStunting['not stunted'] = pn

    def _setProbConditionalCoverage(self): # TODO: this is more general version of the two following methods
        """Set the conditional probabilities of a risk factor (except wasting) given program coverage.
        Note that this value is dependent upon the baseline coverage of the program"""
        risks = [risk for i, risk in enumerate(self.const.risks) if i !=1 ] # remove wasting
        for risk in risks:
            cats = self.project.riskCategories[risk]
            middle = len(cats) / 2
            relevantCats = cats[middle:] # assumes list is symmetric
            for ageGroup in self.ageGroups:
                age = ageGroup.age
                dist = ageGroup.riskDists[risk]
                ageGroup.probConditionalCoverage[risk] = {}
                for program in self.const.programList:
                    ageGroup.probConditionalCoverage[risk][program] = {}
                    fracCovered = self.previousCov[program]
                    fracImpacted = sum(dist[cat] for cat in relevantCats)
                    if self.project.RRprograms[risk].get(program) is not None:
                        RR = self.project.RRprograms[risk][program][age]
                        pn = fracImpacted/(RR*fracCovered + (1.-fracCovered))
                        pc = RR * pn
                    else: # OR
                        OR = self.project.ORprograms[risk][program][age]
                        pn, pc = self._solveQuadratic(OR, fracCovered, fracImpacted)
                    ageGroup.probConditionalCoverage[risk][program]['covered'] = pc
                    ageGroup.probConditionalCoverage[risk][program]['not covered'] = pn

    def _setProbStuntedIfCovered(self):
        risk = 'Stunting'
        for ageGroup in self.ageGroups:
            age = ageGroup.age
            fracStunted = sum(ageGroup.stuntingDist[cat] for cat in self.const.stuntedList)
            ageGroup.probConditionalCoverage[risk] = {}
            for program in self.const.programList:
                ageGroup.probConditionalCoverage[risk][program] = {}
                fracCovered = self.previousCov[program]
                OR = self.project.ORprograms[risk][program][age]
                pn, pc = self._solveQuadratic(OR, fracCovered, fracStunted)
                ageGroup.probConditionalCoverage[risk][program]['covered'] = pc
                ageGroup.probConditionalCoverage[risk][program]['not covered'] = pn

    def _setProbAnaemicIfCovered(self):
        risk = 'Anaemia'
        for ageGroup in self.ageGroups:
            age = ageGroup.age
            fracAnaemic = sum(ageGroup.anaemiaDist[cat] for cat in self.const.anaemicList)
            ageGroup.probConditionalCoverage[risk] = {}
            for program in self.const.programList:
                ageGroup.probConditionalCoverage[risk][program] = {}
                fracCovered = self.previousCov[program]
                if self.project.RRprograms[risk].get(program) is not None:
                    RR = self.project.RRprograms[risk][program][age]
                    pn = fracAnaemic / (RR * fracCovered + (1. - fracCovered))
                    pc = RR * pn
                else:  # OR
                    OR = self.project.ORprograms[risk][program][age]
                    pn, pc = self._solveQuadratic(OR, fracCovered, fracAnaemic)
                ageGroup.probConditionalCoverage[risk][program]['covered'] = pc
                ageGroup.probConditionalCoverage[risk][program]['not covered'] = pn

    def _setProbCorrectlyBreastfedIfCovered(self):
        risk = 'Breastfeeding'
        for ageGroup in self.ageGroups:
            age = ageGroup.age
            ageGroup.probConditionalCoverage[risk] = {}
            fracAppropriate = ageGroup.bfDist[ageGroup.correctBFpractice]
            for program in self.const.programList:
                ageGroup.probConditionalCoverage[risk][program] = {}
                OR = self.project.ORappropriateBFprogram[program][age]
                fracCovered = self.previousCov[program]
                pn, pc = self._solveQuadratic(OR, fracCovered, fracAppropriate)
                ageGroup.probConditionalCoverage[risk][program]['covered'] = pc
                ageGroup.probConditionalCoverage[risk][program]['not covered'] = pn

    def _setProbWastedIfCovered(self):
        for wastingCat in self.const.wastedList:
            for ageGroup in self.ageGroups:
                ageGroup.probConditionalCoverage[wastingCat] = {}
                age = ageGroup.age
                fracThisCatAge = ageGroup.wastingDist[wastingCat]
                for program in self.const.programList:
                    OR = self.project.ORwastingProgram[wastingCat][program][age]
                    fracCovered = self.previousCov[program]
                    pn, pc = self._solveQuadratic(OR, fracCovered, fracThisCatAge)
                    ageGroup.probConditionalCoverage[wastingCat][program] = {}
                    ageGroup.probConditionalCoverage[wastingCat][program]['covered'] = pc
                    ageGroup.probConditionalCoverage[wastingCat][program]['not covered'] = pn

    def _setProbConditionalDiarrhoea(self): # TODO: this is more general version of two following methods
        risks = ['Stunting', 'Anaemia']
        for ageGroup in self.ageGroups:
            for risk in risks:
                ageGroup.probConditionalDiarrhoea[risk] = {}
                cats = self.project.riskCategories[risk]
                middle = len(cats) / 2
                relevantCats = cats[middle:] # assumes specific order and length
                dist = ageGroup.riskDists[risk]
                Z0 = ageGroup._getZa()
                Zt = Z0 # true for initialisation
                beta = ageGroup._getFracDiarrhoea(Z0, Zt)
                if risk == 'Anaemia':  # anaemia only caused by severe diarrhea
                    Yt = Zt * self.project.demographics['fraction severe diarrhoea']
                else:
                    Yt = Zt
                AO = ageGroup._getAverageOR(Yt, risk)
                fracDiarrhoea = sum(beta[bfCat] * ageGroup.bfDist[bfCat] for bfCat in self.const.bfList)
                fracImpactedThisAge = sum(dist[cat] for cat in relevantCats)
                pn, pc = self._solveQuadratic(AO, fracDiarrhoea, fracImpactedThisAge)
                ageGroup.probConditionalDiarrhoea[risk]['diarrhoea'] = pc
                ageGroup.probConditionalDiarrhoea[risk]['no diarrhoea'] = pn

    def _setProbStuntedIfDiarrhoea(self):
        risk = 'Stunting'
        for ageGroup in self.ageGroups:
            ageGroup.probConditionalDiarrhoea[risk] = {}
            Z0 = ageGroup._getZa()
            Zt = Z0 # true for initialisation
            beta = ageGroup._getFracDiarrhoea(Z0, Zt)
            AO = ageGroup._getAverageOR(Zt, risk)
            fracDiarrhoea = sum(beta[bfCat] * ageGroup.bfDist[bfCat] for bfCat in self.const.bfList)
            fracImpactedThisAge = sum(ageGroup.stuntingDist[cat] for cat in self.const.stuntedList)
            pn, pc = self._solveQuadratic(AO, fracDiarrhoea, fracImpactedThisAge)
            ageGroup.probConditionalDiarrhoea[risk]['diarrhoea'] = pc
            ageGroup.probConditionalDiarrhoea[risk]['no diarrhoea'] = pn

    def _setProbAnaemicIfDiarrhoea(self):
        risk = 'Anaemia'
        for ageGroup in self.ageGroups:
            ageGroup.probConditionalDiarrhoea[risk] = {}
            Z0 = ageGroup._getZa()
            Zt = Z0 # true for initialisation
            beta = ageGroup._getFracDiarrhoea(Z0, Zt)
            Yt = Zt * self.project.demographics['fraction severe diarrhoea']
            AO = ageGroup._getAverageOR(Yt, risk)
            fracDiarrhoea = sum(beta[bfCat] * ageGroup.bfDist[bfCat] for bfCat in self.const.bfList)
            fracImpactedThisAge = sum(ageGroup.anaemiaDist[cat] for cat in self.const.anaemicList)
            pn, pc = self._solveQuadratic(AO, fracDiarrhoea, fracImpactedThisAge)
            ageGroup.probConditionalDiarrhoea[risk]['diarrhoea'] = pc
            ageGroup.probConditionalDiarrhoea[risk]['no diarrhoea'] = pn

    def _setProbWastedIfDiarrhoea(self):
        for ageGroup in self.ageGroups:
            Z0 = ageGroup._getZa()
            Zt = Z0 # true for initialisation
            beta = ageGroup._getFracDiarrhoea(Z0, Zt)
            for wastingCat in self.const.wastedList:
                A0 = ageGroup._getAverageOR(Zt, wastingCat)
                ageGroup.probConditionalDiarrhoea[wastingCat] = {}
                fracDiarrhoea = sum(beta[bfCat] * ageGroup.bfDist[bfCat] for bfCat in self.const.bfList)
                fracThisCat = ageGroup.wastingDist[wastingCat]
                pn, pc = self._solveQuadratic(A0, fracDiarrhoea, fracThisCat)
                ageGroup.probConditionalDiarrhoea[wastingCat]['no diarrhoea'] = pn
                ageGroup.probConditionalDiarrhoea[wastingCat]['diarrhoea'] = pc

    def _setProbStuntedAtBirth(self):
        """Sets the probabilty of stunting conditional on birth outcome"""
        newborns = self.ageGroups[0]
        coeffs = self._getBirthStuntingQuarticCoefficients()
        p0 = self._getBaselineProbabilityViaQuartic(coeffs)
        probStuntedAtBirth = {}
        probStuntedAtBirth['Term AGA'] = p0
        for BO in ["Pre-term SGA","Pre-term AGA","Term SGA"]:
            OR = self.const.ORconditionBirth['stunting'][BO]
            probStuntedAtBirth[BO] = p0*OR / (1.-p0+OR*p0)
            pi = probStuntedAtBirth[BO]
            if(pi<0. or pi>1.):
                raise ValueError("probability of stunting at birth, at outcome %s, is out of range (%f)"%(BO, pi))
        newborns.probRiskAtBirth['Stunting'] = probStuntedAtBirth

    def _setProbWastedAtBirth(self):
        newborns = self.ageGroups[0]
        probWastedAtBirth = {}
        for wastingCat in self.const.wastedList:
            coEffs = self._getBirthWastingQuarticCoefficients(wastingCat)
            p0 = self._getBaselineProbabilityViaQuartic(coEffs)
            probWastedAtBirth[wastingCat] = {}
            probWastedAtBirth[wastingCat]['Term AGA'] = p0
            for birthOutcome in ["Pre-term SGA","Pre-term AGA","Term SGA"]:
                probWastedAtBirth[wastingCat][birthOutcome] = {}
                OR = self.project.ORconditionBirth[wastingCat][birthOutcome]
                probWastedAtBirth[wastingCat][birthOutcome] = p0*OR / (1.-p0+OR*p0)
                pi = p0*OR / (1.-p0+OR*p0)
                if(pi<0. or pi>1.):
                    raise ValueError("probability of wasting at birth, at outcome %s, is out of range (%f)"%(birthOutcome, pi))
        newborns.probRiskAtBirth['Wasting'] = probWastedAtBirth

    def _getBirthStuntingQuarticCoefficients(self):
        newborns = self.ageGroups[0]
        OR = [1.]*4
        OR[0] = 1.
        OR[1] = self.const.ORstuntingBO["Term SGA"]
        OR[2] = self.const.ORstuntingBO["Pre-term AGA"]
        OR[3] = self.const.ORstuntingBO["Pre-term SGA"]
        FracBO = [0.]*4
        FracBO[1] = newborns.birthDist["Term SGA"]
        FracBO[2] = newborns.birthDist["Pre-term AGA"]
        FracBO[3] = newborns.birthDist["Pre-term SGA"]
        FracBO[0] = 1. - sum(FracBO[1:3])
        fracStunted = newborns.getStuntedFrac()
        # [i] will refer to the three non-baseline birth outcomes
        A = FracBO[0]*(OR[1]-1.)*(OR[2]-1.)*(OR[3]-1.)
        B = (OR[1]-1.)*(OR[2]-1.)*(OR[3]-1.) * ( \
            sum( FracBO[0] / (OR[i]-1.)         for i in (1,2,3)) + \
            sum( OR[i] * FracBO[i] / (OR[i]-1.) for i in (1,2,3)) - \
            fracStunted )
        C = sum( FracBO[0] * (OR[i]-1.)         for i in (1,2,3)) + \
            sum( OR[i] * FracBO[i] * ((OR[1]-1.)+(OR[2]-1.)+(OR[3]-1.)-(OR[i]-1.)) for i in (1,2,3) ) - \
            sum( fracStunted*(OR[1]-1.)*(OR[2]-1.)*(OR[3]-1.)/(OR[i]-1.) for i in (1,2,3))
        D = FracBO[0] + \
            sum( OR[i] * FracBO[i] for i in (1,2,3)) - \
            sum( fracStunted * (OR[i]-1.) for i in (1,2,3))
        E = -fracStunted
        return [A,B,C,D,E]

    def _getBirthWastingQuarticCoefficients(self, wastingCat):
        newborns = self.ageGroups[0]
        FracBO = [0.]*4
        FracBO[1] = newborns.birthDist["Term SGA"]
        FracBO[2] = newborns.birthDist["Pre-term AGA"]
        FracBO[3] = newborns.birthDist["Pre-term SGA"]
        FracBO[0] = 1. - sum(FracBO[1:3])
        OR = [1.]*4
        OR[0] = 1.
        OR[1] = self.const.ORconditionBirth[wastingCat]["Term SGA"]
        OR[2] = self.const.ORconditionBirth[wastingCat]["Pre-term AGA"]
        OR[3] = self.const.ORconditionBirth[wastingCat]["Pre-term SGA"]
        fracWasted = newborns.getWastedFrac(wastingCat)
        # [i] will refer to the three non-baseline birth outcomes
        A = FracBO[0]*(OR[1]-1.)*(OR[2]-1.)*(OR[3]-1.)
        B = (OR[1]-1.)*(OR[2]-1.)*(OR[3]-1.) * ( \
            sum( FracBO[0] / (OR[i]-1.)         for i in (1,2,3)) + \
            sum( OR[i] * FracBO[i] / (OR[i]-1.) for i in (1,2,3)) - \
            fracWasted )
        C = sum( FracBO[0] * (OR[i]-1.)         for i in (1,2,3)) + \
            sum( OR[i] * FracBO[i] * ((OR[1]-1.)+(OR[2]-1.)+(OR[3]-1.)-(OR[i]-1.)) for i in (1,2,3) ) - \
            sum( fracWasted*(OR[1]-1.)*(OR[2]-1.)*(OR[3]-1.)/(OR[i]-1.) for i in (1,2,3))
        D = FracBO[0] + \
            sum( OR[i] * FracBO[i] for i in (1,2,3)) - \
            sum( fracWasted * (OR[i]-1.) for i in (1,2,3))
        E = -fracWasted
        return [A,B,C,D,E]

    def _getBaselineProbabilityViaQuartic(self, coEffs):
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
        if self._evalQuartic(p0min, coEffs)==0:
            baselineProbability = p0min
            return baselineProbability
        if self._evalQuartic(p0max, coEffs)==0:
            baselineProbability = p0max
            return baselineProbability
        PositiveAtMin = self._evalQuartic(p0min, coEffs)>0
        PositiveAtMax = self._evalQuartic(p0max, coEffs)>0
        if(PositiveAtMin == PositiveAtMax):
            raise ValueError("ERROR: Quartic function evaluated at 0 & 1 both on the same side")
        while interval > tolerance:
            p0x = (p0max+p0min)/2.
            PositiveAtP0 = self._evalQuartic(p0x, coEffs)>0
            if(PositiveAtP0 == PositiveAtMin):
                p0min = p0x
                PositiveAtMin = self._evalQuartic(p0min, coEffs)>0
            else:
                p0max = p0x
                PositiveAtMax = self._evalQuartic(p0max, coEffs)>0
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

    def _evalQuartic(self, p0, coEffs):
        from math import pow
        A,B,C,D,E = coEffs
        return A*pow(p0,4) + B*pow(p0,3) + C*pow(p0,2) + D*p0 + E

    def _setProgramEffectiveness(self):
        for ageGroup in self.ageGroups:
            age = ageGroup.age
            ageGroup.programEffectiveness = self.project.childPrograms[age]

    def _setAnnualPrevChange(self):
        from numpy import polyfit, isfinite, array
        for risk in ['Stunting', 'Wasting', 'Anaemia']:
            for ageGroup in self.ageGroups:
                age = ageGroup.age
                annualPrev = self.project.annualPrev[risk][age]
                years = array(annualPrev.keys())
                prev = array(annualPrev.values())
                notNan = isfinite(years) & isfinite(prev)
                if sum(notNan) <= 1: # static data
                    ageGroup.annualPrevChange[risk] = 1
                else:
                    linReg = polyfit(years[notNan],prev[notNan],1)
                    ageGroup.annualPrevChange[risk] = 1 + linReg[0]

    def _setCorrectBFpractice(self):
        for ageGroup in self.ageGroups:
            age = ageGroup.age
            ageGroup.correctBFpractice = self.project.correctBF[age]

class PregnantWomen(Population):
    def __init__(self, name, project, constants):
        super(PregnantWomen, self).__init__(name, project, constants)
        self.ageGroups = []
        self._makePopSizes()
        self._makeBoxes()
        self._setPWReferenceMortality()
        self._updateMortalityRates()
        self._setProgramEffectiveness()
        self._setAnnualPrevChange()

    def getTotalPopulation(self):
        return sum(ageGroup.getAgeGroupPopulation() for ageGroup in self.ageGroups)

    def getTotalNumberAnaemic(self):
        return sum(ageGroup.getAgeGroupNumberAnaemic() for ageGroup in self.ageGroups)

    def getTotalFracAnaemic(self):
        totalAnaemia = self.getTotalNumberAnaemic()
        totalPop = self.getTotalPopulation()
        return totalAnaemia / totalPop

    ##### DATA WRANGLING ######

    def _setProgramEffectiveness(self):
        for ageGroup in self.ageGroups:
            age = ageGroup.age
            ageGroup.programEffectiveness = self.project.PWprograms[age]

    def _setAnnualPrevChange(self):
        from numpy import polyfit, isfinite, array
        for risk in ['Anaemia']:
            for ageGroup in self.ageGroups:
                age = ageGroup.age
                annualPrev = self.project.annualPrev[risk][age]
                years = array(annualPrev.keys())
                prev = array(annualPrev.values())
                notNan = isfinite(years) & isfinite(prev)
                if sum(notNan) <= 1: # static data
                    ageGroup.annualPrevChange[risk] = 1
                else:
                    linReg = polyfit(years[notNan],prev[notNan],1)
                    ageGroup.annualPrevChange[risk] = 1 + linReg[0]

    def _setConditionalProbabilities(self):
        self._setProbAnaemicIfCovered()

    def _makePopSizes(self):
        PWpop = self.project.populationByAge
        self.popSizes = {age:pop for age, pop in PWpop.iteritems()}

    def _makeBoxes(self):
        for idx in range(len(self.const.PWages)):
            age = self.const.PWages[idx]
            popSize = self.popSizes[age]
            boxes = {}
            anaemiaDist = self.anaemiaDist[age]
            ageingRate = self.const.womenAgeingRates[idx]
            for anaemiaCat in self.const.anaemiaList:
                thisPop = popSize * anaemiaDist[anaemiaCat]
                boxes[anaemiaCat] = Box(thisPop)
            self.ageGroups.append(PWAgeGroup(age, popSize, boxes, anaemiaDist, ageingRate, self.const))

    def _setPWReferenceMortality(self):
        #Equation is:  LHS = RHS * X
        #we are solving for X
        # Calculate RHS for each age and cause
        RHS = {}
        for age in self.const.PWages:
            RHS[age] = {}
            for cause in self.project.causesOfDeath:
                RHS[age][cause] = 0.
                for anaemiaCat in self.const.anaemiaList:
                    t1 = self.anaemiaDist[age][anaemiaCat]
                    t2 = self.project.RRdeath['Anaemia'][cause][anaemiaCat][age]
                    RHS[age][cause] += t1 * t2
        # get age populations
        agePop = [age.getAgeGroupPopulation() for age in self.ageGroups]
        # Correct raw mortality for units (per 1000 live births)
        liveBirths = self.project.demographics['number of live births']
        # The following assumes we only have a single mortality rate for PW
        mortalityRate = self.project.mortalityRates['maternal mortality']
        mortalityCorrected = {}
        for index in range(len(self.const.PWages)):
            age = self.const.PWages[index]
            if index == 0:
                mortalityCorrected[age] = (mortalityRate * liveBirths / 1000.) * (4. / 34.) / agePop[index]
            else:
                mortalityCorrected[age] = (mortalityRate * liveBirths / 1000.) * (9. / 34.) / agePop[index]
        # Calculate LHS for each age and cause of death then solve for X
        for ageGroup in self.ageGroups:
            age = ageGroup.age
            ageGroup.referenceMortality = {}
            for cause in self.project.causesOfDeath:
                LHS_age_cause = mortalityCorrected[age] * self.project.deathDist[cause][age]
                ageGroup.referenceMortality[cause] = LHS_age_cause / RHS[age][cause]

    def _updateMortalityRates(self):
        for ageGroup in self.ageGroups:
            age = ageGroup.age
            for anaemiaCat in self.const.anaemiaList:
                count = 0
                for cause in self.project.causesOfDeath:
                    t1 = ageGroup.referenceMortality[cause]
                    t2 = self.project.RRdeath['Anaemia'][cause][anaemiaCat][age]
                    count += t1 * t2
                ageGroup.boxes[anaemiaCat].mortalityRate = count

    def _setProbAnaemicIfCovered(self):
        risk = 'Anaemia'
        for ageGroup in self.ageGroups:
            age = ageGroup.age
            ageGroup.probConditionalCoverage[risk] = {}
            for program in self.const.programList:
                ageGroup.probConditionalCoverage[risk][program] = {}
                fracCovered = self.previousCov[program]
                fracImpacted = sum(ageGroup.anaemiaDist[cat] for cat in self.const.anaemicList)
                if self.project.ORprograms[risk].get(program) is None:
                    RR = self.project.RRprograms[risk][program][age]
                    pn = fracImpacted / (RR * fracCovered + (1. - fracCovered))
                    pc = RR * pn
                else:
                    OR = self.project.ORprograms[risk][program][age]
                    pn, pc = self._solveQuadratic(OR, fracCovered, fracImpacted)
                ageGroup.probConditionalCoverage[risk][program]['covered'] = pc
                ageGroup.probConditionalCoverage[risk][program]['not covered'] = pn

class NonPregnantWomen(Population):
    def __init__(self, name, project, constants):
        super(NonPregnantWomen, self).__init__(name, project, constants)
        self.ageGroups = []
        self._makePopSizes()
        self._makeBoxes()
        self._setAnnualPrevChange()

    def getTotalPopulation(self):
        return sum(ageGroup.getAgeGroupPopulation() for ageGroup in self.ageGroups)

    def getTotalNumberAnaemic(self):
        return sum(ageGroup.getAgeGroupNumberAnaemic() for ageGroup in self.ageGroups)

    def getTotalFracAnaemic(self):
        totalAnaemia = self.getTotalNumberAnaemic()
        totalPop = self.getTotalPopulation()
        return totalAnaemia / totalPop

    ##### DATA WRANGLING ######

    def _setConditionalProbabilities(self):
        self._setProbAnaemicIfCovered()

    def _makePopSizes(self):
        WRApop = self.project.populationByAge
        self.popSizes = {age:pop for age, pop in WRApop.iteritems()}

    def _makeBoxes(self):
        for age in self.const.WRAages:
            popSize = self.popSizes[age]
            boxes = {}
            anaemiaDist = self.anaemiaDist[age]
            for anaemiaCat in self.const.anaemiaList:
                thisPop = popSize * anaemiaDist[anaemiaCat]
                boxes[anaemiaCat] = Box(thisPop)
            self.ageGroups.append(NonPWAgeGroup(age, popSize, boxes, anaemiaDist, self.project.birthDist,
                                                self.project.birthAgeDist, self.project.birthIntervalDist, self.const))

    def _setProbAnaemicIfCovered(self):
        risk = 'Anaemia'
        for ageGroup in self.ageGroups:
            age = ageGroup.age
            ageGroup.probConditionalCoverage[risk] = {}
            for program in self.const.programList:
                ageGroup.probConditionalCoverage[risk][program] = {}
                fracCovered = self.previousCov[program]
                fracImpacted = sum(ageGroup.anaemiaDist[cat] for cat in self.const.anaemicList)
                if self.project.ORprograms[risk].get(program) is None:
                    RR = self.project.RRprograms[risk][program][age]
                    pn = fracImpacted / (RR * fracCovered + (1. - fracCovered))
                    pc = RR * pn
                else:
                    OR = self.project.ORprograms[risk][program][age]
                    pn, pc = self._solveQuadratic(OR, fracCovered, fracImpacted)
                ageGroup.probConditionalCoverage[risk][program]['covered'] = pc
                ageGroup.probConditionalCoverage[risk][program]['not covered'] = pn

    def _setBirthPregnancyInfo(self, coverage):
        self._updateFracPregnancyAverted(coverage)
        numPregnant = self.const.demographics['number of pregnant women']
        numWRA = sum(pop for key, pop in self.project.populationByAge.iteritems() if 'WRA' in key)
        rate = numPregnant/numWRA/(1.- self.fracPregnancyAverted)
        # reduce rate by % difference between births and pregnancies to get birth rate
        projectedBirths = self.const.popProjections['number of births']
        projectedPWpop = self.const.popProjections['pregnant women']
        percentDiff = [ai/bi for ai,bi in zip(projectedBirths, projectedPWpop)]
        averagePercentDiff = sum(percentDiff) / float(len(percentDiff))
        self.pregnancyRate = rate
        self.birthRate = averagePercentDiff * rate

    def _updateFracPregnancyAverted(self, coverage):
        self.fracPregnancyAverted = sum(self.const.famPlanMethods[prog]['Effectiveness'] *
            self.const.famPlanMethods[prog]['Distribution'] * coverage
            for prog in self.const.famPlanMethods.iterkeys())

    def _setAnnualPrevChange(self):
        from numpy import polyfit, isfinite, array
        for risk in ['Anaemia']:
            for ageGroup in self.ageGroups:
                age = ageGroup.age
                annualPrev = self.project.annualPrev[risk][age]
                years = array(annualPrev.keys())
                prev = array(annualPrev.values())
                notNan = isfinite(years) & isfinite(prev)
                if sum(notNan) <= 1: # static data
                    ageGroup.annualPrevChange[risk] = 1
                else:
                    linReg = polyfit(years[notNan],prev[notNan],1)
                    ageGroup.annualPrevChange[risk] = 1 + linReg[0]


def setUpPopulations(project, constants):
    children = Children('Children', project, constants)
    pregnantWomen = PregnantWomen('Pregnant women', project, constants)
    nonPregnantWomen = NonPregnantWomen('Non-pregnant women', project, constants)
    return [children, pregnantWomen, nonPregnantWomen]