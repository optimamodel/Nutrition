from utils import solve_quad, restratify
from copy import deepcopy as dcp
from math import pow
from numpy import sqrt, isnan, polyfit, isfinite, array

class Box:
    def __init__(self, populationSize):
        self.populationSize = populationSize
        self.mortalityRate = None
        self.cumulativeDeaths = 0

class NonPWAgeGroup:
    def __init__(self, age, populationSize, boxes, anaemiaDist, birthOutcomeDist, birthAgeDist, birthIntervalDist, settingsants):
        self.age = age
        # self.populationSize = populationSize
        self.boxes = dcp(boxes)
        self.anaemiaDist = dcp(anaemiaDist)
        self.birthOutcomeDist = dcp(birthOutcomeDist)
        self.birthAgeDist = dcp(birthAgeDist)
        self.birthIntervalDist = dcp(birthIntervalDist)
        self.settings = settingsants
        self.probConditionalCoverage = {}
        self.annualPrevChange = {}
        self.set_update_storage()
        self._setBirthProbs()

    def set_update_storage(self):
        self.anaemiaUpdate = 1.
        self.birthAgeUpdate = {}
        for BA in self.settings.birthAges:
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
                RRAO = self.settings.RRageOrder[ageOrder][outcome]
                for interval, fracInterval in self.birthIntervalDist.iteritems():
                    RRinterval = self.settings.RRinterval[interval][outcome]
                    thisSum += fracAO * RRAO * fracInterval * RRinterval
            self.birthProb[outcome] = thisSum

    def getAgeGroupPopulation(self):
        return sum(self.boxes[anaemiaCat].populationSize for anaemiaCat in self.settings.anaemiaList)

    def getAgeGroupNumberAnaemic(self):
        for anaemiaCat in self.settings.anaemicList:
            return self.boxes[anaemiaCat].populationSize

    def getFracAnaemic(self):
        return self.getAgeGroupNumberAnaemic() / self.getAgeGroupPopulation()

    def getFracRisk(self, risk):
        return self.getFracAnaemic()

    def updateAnaemiaDist(self):
        totalPop = self.getAgeGroupPopulation()
        for anaemiaCat in self.settings.anaemiaList:
            self.data.anaemiaDist[anaemiaCat] = self.boxes[anaemiaCat].populationSize / totalPop

    def distrib_pop(self):
        for anaemiaCat in self.settings.anaemiaList:
            self.boxes[anaemiaCat].populationSize = self.data.anaemiaDist[anaemiaCat] * self.getAgeGroupPopulation()

class PWAgeGroup:
    def __init__(self, age, populationSize, boxes, anaemiaDist, ageingRate, settingsants):
        self.age = age
        # self.populationSize = populationSize
        self.boxes = dcp(boxes)
        self.anaemiaDist = dcp(anaemiaDist)
        self.ageingRate = ageingRate
        self.settings = settingsants
        self.probConditionalCoverage = {}
        self.annualPrevChange = {}
        self.set_update_storage()

    def set_update_storage(self):
        self.anaemiaUpdate = 1.
        # this update will impact Newborn age group
        self.birthUpdate = {}
        for BO in self.settings.birthOutcomes:
            self.birthUpdate[BO] = 1.
        self.mortalityUpdate = {}
        for cause in self.settings.causesOfDeath:
            self.mortalityUpdate[cause] = 1.

    def getAgeGroupPopulation(self):
        return sum(self.boxes[anaemiaCat].populationSize for anaemiaCat in self.settings.anaemiaList)

    def getAgeGroupNumberAnaemic(self):
        for anaemiaCat in self.settings.anaemicList:
            return self.boxes[anaemiaCat].populationSize

    def getFracAnaemic(self):
        return self.getAgeGroupNumberAnaemic() / self.getAgeGroupPopulation()

    def getFracRisk(self, risk):
        return self.getFracAnaemic()

    def updateAnaemiaDist(self):
        totalPop = self.getAgeGroupPopulation()
        for anaemiaCat in self.settings.anaemiaList:
            self.data.anaemiaDist[anaemiaCat] = self.boxes[anaemiaCat].populationSize / totalPop

    def distrib_pop(self):
        for anaemiaCat in self.settings.anaemiaList:
            self.boxes[anaemiaCat].populationSize = self.data.anaemiaDist[anaemiaCat] * self.getAgeGroupPopulation()

class ChildAgeGroup(object):
    def __init__(self, age, populationSize, boxes, anaemiaDist, incidences, stuntingDist, wastingDist, BFdist,
                 ageingRate, settingsants):
        self.age = age
        # self.populationSize = populationSize
        self.boxes = dcp(boxes)
        self.anaemiaDist = dcp(anaemiaDist)
        self.stuntingDist = dcp(stuntingDist)
        self.wastingDist = dcp(wastingDist)
        self.bfDist = dcp(BFdist)
        self.incidences = dcp(incidences)
        self.settings = settingsants
        self.correctBF = self.settings.correctBF[age]
        self.incorrectBF = list(set(self.settings.bfList) - {self.correctBF})
        self.ageingRate = ageingRate
        self.probConditionalCoverage = {}
        self.probConditionalDiarrhoea = {}
        self.probConditionalStunting = {}
        self.programEffectiveness = {}
        self.annualPrevChange = {}
        self.set_update_storage()
        self._updatesForAgeingAndBirths()

    def _updatesForAgeingAndBirths(self):
        """
        Stunting & wasting have impact on births and ageing, which needs to be adjusted at each time step
        :return:
        """
        self.continuedStuntingImpact = 1.
        self.continuedWastingImpact = {}
        for wastingCat in self.settings.wastedList:
            self.continuedWastingImpact[wastingCat] = 1.

    def set_update_storage(self):
        # storing updates
        self.stuntingUpdate = 1.
        self.anaemiaUpdate = 1.
        self.bfUpdate = {}
        self.diarrhoeaUpdate = {}
        self.bfPracticeUpdate = self.data.bfDist[self.correctBF]
        for risk in ['Stunting', 'Anaemia'] + self.settings.wastedList:
            self.bfUpdate[risk] = 1.
        self.mortalityUpdate = {}
        for cause in self.settings.causesOfDeath:
            self.mortalityUpdate[cause] = 1.
        self.diarrhoeaIncidenceUpdate = 1.
        self.diarrhoeaUpdate = {}
        for risk in self.settings.wastedList + ['Stunting', 'Anaemia']:
            self.diarrhoeaUpdate[risk] = 1.
        self.wastingPreventionUpdate = {}
        self.wastingTreatmentUpdate = {}
        for wastingCat in self.settings.wastedList:
            self.wastingPreventionUpdate[wastingCat] = 1.
            self.wastingTreatmentUpdate[wastingCat] = 1.

    ###### POPULATION CALCULATIONS ######
    # TODO: would like to re-write for better implementation

    def getAgeGroupPopulation(self):
        totalPop = 0
        for stuntingCat in self.settings.stuntingList:
            for wastingCat in self.settings.wastingList:
                for bfCat in self.settings.bfList:
                    for anaemiaCat in self.settings.anaemiaList:
                        totalPop += self.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize
        return totalPop

    def getAgeGroupNumberStunted(self):
        numStunted = 0
        for stuntingCat in self.settings.stuntedList:
            for wastingCat in self.settings.wastingList:
                for bfCat in self.settings.bfList:
                    for anaemiaCat in self.settings.anaemiaList:
                        numStunted += self.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize
        return numStunted

    def getAgeGroupNumberNotStunted(self):
        numNotStunted = 0
        for stuntingCat in self.settings.notStuntedList:
            for wastingCat in self.settings.wastingList:
                for bfCat in self.settings.bfList:
                    for anaemiaCat in self.settings.anaemiaList:
                        numNotStunted += self.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize
        return numNotStunted

    def getAgeGroupNumberNotAnaemic(self):
        numNotAnaemic = 0
        for stuntingCat in self.settings.stuntingList:
            for wastingCat in self.settings.wastingList:
                for bfCat in self.settings.bfList:
                    for anaemiaCat in self.settings.nonAnaemicList:
                        numNotAnaemic += self.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize
        return numNotAnaemic

    def getAgeGroupNumberNotWasted(self):
        numNotWasted = 0
        for stuntingCat in self.settings.stuntingList:
            for wastingCat in self.settings.nonWastedList:
                for bfCat in self.settings.bfList:
                    for anaemiaCat in self.settings.anaemiaList:
                        numNotWasted += self.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize
        return numNotWasted

    def getAgeGroupNumberThreeConditions(self):
        numWithThree = 0
        for stuntingCat in self.settings.stuntedList:
            for wastingCat in self.settings.wastedList:
                for bfCat in self.settings.bfList:
                    for anaemiaCat in self.settings.anaemicList:
                        numWithThree += self.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize
        return numWithThree

    def getAgeGroupNumberHealthy(self):
        numHealthly = 0
        for stuntingCat in self.settings.notStuntedList:
            for wastingCat in self.settings.nonWastedList:
                for bfCat in self.settings.bfList:
                    for anaemiaCat in self.settings.nonAnaemicList:
                        numHealthly += self.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize
        return numHealthly

    def getAgeGroupNumberNonStuntedNonWasted(self):
        numNonStuntedNonWasted = 0
        for stuntingCat in self.settings.notStuntedList:
            for wastingCat in self.settings.nonWastedList:
                for bfCat in self.settings.bfList:
                    for anaemiaCat in self.settings.anaemiaList:
                        numNonStuntedNonWasted += self.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize
        return numNonStuntedNonWasted

    def getStuntingDistribution(self):
        totalPop = self.getAgeGroupPopulation()
        returnDict = {}
        for stuntingCat in self.settings.stuntingList:
            returnDict[stuntingCat] = 0.
            for wastingCat in self.settings.wastingList:
                for breastfeedingCat in self.settings.bfList:
                    for anemiaStatus in self.settings.anaemiaList:
                        returnDict[stuntingCat] += self.boxes[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus].populationSize / totalPop
        return returnDict

    def getWastingDistribution(self):
        totalPop = self.getAgeGroupPopulation()
        returnDict = {}
        for wastingCat in self.settings.wastingList:
            returnDict[wastingCat] = 0.
            for stuntingCat in self.settings.stuntingList:
                for breastfeedingCat in self.settings.bfList:
                    for anemiaStatus in self.settings.anaemiaList:
                        returnDict[wastingCat] += self.boxes[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus].populationSize / totalPop
        return returnDict

    def getAgeGroupNumberAnaemic(self):
        numAnaemic = 0
        for stuntingCat in self.settings.stuntingList:
            for wastingCat in self.settings.wastingList:
                for bfCat in self.settings.bfList:
                    for anaemiaCat in self.settings.anaemicList:
                        numAnaemic += self.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize
        return numAnaemic

    def getAgeGroupNumberWasted(self, wastingCat):
        numWasted = 0
        for stuntingCat in self.settings.stuntingList:
            for bfCat in self.settings.bfList:
                for anaemiaCat in self.settings.anaemiaList:
                    numWasted += self.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize
        return numWasted

    def getCumulativeDeaths(self):
        deaths = 0
        for stuntingCat in self.settings.stuntingList:
            for wastingCat in self.settings.wastingList:
                for bfCat in self.settings.bfList:
                    for anaemiaCat in self.settings.anaemiaList:
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
            return self.data.stuntingDist['high'] + self.data.stuntingDist['moderate']
        elif risk == 'Anaemia':
            return self.data.anaemiaDist['anaemic']

    def getNumberCorrectlyBF(self):
        numCorrect = 0
        for stuntingCat in self.settings.stuntingList:
            for wastingCat in self.settings.wastingList:
                for anaemiaCat in self.settings.anaemiaList:
                    numCorrect += self.boxes[stuntingCat][wastingCat][self.correctBF][anaemiaCat].populationSize
        return numCorrect

    def distrib_pop(self):
        totalPop = self.getAgeGroupPopulation()
        for stuntingCat in self.settings.stuntingList:
            for wastingCat in self.settings.wastingList:
                for bfCat in self.settings.bfList:
                    for anaemiaCat in self.settings.anaemiaList:
                        self.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize = self.data.stuntingDist[stuntingCat] * \
                                                                                                self.data.wastingDist[wastingCat] * \
                                                                                                self.data.bfDist[bfCat] * \
                                                                                                self.data.anaemiaDist[anaemiaCat] * totalPop

    def updateStuntingDist(self):
        totalPop = self.getAgeGroupPopulation()
        for stuntingCat in self.settings.stuntingList:
            self.data.stuntingDist[stuntingCat] = 0
            for wastingCat in self.settings.wastingList:
                for breastfeedingCat in self.settings.bfList:
                    for anemiaStatus in self.settings.anaemiaList:
                        self.data.stuntingDist[stuntingCat] += self.boxes[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus].populationSize / totalPop

    def updateWastingDist(self):
        totalPop = self.getAgeGroupPopulation()
        for wastingCat in self.settings.wastingList:
            self.data.wastingDist[wastingCat] = 0
            for stuntingCat in self.settings.stuntingList:
                for breastfeedingCat in self.settings.bfList:
                    for anaemiaCat in self.settings.anaemiaList:
                        self.data.wastingDist[wastingCat] += self.boxes[stuntingCat][wastingCat][breastfeedingCat][
                                                                  anaemiaCat].populationSize / totalPop
    def updateAnaemiaDist(self):
        totalPop = self.getAgeGroupPopulation()
        for anaemiaCat in self.settings.anaemiaList:
            self.data.anaemiaDist[anaemiaCat] = 0
            for stuntingCat in self.settings.stuntingList:
                for wastingCat in self.settings.wastingList:
                    for breastfeedingCat in self.settings.bfList:
                        self.data.anaemiaDist[anaemiaCat] += self.boxes[stuntingCat][wastingCat][breastfeedingCat][
                                                              anaemiaCat].populationSize / totalPop

    def updateBFDist(self):
        totalPop = self.getAgeGroupPopulation()
        for bfCat in self.settings.bfList:
            self.data.bfDist[bfCat] = 0
            for stuntingCat in self.settings.stuntingList:
                for wastingCat in self.settings.wastingList:
                    for anaemiaCat in self.settings.anaemiaList:
                        self.data.bfDist[bfCat] += self.boxes[stuntingCat][wastingCat][bfCat][
                                                              anaemiaCat].populationSize / totalPop

    def _getFracDiarrhoeaFixedZ(self):
        beta = {}
        RRnot = self.settings.RRdiarrhoea['none'][self.age]
        for bfCat in self.settings.bfList:
            RDa = self.settings.RRdiarrhoea[bfCat][self.age]
            beta[bfCat] = RDa/RRnot
        return beta

    def _getFracDiarrhoea(self, Z0, Zt):
        beta = {}
        RRnot = self.settings.RRdiarrhoea["none"][self.age]
        for bfCat in self.settings.bfList:
            RDa = self.settings.RRdiarrhoea[bfCat][self.age]
            beta[bfCat] = 1. - (RRnot * Z0 - RDa * Zt) / \
                          (RRnot * Z0)
            # RDa * Zt[age] / (RRnot * Z0[age])
        return beta

    def _getZa(self):
        riskSum = self._getDiarrhoeaRiskSum()
        incidence = self.incidences['Diarrhoea']
        return incidence / riskSum

    def _getDiarrhoeaRiskSum(self):
        return sum(self.settings.RRdiarrhoea[bfCat][self.age] * self.data.bfDist[bfCat] for bfCat in self.settings.bfList)

    def _getAverageOR(self, Za, risk):
        RRnot = self.settings.RRdiarrhoea['none'][self.age]
        if risk == 'Stunting':
            OR = self.settings.ORcondition['OR stunting by condition']['Diarrhoea'][self.age]
        elif risk == 'Anaemia':
            OR = self.settings.ORcondition['OR anaemia by condition']['Severe diarrhoea'][self.age]
        elif risk == 'MAM' or risk == 'SAM':
            OR = self.settings.ORcondition['OR '+risk+' by condition']['Diarrhoea'][self.age]
        else:
            print 'risk factor is invalid'
        AO = pow(OR, RRnot * Za * 1./self.ageingRate)
        return AO

    def _updateProbConditionalDiarrhoea(self, Zt):
        # stunting and anaemia
        AO = {}
        for risk in ['Stunting', 'Anaemia']:
            if risk == 'Anaemia':
                AO[risk] = self._getAverageOR(Zt * self.settings.demographics['fraction severe diarrhoea'], risk)
            else:
                AO[risk] = self._getAverageOR(Zt, risk)
            Omega0 = self.probConditionalDiarrhoea[risk]['no diarrhoea']
            self.probConditionalDiarrhoea[risk]['diarrhoea'] = Omega0 * AO[risk] / (1. - Omega0 + AO[risk] * Omega0)
        # wasting cats
        for wastingCat in self.settings.wastedList:
            AO = self._getAverageOR(Zt, wastingCat)
            Omega0 = self.probConditionalDiarrhoea[wastingCat]['no diarrhoea']
            self.probConditionalDiarrhoea[wastingCat]['diarrhoea'] = Omega0 * AO / (1. - Omega0 + AO * Omega0)

class Newborn(ChildAgeGroup):
    def __init__(self, age, populationSize, boxes, anaemiaDist, incidences, stuntingDist, wastingDist, BFdist,
                 ageingRate, settingsants, birthDist):
        """
        This is the <1 month age group, distinguished from the other age groups by birth outcomes, spacing etc etc.
        """
        super(Newborn, self).__init__(age, populationSize, boxes, anaemiaDist, incidences, stuntingDist, wastingDist, BFdist,
                 ageingRate, settingsants)
        self.birthDist = birthDist
        self.probRiskAtBirth = {}
        self.birthUpdate = {}
        for BO in self.settings.birthOutcomes:
            self.birthUpdate[BO] = 1.


# class Population(object):
#     def __init__(self, name, project, settings, default_params):
#         self.name = name
#         self.data = dcp(project) # TODO: may not want to dcp all this -- only really want to get distribution data from project
#         self.settings = settings
#         self.previousCov = None
#         self.populationAreas = self.data.populationAreas
#         self.riskDist = {}
#         self.data.stuntingDist = self.data.riskDistributions['Stunting']
#         self.data.anaemiaDist= self.data.riskDistributions['Anaemia']
#         self.data.bfDist = self.data.riskDistributions['Breastfeeding']
#         self.data.wastingDist = self.data.riskDistributions['Wasting']
#         self.birthDist = self.data.birthDist
#         self.incidences = self.data.incidences
#         self.RRdiarrhoea = self.data.RRdeath['Child diarrhoea']['Diarrhoea incidence']
#         self.ORcondition = self.data.ORcondition
#         self.boxes = {}
#
#     def getDistribution(self, risk):
#         return self.data.riskDistributions[risk]

class Children(object):
    def __init__(self, data, default_params, settings):
        self.name = 'Children'
        self.data = data
        self.default = default_params
        self.settings = settings
        self.age_groups = []
        self._make_pop_sizes()
        self._make_boxes()
        self._set_child_mortality()
        self.update_mortality()
        self._setProgramEffectiveness()
        self._setAnnualPrevChange()
        self._setCorrectBFpractice()
        self._setProbFutureStunting()
        self.set_probstuntedBirth()
        self._setProbWastedBirth()

    ##### DATA WRANGLING ######

    def set_probs(self):
        # self._setCondProbs()
        self._setProbStunted()
        self._setProbAnaemic()
        self._setProbWasted()
        self._setProbBF()
        # self._setProbDia()
        self._setProbStuntedDia()
        self._setProbAnaemiaDia()
        self._setProbWastedDia()

    def _setConditionalDiarrhoea(self):
        self._setProbStuntedDia()
        self._setProbAnaemiaDia()
        self._setProbWastedDia()

    def _make_pop_sizes(self):
        # for children less than 1 year, annual live births
        monthlyBirths = self.data.demographics['number of live births'] / 12.
        popSize = [pop * monthlyBirths for pop in self.settings.childAgeSpans[:3]]
        # children > 1 year, who are not counted in annual 'live births'
        months = sum(self.settings.childAgeSpans[3:])
        popRemainder = self.data.demographics['population U5'] - monthlyBirths * 12.
        monthlyRate = popRemainder/months
        popSize += [pop * monthlyRate for pop in self.settings.childAgeSpans[3:]]
        self.popSizes = {age:pop for age, pop in zip(self.settings.childAges, popSize)}

    def _make_boxes(self):
        for idx in range(len(self.data.childAges)):
            age = self.data.childAges[idx]
            popSize = self.popSizes[age]
            boxes = {}
            stuntingDist = self.data.stuntingDist[age]
            stuntingDist = restratify(sum(stuntingDist[cat] for cat in self.settings.stuntedList))
            anaemiaDist = self.data.anaemiaDist[age]
            wastingDist = self.data.wastingDist[age]
            probWasted = sum(wastingDist[cat] for cat in self.settings.wastedList)
            nonWastingDist = restratify(probWasted)
            for cat in self.settings.nonWastedList:
                wastingDist[cat] = nonWastingDist[cat]
            bfDist = self.data.bfDist[age]
            birthDist = self.birthDist
            incidences = self.data.incidences[age] # TODO: do this adjustment elsewhere, same as restratifying
            incidences = {condition: incidence * self.settings.timestep for condition, incidence in incidences.iteritems()}
            ageingRate = 1./self.settings.childAgeSpans[idx]
            for stuntingCat in self.settings.stuntingList:
                boxes[stuntingCat] = {}
                for wastingCat in self.settings.wastingList:
                    boxes[stuntingCat][wastingCat] = {}
                    for bfCat in self.settings.bfList:
                        boxes[stuntingCat][wastingCat][bfCat] = {}
                        for anaemiaCat in self.settings.anaemiaList:
                            thisPop = popSize * stuntingDist[stuntingCat] * anaemiaDist[anaemiaCat] * \
                                      wastingDist[wastingCat] * bfDist[bfCat]
                            boxes[stuntingCat][wastingCat][bfCat][anaemiaCat] = Box(thisPop)
            if age == '<1 month': # <1 month age group has slightly different functionality
                self.age_groups.append(Newborn(age, popSize, boxes,
                                           anaemiaDist, incidences, stuntingDist, wastingDist, bfDist,
                                                ageingRate, self.settings, birthDist))
            else:
                self.age_groups.append(ChildAgeGroup(age, popSize, boxes,
                                           anaemiaDist, incidences, stuntingDist, wastingDist, bfDist,
                                                ageingRate, self.settings))

    def _set_child_mortality(self):
        # Equation is:  LHS = RHS * X
        # we are solving for X
        # Calculate RHS for each age and cause
        RHS = {}
        for age in self.settings.childAges:
            RHS[age] = {}
            for cause in self.data.causesOfDeath:
                RHS[age][cause] = 0.
                for stuntingCat in self.settings.stuntingList:
                    for wastingCat in self.settings.wastingList:
                        for bfCat in self.settings.bfList:
                            for anaemiaCat in self.settings.anaemiaList:
                                t1 = self.data.stuntingDist[age][stuntingCat]
                                t2 = self.data.wastingDist[age][wastingCat]
                                t3 = self.data.bfDist[age][bfCat]
                                t4 = self.data.anaemiaDist[age][anaemiaCat]
                                t5 = self.default.RRdeath['Stunting'][cause][stuntingCat][age]
                                t6 = self.default.RRdeath['Wasting'][cause][wastingCat][age]
                                t7 = self.default.RRdeath['Breastfeeding'][cause][bfCat][age]
                                t8 = self.default.RRdeath['Anaemia'][cause][anaemiaCat][age]
                                RHS[age][cause] += t1 * t2 * t3 * t4 * t5 * t6 * t7 * t8
        # RHS for newborns only
        age = '<1 month'
        for cause in self.data.causesOfDeath:
            RHS[age][cause] = 0.
            for breastfeedingCat in self.settings.bfList:
                Pbf = self.data.bfDist[age][breastfeedingCat]
                RRbf = self.default.RRdeath['Breastfeeding'][cause][breastfeedingCat][age]
                for birthoutcome in self.settings.birthOutcomes:
                    Pbo = self.birthDist[birthoutcome]
                    RRbo = self.default.RRdeath['Birth outcomes'][cause][birthoutcome]
                    for anemiaStatus in self.settings.anaemiaList:
                        Pan = self.data.anaemiaDist[age][anemiaStatus]
                        RRan = self.default.RRdeath['Anaemia'][cause][anemiaStatus][age]
                        RHS[age][cause] += Pbf * RRbf * Pbo * RRbo * Pan * RRan
        # calculate total mortality by age (corrected for units)
        AgePop = [age.getAgeGroupPopulation() for age in self.age_groups]
        MortalityCorrected = {}
        LiveBirths = self.data.demographics['number of live births']
        Mnew = self.data.mortalityRates['neonatal']
        Minfant = self.data.mortalityRates['infant']
        Mu5 = self.data.mortalityRates['under 5']
        # Newborns
        ageName = self.age_groups[0].age
        m0 = Mnew * LiveBirths / 1000. / AgePop[0]
        MortalityCorrected[ageName] = m0
        # 1-5 months
        ageName = self.age_groups[1].age
        m1 = (Minfant - Mnew) * LiveBirths / 1000. * 5. / 11. / AgePop[1]
        MortalityCorrected[ageName] = m1
        # 6-12 months
        ageName = self.age_groups[2].age
        m2 = (Minfant - Mnew) * LiveBirths / 1000. * 6. / 11. / AgePop[2]
        MortalityCorrected[ageName] = m2
        # 12-24 months
        ageName = self.age_groups[3].age
        m3 = (Mu5 - Minfant) * LiveBirths / 1000. * 1. / 4. / AgePop[3]
        MortalityCorrected[ageName] = m3
        # 24-60 months
        ageName = self.age_groups[4].age
        m4 = (Mu5 - Minfant) * LiveBirths / 1000. * 3. / 4. / AgePop[4]
        MortalityCorrected[ageName] = m4
        # Calculate LHS for each age and cause of death then solve for X
        for age_group in self.age_groups:
            age_group.referenceMortality = {}
            age = age_group.age
            for cause in self.settings.causesOfDeath:
                LHS_age_cause = MortalityCorrected[age] * self.data.deathDist[cause][age]
                age_group.referenceMortality[cause] = LHS_age_cause / RHS[age][cause]

    def update_mortality(self):
        # Newborns first
        age_group = self.age_groups[0]
        age = age_group.age
        for bfCat in self.settings.bfList:
            count = 0.
            for cause in self.data.causesOfDeath:
                Rb = self.default.RRdeath['Breastfeeding'][cause][bfCat][age]
                for outcome in self.settings.birthOutcomes:
                    pbo = age_group.birthDist[outcome]
                    Rbo = self.default.RRdeath['Birth outcomes'][cause][outcome]
                    count += Rb * pbo * Rbo * age_group.referenceMortality[cause]
            for stuntingCat in self.settings.stuntingList:
                for wastingCat in self.settings.wastingList:
                    for anaemiaCat in self.settings.anaemiaList:
                        age_group.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].mortalityRate = count
        # over 1 months
        for age_group in self.age_groups[1:]:
            age = age_group.age
            for stuntingCat in self.settings.stuntingList:
                for wastingCat in self.settings.wastingList:
                    for bfCat in self.settings.bfList:
                        for anaemiaCat in self.settings.anaemiaList:
                            count = 0.
                            for cause in self.data.causesOfDeath:
                                t1 = age_group.referenceMortality[cause]
                                t2 = self.default.RRdeath['Stunting'][cause][stuntingCat][age]
                                t3 = self.default.RRdeath['Wasting'][cause][wastingCat][age]
                                t4 = self.default.RRdeath['Breastfeeding'][cause][bfCat][age]
                                t5 = self.default.RRdeath['Anaemia'][cause][anaemiaCat][age]
                                count += t1 * t2 * t3 * t4 * t5
                            age_group.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].mortalityRate = count

    def getTotalPopulation(self):
        return sum(age_group.getAgeGroupPopulation() for age_group in self.age_groups)

    def getTotalNumberStunted(self):
        return sum(age_group.getAgeGroupNumberStunted() for age_group in self.age_groups)

    def getTotalFracStunted(self):
        totalStunted = self.getTotalNumberStunted()
        totalPop = self.getTotalPopulation()
        return totalStunted / totalPop

    def getTotalNumberAnaemic(self):
        return sum(age_group.getAgeGroupNumberAnaemic() for age_group in self.age_groups)

    def getTotalFracAnaemic(self):
        totalAnaemia = self.getTotalNumberAnaemic()
        totalPop = self.getTotalPopulation()
        return totalAnaemia / totalPop

    def getTotalNumberWasted(self, wastingCat):
        return sum(age_group.getAgeGroupNumberWasted(wastingCat) for age_group in self.age_groups)

    def getTotalFracWasted(self):
        totalWasted = sum(self.getTotalNumberWasted(wastingCat) for wastingCat in self.settings.wastedList)
        totalPop = self.getTotalPopulation()
        return totalWasted / totalPop

    def getFracWastingCat(self, wastingCat):
        totalThisCat = self.getTotalNumberWasted(wastingCat)
        totalPop = self.getTotalPopulation()
        return totalThisCat/totalPop

    def _replaceRiskList(self, index, newList):
        """replaces one risk list in a list of risk lists. index is the position of list to replace """
        alteredList = self.settings.allRisks[:]
        alteredList[index] = newList
        return alteredList

    def _setProbFutureStunting(self):
        """Calculate the probability of stunting given previous stunting between age groups"""
        for indx in range(1, len(self.age_groups)):
            age_group = self.age_groups[indx]
            thisAge = age_group.age
            prevAgeGroup = self.age_groups[indx-1]
            OR = self.data.ORcondition['Stunting progression'][thisAge]
            fracStuntedThisAge = age_group.getStuntedFrac()
            fracStuntedPrev = prevAgeGroup.getStuntedFrac()
            pn, pc = solve_quad(OR, fracStuntedPrev, fracStuntedThisAge)
            age_group.probConditionalStunting['stunted'] = pc
            age_group.probConditionalStunting['not stunted'] = pn

    def _setCondProbs(self): # TODO: this is more general version of the two following methods
        """Set the conditional probabilities of a risk factor (except wasting) given program coverage.
        Note that this value is dependent upon the baseline coverage of the program"""
        risks = [risk for i, risk in enumerate(self.settings.risks) if i !=1 ] # remove wasting
        for risk in risks:
            cats = self.data.riskCategories[risk]
            middle = len(cats) / 2
            relevantCats = cats[middle:] # assumes list is symmetric
            for age_group in self.age_groups:
                age = age_group.age
                dist = age_group.riskDists[risk]
                age_group.probConditionalCoverage[risk] = {}
                for program in self.settings.programList:
                    age_group.probConditionalCoverage[risk][program] = {}
                    fracCovered = self.previousCov[program]
                    fracImpacted = sum(dist[cat] for cat in relevantCats)
                    if self.data.RRprograms[risk].get(program) is not None:
                        RR = self.data.RRprograms[risk][program][age]
                        pn = fracImpacted/(RR*fracCovered + (1.-fracCovered))
                        pc = RR * pn
                    else: # OR
                        OR = self.default.ORprograms[risk][program][age]
                        pn, pc = solve_quad(OR, fracCovered, fracImpacted)
                    age_group.probConditionalCoverage[risk][program]['covered'] = pc
                    age_group.probConditionalCoverage[risk][program]['not covered'] = pn

    def _setProbStunted(self):
        risk = 'Stunting'
        for age_group in self.age_groups:
            age = age_group.age
            fracStunted = sum(age_group.stuntingDist[cat] for cat in self.settings.stuntedList)
            age_group.probConditionalCoverage[risk] = {}
            for program in self.settings.programList:
                age_group.probConditionalCoverage[risk][program] = {}
                fracCovered = self.previousCov[program]
                OR = self.default.ORprograms[risk][program][age]
                pn, pc = solve_quad(OR, fracCovered, fracStunted)
                age_group.probConditionalCoverage[risk][program]['covered'] = pc
                age_group.probConditionalCoverage[risk][program]['not covered'] = pn

    def _setProbAnaemic(self):
        risk = 'Anaemia'
        for age_group in self.age_groups:
            age = age_group.age
            fracAnaemic = sum(age_group.anaemiaDist[cat] for cat in self.settings.anaemicList)
            age_group.probConditionalCoverage[risk] = {}
            for program in self.settings.programList:
                age_group.probConditionalCoverage[risk][program] = {}
                fracCovered = self.previousCov[program]
                if self.default.RRprograms[risk].get(program) is not None:
                    RR = self.default.RRprograms[risk][program][age]
                    pn = fracAnaemic / (RR * fracCovered + (1. - fracCovered))
                    pc = RR * pn
                else:  # OR
                    OR = self.default.ORprograms[risk][program][age]
                    pn, pc = solve_quad(OR, fracCovered, fracAnaemic)
                age_group.probConditionalCoverage[risk][program]['covered'] = pc
                age_group.probConditionalCoverage[risk][program]['not covered'] = pn

    def _setProbBF(self):
        risk = 'Breastfeeding'
        for age_group in self.age_groups:
            age = age_group.age
            age_group.probConditionalCoverage[risk] = {}
            fracAppropriate = age_group.bfDist[age_group.correctBFpractice]
            for program in self.settings.programList:
                age_group.probConditionalCoverage[risk][program] = {}
                OR = self.default.ORappropriateBFprogram[program][age]
                fracCovered = self.previousCov[program]
                pn, pc = solve_quad(OR, fracCovered, fracAppropriate)
                age_group.probConditionalCoverage[risk][program]['covered'] = pc
                age_group.probConditionalCoverage[risk][program]['not covered'] = pn

    def _setProbWasted(self):
        for wastingCat in self.settings.wastedList:
            for age_group in self.age_groups:
                age_group.probConditionalCoverage[wastingCat] = {}
                age = age_group.age
                fracThisCatAge = age_group.wastingDist[wastingCat]
                for program in self.settings.programList:
                    OR = self.default.ORwastingProgram[wastingCat][program][age]
                    fracCovered = self.previousCov[program]
                    pn, pc = solve_quad(OR, fracCovered, fracThisCatAge)
                    age_group.probConditionalCoverage[wastingCat][program] = {}
                    age_group.probConditionalCoverage[wastingCat][program]['covered'] = pc
                    age_group.probConditionalCoverage[wastingCat][program]['not covered'] = pn

    def _setProbDia(self): # TODO: this is more general version of two following methods
        risks = ['Stunting', 'Anaemia']
        for age_group in self.age_groups:
            for risk in risks:
                age_group.probConditionalDiarrhoea[risk] = {}
                cats = self.settings.riskCategories[risk]
                middle = len(cats) / 2
                relevantCats = cats[middle:] # assumes specific order and length
                dist = age_group.riskDists[risk]
                Z0 = age_group._getZa()
                Zt = Z0 # true for initialisation
                beta = age_group._getFracDiarrhoea(Z0, Zt)
                if risk == 'Anaemia':  # anaemia only caused by severe diarrhea
                    Yt = Zt * self.data.demographics['fraction severe diarrhoea']
                else:
                    Yt = Zt
                AO = age_group._getAverageOR(Yt, risk)
                fracDiarrhoea = sum(beta[bfCat] * age_group.bfDist[bfCat] for bfCat in self.settings.bfList)
                fracImpactedThisAge = sum(dist[cat] for cat in relevantCats)
                pn, pc = solve_quad(AO, fracDiarrhoea, fracImpactedThisAge)
                age_group.probConditionalDiarrhoea[risk]['diarrhoea'] = pc
                age_group.probConditionalDiarrhoea[risk]['no diarrhoea'] = pn

    def _setProbStuntedDia(self):
        risk = 'Stunting'
        for age_group in self.age_groups:
            age_group.probConditionalDiarrhoea[risk] = {}
            Z0 = age_group._getZa()
            Zt = Z0 # true for initialisation
            beta = age_group._getFracDiarrhoea(Z0, Zt)
            AO = age_group._getAverageOR(Zt, risk)
            fracDiarrhoea = sum(beta[bfCat] * age_group.bfDist[bfCat] for bfCat in self.settings.bfList)
            fracImpactedThisAge = sum(age_group.stuntingDist[cat] for cat in self.settings.stuntedList)
            pn, pc = solve_quad(AO, fracDiarrhoea, fracImpactedThisAge)
            age_group.probConditionalDiarrhoea[risk]['diarrhoea'] = pc
            age_group.probConditionalDiarrhoea[risk]['no diarrhoea'] = pn

    def _setProbAnaemiaDia(self):
        risk = 'Anaemia'
        for age_group in self.age_groups:
            age_group.probConditionalDiarrhoea[risk] = {}
            Z0 = age_group._getZa()
            Zt = Z0 # true for initialisation
            beta = age_group._getFracDiarrhoea(Z0, Zt)
            Yt = Zt * self.data.demographics['fraction severe diarrhoea']
            AO = age_group._getAverageOR(Yt, risk)
            fracDiarrhoea = sum(beta[bfCat] * age_group.bfDist[bfCat] for bfCat in self.settings.bfList)
            fracImpactedThisAge = sum(age_group.anaemiaDist[cat] for cat in self.settings.anaemicList)
            pn, pc = solve_quad(AO, fracDiarrhoea, fracImpactedThisAge)
            age_group.probConditionalDiarrhoea[risk]['diarrhoea'] = pc
            age_group.probConditionalDiarrhoea[risk]['no diarrhoea'] = pn

    def _setProbWastedDia(self):
        for age_group in self.age_groups:
            Z0 = age_group._getZa()
            Zt = Z0 # true for initialisation
            beta = age_group._getFracDiarrhoea(Z0, Zt)
            for wastingCat in self.settings.wastedList:
                A0 = age_group._getAverageOR(Zt, wastingCat)
                age_group.probConditionalDiarrhoea[wastingCat] = {}
                fracDiarrhoea = sum(beta[bfCat] * age_group.bfDist[bfCat] for bfCat in self.settings.bfList)
                fracThisCat = age_group.wastingDist[wastingCat]
                pn, pc = solve_quad(A0, fracDiarrhoea, fracThisCat)
                age_group.probConditionalDiarrhoea[wastingCat]['no diarrhoea'] = pn
                age_group.probConditionalDiarrhoea[wastingCat]['diarrhoea'] = pc

    def _setProbStuntedBirth(self):
        """Sets the probabilty of stunting conditional on birth outcome"""
        newborns = self.age_groups[0]
        coeffs = self._getBirthStuntingQuarticCoefficients()
        p0 = self._getBaselineProbabilityViaQuartic(coeffs)
        probStuntedAtBirth = {}
        probStuntedAtBirth['Term AGA'] = p0
        for BO in ["Pre-term SGA","Pre-term AGA","Term SGA"]:
            OR = self.settings.ORconditionBirth['stunting'][BO]
            probStuntedAtBirth[BO] = p0*OR / (1.-p0+OR*p0)
            pi = probStuntedAtBirth[BO]
            if(pi<0. or pi>1.):
                raise ValueError("probability of stunting at birth, at outcome %s, is out of range (%f)"%(BO, pi))
        newborns.probRiskAtBirth['Stunting'] = probStuntedAtBirth

    def _setProbWastedBirth(self):
        newborns = self.age_groups[0]
        probWastedAtBirth = {}
        for wastingCat in self.settings.wastedList:
            coEffs = self._getBirthWastingQuarticCoefficients(wastingCat)
            p0 = self._getBaselineProbabilityViaQuartic(coEffs)
            probWastedAtBirth[wastingCat] = {}
            probWastedAtBirth[wastingCat]['Term AGA'] = p0
            for birthOutcome in ["Pre-term SGA","Pre-term AGA","Term SGA"]:
                probWastedAtBirth[wastingCat][birthOutcome] = {}
                OR = self.default.ORconditionBirth[wastingCat][birthOutcome]
                probWastedAtBirth[wastingCat][birthOutcome] = p0*OR / (1.-p0+OR*p0)
                pi = p0*OR / (1.-p0+OR*p0)
                if(pi<0. or pi>1.):
                    raise ValueError("probability of wasting at birth, at outcome %s, is out of range (%f)"%(birthOutcome, pi))
        newborns.probRiskAtBirth['Wasting'] = probWastedAtBirth

    def _getBirthStuntingQuarticCoefficients(self):
        newborns = self.age_groups[0]
        OR = [1.]*4
        OR[0] = 1.
        OR[1] = self.settings.ORstuntingBO["Term SGA"]
        OR[2] = self.settings.ORstuntingBO["Pre-term AGA"]
        OR[3] = self.settings.ORstuntingBO["Pre-term SGA"]
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
        newborns = self.age_groups[0]
        FracBO = [0.]*4
        FracBO[1] = newborns.birthDist["Term SGA"]
        FracBO[2] = newborns.birthDist["Pre-term AGA"]
        FracBO[3] = newborns.birthDist["Pre-term SGA"]
        FracBO[0] = 1. - sum(FracBO[1:3])
        OR = [1.]*4
        OR[0] = 1.
        OR[1] = self.settings.ORconditionBirth[wastingCat]["Term SGA"]
        OR[2] = self.settings.ORconditionBirth[wastingCat]["Pre-term AGA"]
        OR[3] = self.settings.ORconditionBirth[wastingCat]["Pre-term SGA"]
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
        A,B,C,D,E = coEffs
        return A*pow(p0,4) + B*pow(p0,3) + C*pow(p0,2) + D*p0 + E

    def _setProgramEffectiveness(self):
        for age_group in self.age_groups:
            age = age_group.age
            age_group.programEffectiveness = self.default.childPrograms[age]

    def _setAnnualPrevChange(self):
        for risk in ['Stunting', 'Wasting', 'Anaemia']:
            for age_group in self.age_groups:
                age = age_group.age
                annualPrev = self.data.annualPrev[risk][age]
                years = array(annualPrev.keys())
                prev = array(annualPrev.values())
                notNan = isfinite(years) & isfinite(prev)
                if sum(notNan) <= 1: # static data
                    age_group.annualPrevChange[risk] = 1
                else:
                    linReg = polyfit(years[notNan],prev[notNan],1)
                    age_group.annualPrevChange[risk] = 1 + linReg[0]

    def _setCorrectBFpractice(self):
        for age_group in self.age_groups:
            age = age_group.age
            age_group.correctBFpractice = self.default.correctBF[age]

class PregnantWomen(object):
    def __init__(self, data, default_params, settings):
        self.name = 'Pregnant women'
        self.data = data
        self.default = default_params
        self.settings = settings
        self.age_groups = []
        self._make_pop_sizes()
        self._make_boxes()
        self._setPWReferenceMortality()
        self.update_mortality()
        self._setProgramEffectiveness()
        self._setAnnualPrevChange()

    def getTotalPopulation(self):
        return sum(age_group.getAgeGroupPopulation() for age_group in self.age_groups)

    def getTotalNumberAnaemic(self):
        return sum(age_group.getAgeGroupNumberAnaemic() for age_group in self.age_groups)

    def getTotalFracAnaemic(self):
        totalAnaemia = self.getTotalNumberAnaemic()
        totalPop = self.getTotalPopulation()
        return totalAnaemia / totalPop

    ##### DATA WRANGLING ######

    def _setProgramEffectiveness(self):
        for age_group in self.age_groups:
            age = age_group.age
            age_group.programEffectiveness = self.default.PWprograms[age]

    def _setAnnualPrevChange(self):
        for risk in ['Anaemia']:
            for age_group in self.age_groups:
                age = age_group.age
                annualPrev = self.data.annualPrev[risk][age]
                years = array(annualPrev.keys())
                prev = array(annualPrev.values())
                notNan = isfinite(years) & isfinite(prev)
                if sum(notNan) <= 1: # static data
                    age_group.annualPrevChange[risk] = 1
                else:
                    linReg = polyfit(years[notNan],prev[notNan],1)
                    age_group.annualPrevChange[risk] = 1 + linReg[0]

    def _setProbs(self):
        self._setProbAnaemic()

    def _make_pop_sizes(self):
        PWpop = self.data.populationByAge
        self.popSizes = {age:pop for age, pop in PWpop.iteritems()}

    def _make_boxes(self):
        for idx in range(len(self.settings.PWages)):
            age = self.settings.PWages[idx]
            popSize = self.popSizes[age]
            boxes = {}
            anaemiaDist = self.data.anaemiaDist[age]
            ageingRate = self.settings.womenAgeingRates[idx]
            for anaemiaCat in self.settings.anaemiaList:
                thisPop = popSize * anaemiaDist[anaemiaCat]
                boxes[anaemiaCat] = Box(thisPop)
            self.age_groups.append(PWAgeGroup(age, popSize, boxes, anaemiaDist, ageingRate, self.settings))

    def _setPWReferenceMortality(self):
        #Equation is:  LHS = RHS * X
        #we are solving for X
        # Calculate RHS for each age and cause
        RHS = {}
        for age in self.settings.PWages:
            RHS[age] = {}
            for cause in self.data.causesOfDeath:
                RHS[age][cause] = 0.
                for anaemiaCat in self.settings.anaemiaList:
                    t1 = self.data.anaemiaDist[age][anaemiaCat]
                    t2 = self.default.RRdeath['Anaemia'][cause][anaemiaCat][age]
                    RHS[age][cause] += t1 * t2
        # get age populations
        agePop = [age.getAgeGroupPopulation() for age in self.age_groups]
        # Correct raw mortality for units (per 1000 live births)
        liveBirths = self.data.demographics['number of live births']
        # The following assumes we only have a single mortality rate for PW
        mortalityRate = self.data.mortalityRates['maternal mortality']
        mortalityCorrected = {}
        for index in range(len(self.settings.PWages)):
            age = self.settings.PWages[index]
            if index == 0:
                mortalityCorrected[age] = (mortalityRate * liveBirths / 1000.) * (4. / 34.) / agePop[index]
            else:
                mortalityCorrected[age] = (mortalityRate * liveBirths / 1000.) * (9. / 34.) / agePop[index]
        # Calculate LHS for each age and cause of death then solve for X
        for age_group in self.age_groups:
            age = age_group.age
            age_group.referenceMortality = {}
            for cause in self.data.causesOfDeath:
                LHS_age_cause = mortalityCorrected[age] * self.data.deathDist[cause][age]
                age_group.referenceMortality[cause] = LHS_age_cause / RHS[age][cause]

    def update_mortality(self):
        for age_group in self.age_groups:
            age = age_group.age
            for anaemiaCat in self.settings.anaemiaList:
                count = 0
                for cause in self.data.causesOfDeath:
                    t1 = age_group.referenceMortality[cause]
                    t2 = self.default.RRdeath['Anaemia'][cause][anaemiaCat][age]
                    count += t1 * t2
                age_group.boxes[anaemiaCat].mortalityRate = count

    def _setProbAnaemic(self):
        risk = 'Anaemia'
        for age_group in self.age_groups:
            age = age_group.age
            age_group.probConditionalCoverage[risk] = {}
            for program in self.settings.programList:
                age_group.probConditionalCoverage[risk][program] = {}
                fracCovered = self.previousCov[program]
                fracImpacted = sum(age_group.anaemiaDist[cat] for cat in self.settings.anaemicList)
                if self.default.ORprograms[risk].get(program) is None:
                    RR = self.default.RRprograms[risk][program][age]
                    pn = fracImpacted / (RR * fracCovered + (1. - fracCovered))
                    pc = RR * pn
                else:
                    OR = self.default.ORprograms[risk][program][age]
                    pn, pc = solve_quad(OR, fracCovered, fracImpacted)
                age_group.probConditionalCoverage[risk][program]['covered'] = pc
                age_group.probConditionalCoverage[risk][program]['not covered'] = pn

class NonPregnantWomen(object):
    def __init__(self, data, default_params, settings):
        self.name = 'Non-pregnant women'
        self.data = data
        self.default = default_params
        self.settings = settings
        self.age_groups = []
        self._make_pop_sizes()
        self._make_boxes()
        self._setAnnualPrevChange()

    def getTotalPopulation(self):
        return sum(age_group.getAgeGroupPopulation() for age_group in self.age_groups)

    def getTotalNumberAnaemic(self):
        return sum(age_group.getAgeGroupNumberAnaemic() for age_group in self.age_groups)

    def getTotalFracAnaemic(self):
        totalAnaemia = self.getTotalNumberAnaemic()
        totalPop = self.getTotalPopulation()
        return totalAnaemia / totalPop

    ##### DATA WRANGLING ######

    def _setProbs(self):
        self._setProbAnaemic()

    def _make_pop_sizes(self):
        WRApop = self.data.populationByAge
        self.popSizes = {age:pop for age, pop in WRApop.iteritems()}

    def _make_boxes(self):
        for age in self.settings.WRAages:
            popSize = self.popSizes[age]
            boxes = {}
            anaemiaDist = self.data.anaemiaDist[age]
            for anaemiaCat in self.settings.anaemiaList:
                thisPop = popSize * anaemiaDist[anaemiaCat]
                boxes[anaemiaCat] = Box(thisPop)
            self.age_groups.append(NonPWAgeGroup(age, popSize, boxes, anaemiaDist, self.data.birthDist,
                                                self.data.birthAgeDist, self.data.birthIntervalDist, self.settings))

    def _setProbAnaemic(self):
        risk = 'Anaemia'
        for age_group in self.age_groups:
            age = age_group.age
            age_group.probConditionalCoverage[risk] = {}
            for program in self.settings.programList:
                age_group.probConditionalCoverage[risk][program] = {}
                fracCovered = self.previousCov[program]
                fracImpacted = sum(age_group.anaemiaDist[cat] for cat in self.settings.anaemicList)
                if self.default.ORprograms[risk].get(program) is None:
                    RR = self.default.RRprograms[risk][program][age]
                    pn = fracImpacted / (RR * fracCovered + (1. - fracCovered))
                    pc = RR * pn
                else:
                    OR = self.default.ORprograms[risk][program][age]
                    pn, pc = solve_quad(OR, fracCovered, fracImpacted)
                age_group.probConditionalCoverage[risk][program]['covered'] = pc
                age_group.probConditionalCoverage[risk][program]['not covered'] = pn

    def _setBPInfo(self, coverage):
        self._updateFracPregnancyAverted(coverage)
        numPregnant = self.settings.demographics['number of pregnant women']
        numWRA = sum(pop for key, pop in self.data.populationByAge.iteritems() if 'WRA' in key)
        rate = numPregnant/numWRA/(1.- self.fracPregnancyAverted)
        # reduce rate by % difference between births and pregnancies to get birth rate
        projectedBirths = self.settings.popProjections['number of births']
        projectedPWpop = self.settings.popProjections['pregnant women']
        percentDiff = [ai/bi for ai,bi in zip(projectedBirths, projectedPWpop)]
        averagePercentDiff = sum(percentDiff) / float(len(percentDiff))
        self.pregnancyRate = rate
        self.birthRate = averagePercentDiff * rate

    def _updateFracPregnancyAverted(self, coverage):
        if coverage == 0: # if missing or 0 cov
            self.fracPregnancyAverted = 0.
        else:
            self.fracPregnancyAverted = sum(self.settings.famPlanMethods[prog]['Effectiveness'] *
                self.settings.famPlanMethods[prog]['Distribution'] * coverage
                for prog in self.settings.famPlanMethods.iterkeys())

    def _setAnnualPrevChange(self):
        for risk in ['Anaemia']:
            for age_group in self.age_groups:
                age = age_group.age
                annualPrev = self.data.annualPrev[risk][age]
                years = array(annualPrev.keys())
                prev = array(annualPrev.values())
                notNan = isfinite(years) & isfinite(prev)
                if sum(notNan) <= 1: # static data
                    age_group.annualPrevChange[risk] = 1
                else:
                    linReg = polyfit(years[notNan],prev[notNan],1)
                    age_group.annualPrevChange[risk] = 1 + linReg[0]


def set_pops(data, default_params, settings):
    children = Children(data, default_params, settings)
    pregnantWomen = PregnantWomen(data, default_params, settings)
    nonPregnantWomen = NonPregnantWomen(data, default_params, settings)
    return [children, pregnantWomen, nonPregnantWomen]