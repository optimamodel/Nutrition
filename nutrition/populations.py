from utils import solve_quad, restratify, fit_poly
from nutrition import settings
from copy import deepcopy as dcp
from math import pow
from numpy import sqrt, isnan

class Box:
    def __init__(self, populationSize):
        self.populationSize = populationSize
        self.mortalityRate = None
        self.cumulativeDeaths = 0

class NonPWAgeGroup:
    def __init__(self, age, populationSize, boxes, anaemia_dist, birthOutcomeDist, birth_age, birth_int, settings):
        self.age = age
        # self.populationSize = populationSize
        self.boxes = dcp(boxes)
        self.anaemia_dist = dcp(anaemia_dist)
        self.birthOutcomeDist = dcp(birthOutcomeDist)
        self.birth_age = dcp(birth_age)
        self.birth_int = dcp(birth_int)
        self.settings = settings
        self.probConditionalCoverage = {}
        self.trends = {}
        self.set_update_storage()
        # self._setBirthProbs()

    def set_update_storage(self):
        self.anaemiaUpdate = 1.
        self.birthAgeUpdate = {}
        # for BA in self.settings.birthAges: # TODO: need this anymore?
        #     self.birthAgeUpdate[BA] = 1.

# TODO: do we need this?
    # def _setBirthProbs(self): # TODO: this should probably go in the NonPW class...
    #     """
    #     Setting the probability of each birth outcome.
    #     :return:
    #     """
    #     self.birthProb = {}
    #     for outcome, frac in self.birthOutcomeDist.iteritems():
    #         thisSum = 0.
    #         for ageOrder, fracAO in self.birth_age.iteritems():
    #             RRAO = self.default.rr_age_order[ageOrder][outcome]
    #             for interval, fracInterval in self.birth_int.iteritems():
    #                 rr_interval = self.default.rr_interval[interval][outcome]
    #                 thisSum += fracAO * RRAO * fracInterval * rr_interval
    #         self.birthProb[outcome] = thisSum

    def getAgeGroupPopulation(self):
        return sum(self.boxes[anaemiaCat].populationSize for anaemiaCat in self.settings.anaemia_list)

    def getAgeGroupNumberAnaemic(self):
        for anaemiaCat in self.settings.anaemic_list:
            return self.boxes[anaemiaCat].populationSize

    def getFracAnaemic(self):
        return self.getAgeGroupNumberAnaemic() / self.getAgeGroupPopulation()

    def getFracRisk(self, risk):
        return self.getFracAnaemic()

    def update_anaemia_dist(self):
        totalPop = self.getAgeGroupPopulation()
        for anaemiaCat in self.settings.anaemia_list:
            self.anaemia_dist[anaemiaCat] = self.boxes[anaemiaCat].populationSize / totalPop

    def distrib_pop(self):
        for anaemiaCat in self.settings.anaemia_list:
            self.boxes[anaemiaCat].populationSize = self.anaemia_dist[anaemiaCat] * self.getAgeGroupPopulation()

class PWAgeGroup:
    def __init__(self, age, populationSize, boxes, anaemia_dist, ageingRate, settings, causes_death, age_dist):
        self.age = age
        # self.populationSize = populationSize # TODO: would like to use this to good effect
        self.boxes = dcp(boxes)
        self.anaemia_dist = dcp(anaemia_dist)
        self.ageingRate = ageingRate
        self.settings = settings
        self.causes_death = dcp(causes_death)
        self.age_dist = age_dist
        self.probConditionalCoverage = {}
        self.trends = {}
        self.set_update_storage()

    def set_update_storage(self):
        self.anaemiaUpdate = 1.
        # this update will impact Newborn age group
        self.birthUpdate = {}
        for BO in self.settings.birth_outcomes:
            self.birthUpdate[BO] = 1.
        self.mortalityUpdate = {}
        for cause in self.causes_death:
            self.mortalityUpdate[cause] = 1.

    def getAgeGroupPopulation(self):
        return sum(self.boxes[anaemiaCat].populationSize for anaemiaCat in self.settings.anaemia_list)

    def getAgeGroupNumberAnaemic(self):
        for anaemiaCat in self.settings.anaemic_list:
            return self.boxes[anaemiaCat].populationSize

    def getFracAnaemic(self):
        return self.getAgeGroupNumberAnaemic() / self.getAgeGroupPopulation()

    def getFracRisk(self, risk):
        return self.getFracAnaemic()

    def update_anaemia_dist(self):
        totalPop = self.getAgeGroupPopulation()
        for anaemiaCat in self.settings.anaemia_list:
            self.anaemia_dist[anaemiaCat] = self.boxes[anaemiaCat].populationSize / totalPop

    def distrib_pop(self):
        for anaemiaCat in self.settings.anaemia_list:
            self.boxes[anaemiaCat].populationSize = self.anaemia_dist[anaemiaCat] * self.getAgeGroupPopulation()

class ChildAgeGroup(object):
    def __init__(self, age, populationSize, boxes, anaemia_dist, incidences, stunting_dist, wasting_dist, bf_dist,
                 ageingRate, settings, causes_death, default_params, frac_severe_dia):
        self.age = age
        # self.populationSize = populationSize
        self.boxes = dcp(boxes)
        self.anaemia_dist = dcp(anaemia_dist)
        self.stunting_dist = dcp(stunting_dist)
        self.wasting_dist = dcp(wasting_dist)
        self.bf_dist = dcp(bf_dist)
        self.incidences = dcp(incidences)
        self.settings = settings
        self.causes_death = dcp(causes_death)
        self.default = default_params
        self.frac_severe_dia = frac_severe_dia
        self.correct_bf = self.settings.correct_bf[age]
        self.incorrect_bf = list(set(self.settings.bf_list) - {self.correct_bf})
        self.ageingRate = ageingRate
        self.probConditionalCoverage = {}
        self.probConditionalDiarrhoea = {}
        self.probConditionalStunting = {}
        self.prog_eff = {}
        self.trends = {}
        self.set_update_storage()
        self._updatesForAgeingAndBirths()

    def _updatesForAgeingAndBirths(self):
        """
        Stunting & wasting have impact on births and ageing, which needs to be adjusted at each time step
        :return:
        """
        self.continuedStuntingImpact = 1.
        self.continuedWastingImpact = {}
        for wastingCat in self.settings.wasted_list:
            self.continuedWastingImpact[wastingCat] = 1.

    def set_update_storage(self):
        # storing updates
        self.stuntingUpdate = 1.
        self.anaemiaUpdate = 1.
        self.bfUpdate = {}
        self.diarrhoeaUpdate = {}
        self.bfPracticeUpdate = self.bf_dist[self.correct_bf]
        for risk in ['Stunting', 'Anaemia'] + self.settings.wasted_list:
            self.bfUpdate[risk] = 1.
        self.mortalityUpdate = {}
        for cause in self.causes_death:
            self.mortalityUpdate[cause] = 1.
        self.diarrhoeaIncidenceUpdate = 1.
        self.diarrhoeaUpdate = {}
        for risk in self.settings.wasted_list + ['Stunting', 'Anaemia']:
            self.diarrhoeaUpdate[risk] = 1.
        self.wastingPreventionUpdate = {}
        self.wastingTreatmentUpdate = {}
        for wastingCat in self.settings.wasted_list:
            self.wastingPreventionUpdate[wastingCat] = 1.
            self.wastingTreatmentUpdate[wastingCat] = 1.

    ###### POPULATION CALCULATIONS ######

    def getAgeGroupPopulation(self):
        totalPop = 0
        for stuntingCat in self.settings.stunting_list:
            for wastingCat in self.settings.wasting_list:
                for bfCat in self.settings.bf_list:
                    for anaemiaCat in self.settings.anaemia_list:
                        totalPop += self.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize
        return totalPop

    def getAgeGroupNumberStunted(self):
        numStunted = 0
        for stuntingCat in self.settings.stunted_list:
            for wastingCat in self.settings.wasting_list:
                for bfCat in self.settings.bf_list:
                    for anaemiaCat in self.settings.anaemia_list:
                        numStunted += self.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize
        return numStunted

    def getAgeGroupNumberNotStunted(self):
        numNotStunted = 0
        for stuntingCat in self.settings.non_stunted_list:
            for wastingCat in self.settings.wasting_list:
                for bfCat in self.settings.bf_list:
                    for anaemiaCat in self.settings.anaemia_list:
                        numNotStunted += self.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize
        return numNotStunted

    def getAgeGroupNumberNotAnaemic(self):
        numNotAnaemic = 0
        for stuntingCat in self.settings.stunting_list:
            for wastingCat in self.settings.wasting_list:
                for bfCat in self.settings.bf_list:
                    for anaemiaCat in self.settings.non_anaemic_list:
                        numNotAnaemic += self.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize
        return numNotAnaemic

    def getAgeGroupNumberNotWasted(self):
        numNotWasted = 0
        for stuntingCat in self.settings.stunting_list:
            for wastingCat in self.settings.non_wasted_list:
                for bfCat in self.settings.bf_list:
                    for anaemiaCat in self.settings.anaemia_list:
                        numNotWasted += self.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize
        return numNotWasted

    def getAgeGroupNumberThreeConditions(self):
        numWithThree = 0
        for stuntingCat in self.settings.stunted_list:
            for wastingCat in self.settings.wasted_list:
                for bfCat in self.settings.bf_list:
                    for anaemiaCat in self.settings.anaemic_list:
                        numWithThree += self.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize
        return numWithThree

    def getAgeGroupNumberHealthy(self):
        numHealthly = 0
        for stuntingCat in self.settings.non_stunted_list:
            for wastingCat in self.settings.non_wasted_list:
                for bfCat in self.settings.bf_list:
                    for anaemiaCat in self.settings.non_anaemic_list:
                        numHealthly += self.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize
        return numHealthly

    def getAgeGroupNumberNonStuntedNonWasted(self):
        numNonStuntedNonWasted = 0
        for stuntingCat in self.settings.non_stunted_list:
            for wastingCat in self.settings.non_wasted_list:
                for bfCat in self.settings.bf_list:
                    for anaemiaCat in self.settings.anaemia_list:
                        numNonStuntedNonWasted += self.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize
        return numNonStuntedNonWasted

    def get_stunting_dist(self):
        totalPop = self.getAgeGroupPopulation()
        returnDict = {}
        for stuntingCat in self.settings.stunting_list:
            returnDict[stuntingCat] = 0.
            for wastingCat in self.settings.wasting_list:
                for breastfeedingCat in self.settings.bf_list:
                    for anemiaStatus in self.settings.anaemia_list:
                        returnDict[stuntingCat] += self.boxes[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus].populationSize / totalPop
        return returnDict

    def getwasting_distribution(self):
        totalPop = self.getAgeGroupPopulation()
        returnDict = {}
        for wastingCat in self.settings.wasting_list:
            returnDict[wastingCat] = 0.
            for stuntingCat in self.settings.stunting_list:
                for breastfeedingCat in self.settings.bf_list:
                    for anemiaStatus in self.settings.anaemia_list:
                        returnDict[wastingCat] += self.boxes[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus].populationSize / totalPop
        return returnDict

    def getAgeGroupNumberAnaemic(self):
        numAnaemic = 0
        for stuntingCat in self.settings.stunting_list:
            for wastingCat in self.settings.wasting_list:
                for bfCat in self.settings.bf_list:
                    for anaemiaCat in self.settings.anaemic_list:
                        numAnaemic += self.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize
        return numAnaemic

    def getAgeGroupNumberWasted(self, wastingCat):
        numWasted = 0
        for stuntingCat in self.settings.stunting_list:
            for bfCat in self.settings.bf_list:
                for anaemiaCat in self.settings.anaemia_list:
                    numWasted += self.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize
        return numWasted

    def getCumulativeDeaths(self):
        deaths = 0
        for stuntingCat in self.settings.stunting_list:
            for wastingCat in self.settings.wasting_list:
                for bfCat in self.settings.bf_list:
                    for anaemiaCat in self.settings.anaemia_list:
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
            return sum([self.stunting_dist[cat] for cat in self.settings.stunted_list])
        elif risk == 'Anaemia':
            return sum([self.anaemia_dist[cat] for cat in self.settings.anaemic_list])

    def getNumberCorrectlyBF(self):
        numCorrect = 0
        for stuntingCat in self.settings.stunting_list:
            for wastingCat in self.settings.wasting_list:
                for anaemiaCat in self.settings.anaemia_list:
                    numCorrect += self.boxes[stuntingCat][wastingCat][self.correct_bf][anaemiaCat].populationSize
        return numCorrect

    def distrib_pop(self):
        totalPop = self.getAgeGroupPopulation()
        for stuntingCat in self.settings.stunting_list:
            for wastingCat in self.settings.wasting_list:
                for bfCat in self.settings.bf_list:
                    for anaemiaCat in self.settings.anaemia_list:
                        self.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize = self.stunting_dist[stuntingCat] * \
                                                                                                self.wasting_dist[wastingCat] * \
                                                                                                self.bf_dist[bfCat] * \
                                                                                                self.anaemia_dist[anaemiaCat] * totalPop

    def update_stunting_dist(self):
        totalPop = self.getAgeGroupPopulation()
        for stuntingCat in self.settings.stunting_list:
            self.stunting_dist[stuntingCat] = 0
            for wastingCat in self.settings.wasting_list:
                for breastfeedingCat in self.settings.bf_list:
                    for anemiaStatus in self.settings.anaemia_list:
                        self.stunting_dist[stuntingCat] += self.boxes[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus].populationSize / totalPop

    def update_wasting_dist(self):
        totalPop = self.getAgeGroupPopulation()
        for wastingCat in self.settings.wasting_list:
            self.wasting_dist[wastingCat] = 0
            for stuntingCat in self.settings.stunting_list:
                for breastfeedingCat in self.settings.bf_list:
                    for anaemiaCat in self.settings.anaemia_list:
                        self.wasting_dist[wastingCat] += self.boxes[stuntingCat][wastingCat][breastfeedingCat][
                                                                  anaemiaCat].populationSize / totalPop

    def update_anaemia_dist(self):
        totalPop = self.getAgeGroupPopulation()
        for anaemiaCat in self.settings.anaemia_list:
            self.anaemia_dist[anaemiaCat] = 0
            for stuntingCat in self.settings.stunting_list:
                for wastingCat in self.settings.wasting_list:
                    for breastfeedingCat in self.settings.bf_list:
                        self.anaemia_dist[anaemiaCat] += self.boxes[stuntingCat][wastingCat][breastfeedingCat][
                                                              anaemiaCat].populationSize / totalPop

    def update_bf_dist(self):
        totalPop = self.getAgeGroupPopulation()
        for bfCat in self.settings.bf_list:
            self.bf_dist[bfCat] = 0
            for stuntingCat in self.settings.stunting_list:
                for wastingCat in self.settings.wasting_list:
                    for anaemiaCat in self.settings.anaemia_list:
                        self.bf_dist[bfCat] += self.boxes[stuntingCat][wastingCat][bfCat][
                                                              anaemiaCat].populationSize / totalPop

    def _getFracDiarrhoeaFixedZ(self):
        beta = {}
        RRnot = self.default.rr_dia[self.age]['None']
        for bfCat in self.settings.bf_list:
            RDa = self.default.rr_dia[self.age][bfCat]
            beta[bfCat] = RDa/RRnot
        return beta

    def _getFracDiarrhoea(self, Z0, Zt):
        beta = {}
        RRnot = self.default.rr_dia[self.age]['None']
        for bfCat in self.settings.bf_list:
            RDa = self.default.rr_dia[self.age][bfCat]
            beta[bfCat] = 1. - (RRnot * Z0 - RDa * Zt) / \
                          (RRnot * Z0)
            # RDa * Zt[age] / (RRnot * Z0[age])
        return beta

    def _getZa(self):
        riskSum = self._getDiarrhoeaRiskSum()
        incidence = self.incidences['Diarrhoea']
        return incidence / riskSum

    def _getDiarrhoeaRiskSum(self):
        return sum(self.default.rr_dia[self.age][bfCat] * self.bf_dist[bfCat] for bfCat in self.settings.bf_list)

    def _getAverageOR(self, Za, risk):
        RRnot = self.default.rr_dia[self.age]['None']
        if risk == 'Stunting':
            OR = self.default.or_cond['Stunting']['Diarrhoea'][self.age]
        elif risk == 'Anaemia':
            OR = self.default.or_cond['Anaemia']['Severe diarrhoea'][self.age]
        elif risk == 'MAM' or risk == 'SAM':
            OR = self.default.or_cond[risk]['Diarrhoea'][self.age]
        else:
            print 'risk factor is invalid'
        AO = pow(OR, RRnot * Za * 1./self.ageingRate)
        return AO

    def _updateProbConditionalDiarrhoea(self, Zt):
        # stunting and anaemia
        AO = {}
        for risk in ['Stunting', 'Anaemia']:
            if risk == 'Anaemia':
                AO[risk] = self._getAverageOR(Zt * self.frac_severe_dia, risk)
            else:
                AO[risk] = self._getAverageOR(Zt, risk)
            Omega0 = self.probConditionalDiarrhoea[risk]['no diarrhoea']
            self.probConditionalDiarrhoea[risk]['diarrhoea'] = Omega0 * AO[risk] / (1. - Omega0 + AO[risk] * Omega0)
        # wasting cats
        for wastingCat in self.settings.wasted_list:
            AO = self._getAverageOR(Zt, wastingCat)
            Omega0 = self.probConditionalDiarrhoea[wastingCat]['no diarrhoea']
            self.probConditionalDiarrhoea[wastingCat]['diarrhoea'] = Omega0 * AO / (1. - Omega0 + AO * Omega0)

class Newborn(ChildAgeGroup):
    def __init__(self, age, populationSize, boxes, anaemia_dist, incidences, stunting_dist, wasting_dist, bf_dist,
                 ageingRate, settingsants, birth_dist, causes_death, default_params, frac_severe_dia):
        """
        This is the <1 month age group, distinguished from the other age groups by birth outcomes, spacing etc etc.
        """
        super(Newborn, self).__init__(age, populationSize, boxes, anaemia_dist, incidences, stunting_dist, wasting_dist, bf_dist,
                 ageingRate, settingsants, causes_death, default_params, frac_severe_dia)
        self.birth_dist = birth_dist
        self.probRiskAtBirth = {}
        self.birthUpdate = {}
        for BO in self.settings.birth_outcomes:
            self.birthUpdate[BO] = 1.

class Children(object):
    def __init__(self, data, default_params):
        self.name = 'Children'
        self.data = data # TODO: need to copy all this?
        self.proj = dcp(data.proj)
        self.pop_areas = default_params.pop_areas
        self.birth_dist = self.data.demo['Birth dist']
        self.stunting_dist = self.data.risk_dist['Stunting']
        self.anaemia_dist = self.data.risk_dist['Anaemia']
        self.wasting_dist = self.data.risk_dist['Wasting']
        self.bf_dist = self.data.risk_dist['Breastfeeding']
        self.mamtosam = self.data.mamtosam
        self.samtomam = self.data.samtomam
        self.default = default_params
        self.settings = settings.Settings()
        self.age_groups = []
        self._make_pop_sizes()
        self._make_boxes()
        self._set_child_mortality()
        self.update_mortality()
        self._setProgramEffectiveness()
        self._set_time_trends()
        self._setcorrect_bfpractice()
        self._setprob_futurestunting()
        self._setprob_stuntedbirth()
        self._setProbWastedBirth()

    ##### DATA WRANGLING ######

    def set_probs(self, prog_areas):
        self._setProbStunted(prog_areas)
        self._set_prob_anaem(prog_areas)
        self._setProbWasted(prog_areas)
        self._setProbBF(prog_areas)
        self._setProbStuntedDia()
        self._setProbAnaemiaDia()
        self._setProbWastedDia()

    def _setConditionalDiarrhoea(self):
        self._setProbStuntedDia()
        self._setProbAnaemiaDia()
        self._setProbWastedDia()

    def _make_pop_sizes(self):
        # for children less than 1 year, annual live births
        monthlyBirths = self.data.proj['Number of births'][0] / 12.
        popSize = [pop * monthlyBirths for pop in self.settings.child_age_spans[:3]]
        # children > 1 year, who are not counted in annual 'live births'
        months = sum(self.settings.child_age_spans[3:])
        popRemainder = self.data.proj['Children under 5'][0] - monthlyBirths * 12.
        monthlyRate = popRemainder/months
        popSize += [pop * monthlyRate for pop in self.settings.child_age_spans[3:]]
        self.popSizes = {age:pop for age, pop in zip(self.settings.child_ages, popSize)}

    def _make_boxes(self):
        for i, age in enumerate(self.settings.child_ages):
            popSize = self.popSizes[age]
            boxes = {}
            stunting_dist = self.stunting_dist[age]
            stunting_dist = restratify(sum(stunting_dist[cat] for cat in self.settings.stunted_list))
            anaemia_dist = self.anaemia_dist[age]
            wasting_dist = self.wasting_dist[age]
            probWasted = sum(wasting_dist[cat] for cat in self.settings.wasted_list)
            nonwasting_dist = restratify(probWasted)
            for cat in self.settings.non_wasted_list:
                wasting_dist[cat] = nonwasting_dist[cat]
            bf_dist = self.bf_dist[age]
            birth_dist = self.birth_dist
            incidences = self.data.incidences[age] # TODO: do this adjustment elsewhere, same as restratifying
            incidences = {condition: incidence * self.settings.timestep for condition, incidence in incidences.iteritems()}
            ageingRate = 1./self.settings.child_age_spans[i]
            for stuntingCat in self.settings.stunting_list:
                boxes[stuntingCat] = {}
                for wastingCat in self.settings.wasting_list:
                    boxes[stuntingCat][wastingCat] = {}
                    for bfCat in self.settings.bf_list:
                        boxes[stuntingCat][wastingCat][bfCat] = {}
                        for anaemiaCat in self.settings.anaemia_list:
                            thisPop = popSize * stunting_dist[stuntingCat] * anaemia_dist[anaemiaCat] * \
                                      wasting_dist[wastingCat] * bf_dist[bfCat]
                            boxes[stuntingCat][wastingCat][bfCat][anaemiaCat] = Box(thisPop)
            if age == '<1 month': # <1 month age group has slightly different functionality
                self.age_groups.append(Newborn(age, popSize, boxes,
                                           anaemia_dist, incidences, stunting_dist, wasting_dist, bf_dist,
                                                ageingRate, self.settings, birth_dist, self.data.causes_death, self.default,
                                               self.data.demo['Percentage of diarrhea that is severe']))
            else:
                self.age_groups.append(ChildAgeGroup(age, popSize, boxes,
                                           anaemia_dist, incidences, stunting_dist, wasting_dist, bf_dist,
                                                ageingRate, self.settings, self.data.causes_death, self.default,
                                                     self.data.demo['Percentage of diarrhea that is severe']))

    def _set_child_mortality(self):
        # Equation is:  LHS = RHS * X
        # we are solving for X
        # Calculate RHS for each age and cause
        RHS = {}
        for age in self.settings.child_ages:
            RHS[age] = {}
            for cause in self.data.causes_death:
                RHS[age][cause] = 0.
                for stuntingCat in self.settings.stunting_list:
                    for wastingCat in self.settings.wasting_list:
                        for bfCat in self.settings.bf_list:
                            for anaemiaCat in self.settings.anaemia_list:
                                t1 = self.stunting_dist[age][stuntingCat]
                                t2 = self.wasting_dist[age][wastingCat]
                                t3 = self.bf_dist[age][bfCat]
                                t4 = self.anaemia_dist[age][anaemiaCat]
                                t5 = self.default.rr_death['Stunting'][age][stuntingCat].get(cause,1)
                                t6 = self.default.rr_death['Wasting'][age][wastingCat].get(cause,1)
                                t7 = self.default.rr_death['Breastfeeding'][age][bfCat].get(cause,1)
                                t8 = self.default.rr_death['Anaemia'][age][anaemiaCat].get(cause,1)
                                RHS[age][cause] += t1 * t2 * t3 * t4 * t5 * t6 * t7 * t8
        # RHS for newborns only
        age = '<1 month'
        for cause in self.data.causes_death:
            RHS[age][cause] = 0.
            for breastfeedingCat in self.settings.bf_list:
                Pbf = self.bf_dist[age][breastfeedingCat]
                RRbf = self.default.rr_death['Breastfeeding'][age][breastfeedingCat].get(cause,1)
                for birthoutcome in self.settings.birth_outcomes:
                    Pbo = self.birth_dist[birthoutcome]
                    RRbo = self.default.rr_death['Birth outcomes'][birthoutcome].get(cause,1)
                    for anaemiaCat in self.settings.anaemia_list:
                        Pan = self.anaemia_dist[age][anaemiaCat]
                        RRan = self.default.rr_death['Anaemia'][age][anaemiaCat].get(cause,1)
                        RHS[age][cause] += Pbf * RRbf * Pbo * RRbo * Pan * RRan
        # calculate total mortality by age (corrected for units)
        AgePop = [age.getAgeGroupPopulation() for age in self.age_groups]
        MortalityCorrected = {}
        LiveBirths = self.data.proj['Number of births'][0]
        Mnew = self.data.demo['Neonatal mortality (per 1,000 live births)']
        Minfant = self.data.demo['Infant mortality (per 1,000 live births)']
        Mu5 = self.data.demo['Under 5 mortality (per 1,000 live births)']
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
            for cause in self.data.causes_death:
                LHS_age_cause = MortalityCorrected[age] * self.data.death_dist[cause][age]
                age_group.referenceMortality[cause] = LHS_age_cause / RHS[age][cause]

    def update_mortality(self):
        # Newborns first
        age_group = self.age_groups[0]
        age = age_group.age
        for bfCat in self.settings.bf_list:
            count = 0.
            for cause in self.data.causes_death:
                Rb = self.default.rr_death['Breastfeeding'][age][bfCat].get(cause,1)
                for outcome in self.settings.birth_outcomes:
                    pbo = age_group.birth_dist[outcome]
                    Rbo = self.default.rr_death['Birth outcomes'][outcome].get(cause,1)
                    count += Rb * pbo * Rbo * age_group.referenceMortality[cause]
            for stuntingCat in self.settings.stunting_list:
                for wastingCat in self.settings.wasting_list:
                    for anaemiaCat in self.settings.anaemia_list:
                        age_group.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].mortalityRate = count
        # over 1 months
        for age_group in self.age_groups[1:]:
            age = age_group.age
            for stuntingCat in self.settings.stunting_list:
                for wastingCat in self.settings.wasting_list:
                    for bfCat in self.settings.bf_list:
                        for anaemiaCat in self.settings.anaemia_list:
                            count = 0.
                            for cause in self.data.causes_death:
                                t1 = age_group.referenceMortality[cause]
                                t2 = self.default.rr_death['Stunting'][age][stuntingCat].get(cause,1)
                                t3 = self.default.rr_death['Wasting'][age][wastingCat].get(cause,1)
                                t4 = self.default.rr_death['Breastfeeding'][age][bfCat].get(cause,1)
                                t5 = self.default.rr_death['Anaemia'][age][anaemiaCat].get(cause,1)
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
        totalWasted = sum(self.getTotalNumberWasted(wastingCat) for wastingCat in self.settings.wasted_list)
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

    def _setprob_futurestunting(self):
        """Calculate the probability of stunting given previous stunting between age groups"""
        for i, age_group in enumerate(self.age_groups[1:]):
            thisAge = age_group.age
            prevAgeGroup = self.age_groups[i-1]
            OR = self.default.or_cond['Stunting']['Prev stunting'][thisAge]
            fracStuntedThisAge = age_group.getStuntedFrac()
            fracStuntedPrev = prevAgeGroup.getStuntedFrac()
            pn, pc = solve_quad(OR, fracStuntedPrev, fracStuntedThisAge)
            age_group.probConditionalStunting['stunted'] = pc
            age_group.probConditionalStunting['not stunted'] = pn

    def _setProbStunted(self, prog_areas):
        risk = 'Stunting'
        relev_progs = prog_areas[risk]
        for age_group in self.age_groups:
            age = age_group.age
            fracStunted = sum(age_group.stunting_dist[cat] for cat in self.settings.stunted_list)
            age_group.probConditionalCoverage[risk] = {}
            for program in relev_progs:
                age_group.probConditionalCoverage[risk][program] = {}
                fracCovered = self.previousCov[program]
                OR = self.default.or_stunting_prog[program][age]
                pn, pc = solve_quad(OR, fracCovered, fracStunted)
                age_group.probConditionalCoverage[risk][program]['covered'] = pc
                age_group.probConditionalCoverage[risk][program]['not covered'] = pn

    def _set_prob_anaem(self, prog_areas):
        risk = 'Anaemia'
        relev_progs = prog_areas[risk]
        for age_group in self.age_groups:
            age = age_group.age
            fracAnaemic = sum(age_group.anaemia_dist[cat] for cat in self.settings.anaemic_list)
            age_group.probConditionalCoverage[risk] = {}
            for program in relev_progs:
                age_group.probConditionalCoverage[risk][program] = {}
                fracCovered = self.previousCov[program]
                if self.default.rr_anaem_prog.get(program) is not None:
                    RR = self.default.rr_anaem_prog[program][age]
                    pn = fracAnaemic / (RR * fracCovered + (1. - fracCovered))
                    pc = RR * pn
                else:  # OR
                    OR = self.default.or_anaem_prog[program][age]
                    pn, pc = solve_quad(OR, fracCovered, fracAnaemic)
                age_group.probConditionalCoverage[risk][program]['covered'] = pc
                age_group.probConditionalCoverage[risk][program]['not covered'] = pn

    def _setProbBF(self, prog_areas):
        risk = 'Breastfeeding'
        relev_progs = prog_areas[risk]
        for age_group in self.age_groups:
            age = age_group.age
            age_group.probConditionalCoverage[risk] = {}
            fracAppropriate = age_group.bf_dist[age_group.correct_bfpractice]
            for program in relev_progs:
                age_group.probConditionalCoverage[risk][program] = {}
                OR = self.default.ORappropriateBFprogram[program][age]
                fracCovered = self.previousCov[program]
                pn, pc = solve_quad(OR, fracCovered, fracAppropriate)
                age_group.probConditionalCoverage[risk][program]['covered'] = pc
                age_group.probConditionalCoverage[risk][program]['not covered'] = pn

    def _setProbWasted(self, prog_areas):
        risk = 'Wasting treatment' # only treatment have ORs for wasting
        relev_progs = prog_areas[risk]
        for wastingCat in self.settings.wasted_list:
            for age_group in self.age_groups:
                age_group.probConditionalCoverage[wastingCat] = {}
                age = age_group.age
                fracThisCatAge = age_group.wasting_dist[wastingCat]
                for program in relev_progs:
                    try:
                        OR = self.default.or_wasting_prog[wastingCat][program][age]
                    except KeyError: # if, for eg, MAM doesn't have Treatment of SAM key
                        OR = 1
                    fracCovered = self.previousCov[program]
                    pn, pc = solve_quad(OR, fracCovered, fracThisCatAge)
                    age_group.probConditionalCoverage[wastingCat][program] = {}
                    age_group.probConditionalCoverage[wastingCat][program]['covered'] = pc
                    age_group.probConditionalCoverage[wastingCat][program]['not covered'] = pn

    def _setProbStuntedDia(self):
        risk = 'Stunting'
        for age_group in self.age_groups:
            age_group.probConditionalDiarrhoea[risk] = {}
            Z0 = age_group._getZa()
            Zt = Z0 # true for initialisation
            beta = age_group._getFracDiarrhoea(Z0, Zt)
            AO = age_group._getAverageOR(Zt, risk)
            fracDiarrhoea = sum(beta[bfCat] * age_group.bf_dist[bfCat] for bfCat in self.settings.bf_list)
            fracImpactedThisAge = sum(age_group.stunting_dist[cat] for cat in self.settings.stunted_list)
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
            Yt = Zt * self.data.demo['Percentage of diarrhea that is severe']
            AO = age_group._getAverageOR(Yt, risk)
            fracDiarrhoea = sum(beta[bfCat] * age_group.bf_dist[bfCat] for bfCat in self.settings.bf_list)
            fracImpactedThisAge = sum(age_group.anaemia_dist[cat] for cat in self.settings.anaemic_list)
            pn, pc = solve_quad(AO, fracDiarrhoea, fracImpactedThisAge)
            age_group.probConditionalDiarrhoea[risk]['diarrhoea'] = pc
            age_group.probConditionalDiarrhoea[risk]['no diarrhoea'] = pn

    def _setProbWastedDia(self):
        for age_group in self.age_groups:
            Z0 = age_group._getZa()
            Zt = Z0 # true for initialisation
            beta = age_group._getFracDiarrhoea(Z0, Zt)
            for wastingCat in self.settings.wasted_list:
                A0 = age_group._getAverageOR(Zt, wastingCat)
                age_group.probConditionalDiarrhoea[wastingCat] = {}
                fracDiarrhoea = sum(beta[bfCat] * age_group.bf_dist[bfCat] for bfCat in self.settings.bf_list)
                fracThisCat = age_group.wasting_dist[wastingCat]
                pn, pc = solve_quad(A0, fracDiarrhoea, fracThisCat)
                age_group.probConditionalDiarrhoea[wastingCat]['no diarrhoea'] = pn
                age_group.probConditionalDiarrhoea[wastingCat]['diarrhoea'] = pc

    def _setprob_stuntedbirth(self):
        """Sets the probabilty of stunting conditional on birth outcome"""
        newborns = self.age_groups[0]
        coeffs = self._getBirthStuntingQuarticCoefficients()
        p0 = self._getBaselineProbabilityViaQuartic(coeffs)
        probStuntedAtBirth = {}
        probStuntedAtBirth['Term AGA'] = p0
        for BO in ["Pre-term SGA","Pre-term AGA","Term SGA"]:
            OR = self.default.or_cond_bo['Stunting'][BO]
            probStuntedAtBirth[BO] = p0*OR / (1.-p0+OR*p0)
            pi = probStuntedAtBirth[BO]
            if(pi<0. or pi>1.):
                raise ValueError("probability of stunting at birth, at outcome %s, is out of range (%f)"%(BO, pi))
        newborns.probRiskAtBirth['Stunting'] = probStuntedAtBirth

    def _setProbWastedBirth(self):
        newborns = self.age_groups[0]
        probWastedAtBirth = {}
        for wastingCat in self.settings.wasted_list:
            coEffs = self._getBirthWastingQuarticCoefficients(wastingCat)
            p0 = self._getBaselineProbabilityViaQuartic(coEffs)
            probWastedAtBirth[wastingCat] = {}
            probWastedAtBirth[wastingCat]['Term AGA'] = p0
            for birthOutcome in ["Pre-term SGA","Pre-term AGA","Term SGA"]:
                probWastedAtBirth[wastingCat][birthOutcome] = {}
                OR = self.default.or_cond_bo[wastingCat][birthOutcome]
                probWastedAtBirth[wastingCat][birthOutcome] = p0*OR / (1.-p0+OR*p0)
                pi = p0*OR / (1.-p0+OR*p0)
                if(pi<0. or pi>1.):
                    raise ValueError("probability of wasting at birth, at outcome %s, is out of range (%f)"%(birthOutcome, pi))
        newborns.probRiskAtBirth['Wasting'] = probWastedAtBirth

    def _getBirthStuntingQuarticCoefficients(self):
        newborns = self.age_groups[0]
        OR = [1.]*4
        OR[0] = 1.
        OR[1] = self.default.or_cond_bo['Stunting']["Term SGA"]
        OR[2] = self.default.or_cond_bo['Stunting']["Pre-term AGA"]
        OR[3] = self.default.or_cond_bo['Stunting']["Pre-term SGA"]
        FracBO = [0.]*4
        FracBO[1] = newborns.birth_dist["Term SGA"]
        FracBO[2] = newborns.birth_dist["Pre-term AGA"]
        FracBO[3] = newborns.birth_dist["Pre-term SGA"]
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
        FracBO[1] = newborns.birth_dist["Term SGA"]
        FracBO[2] = newborns.birth_dist["Pre-term AGA"]
        FracBO[3] = newborns.birth_dist["Pre-term SGA"]
        FracBO[0] = 1. - sum(FracBO[1:3])
        OR = [1.]*4
        OR[0] = 1.
        OR[1] = self.default.or_cond_bo[wastingCat]["Term SGA"]
        OR[2] = self.default.or_cond_bo[wastingCat]["Pre-term AGA"]
        OR[3] = self.default.or_cond_bo[wastingCat]["Pre-term SGA"]
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
            age_group.prog_eff = self.default.child_progs[age]

    def _set_time_trends(self):
        trends = self.data.time_trends
        for risk in ['Stunting', 'Wasting', 'Anaemia']:
            trend = trends[risk]
            for age_group in self.age_groups:
                age_group.trends[risk] = fit_poly(0, trend)
        # breastfeeding has age dependency
        risk = 'Breastfeeding'
        trend = trends[risk]
        younger = self.age_groups[:3]
        for age_group in younger:
            age_group.trends[risk] = fit_poly(0, trend)
        older = self.age_groups[3:]
        for age_group in older:
            age_group.trends[risk] = fit_poly(1, trend)

    def _setcorrect_bfpractice(self):
        for age_group in self.age_groups:
            age = age_group.age
            age_group.correct_bfpractice = self.settings.correct_bf[age]

class PregnantWomen(object):
    def __init__(self, data, default_params):
        self.name = 'Pregnant women'
        self.data = data
        self.proj = dcp(data.proj)
        self.pop_areas = default_params.pop_areas
        self.age_dist = data.pw_agedist
        self.anaemia_dist = self.data.risk_dist['Anaemia']
        self.default = default_params
        self.settings = settings.Settings()
        self.age_groups = []
        self._make_pop_sizes()
        self._make_boxes()
        self._setPWReferenceMortality()
        self.update_mortality()
        self._setProgramEffectiveness()
        self._set_time_trends()

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
            age_group.prog_eff = self.default.pw_progs[age]

    def _set_time_trends(self):
        risk = 'Anaemia'
        trend = self.data.time_trends[risk]
        for age_group in self.age_groups:
            age_group.trends[risk] = fit_poly(1, trend)

    def set_probs(self, prog_areas):
        self._set_prob_anaem(prog_areas)

    def _make_pop_sizes(self):
        pw_pop = self.data.proj['Estimated pregnant women'][0] # total baseline number
        pw_dist = self.data.pw_agedist
        self.popSizes = [pw_pop*dist for dist in pw_dist]

    def _make_boxes(self):
        for i, age in enumerate(self.settings.pw_ages):
            popSize = self.popSizes[i]
            boxes = {}
            anaemia_dist = self.anaemia_dist[age]
            ageingRate = self.settings.women_age_rates[i]
            age_dist = self.data.pw_agedist[i]
            for anaemiaCat in self.settings.anaemia_list:
                thisPop = popSize * anaemia_dist[anaemiaCat]
                boxes[anaemiaCat] = Box(thisPop)
            self.age_groups.append(PWAgeGroup(age, popSize, boxes, anaemia_dist, ageingRate, self.settings,
                                              self.data.causes_death, age_dist))

    def _setPWReferenceMortality(self):
        #Equation is:  LHS = RHS * X
        #we are solving for X
        # Calculate RHS for each age and cause
        RHS = {}
        for age in self.settings.pw_ages:
            RHS[age] = {}
            for cause in self.data.causes_death:
                RHS[age][cause] = 0.
                for anaemiaCat in self.settings.anaemia_list:
                    t1 = self.anaemia_dist[age][anaemiaCat]
                    t2 = self.default.rr_death['Anaemia'][age][anaemiaCat].get(cause,1)
                    RHS[age][cause] += t1 * t2
        # get age populations
        agePop = [age.getAgeGroupPopulation() for age in self.age_groups]
        # Correct raw mortality for units (per 1000 live births)
        liveBirths = self.data.proj['Number of births'][0]
        # The following assumes we only have a single mortality rate for PW
        mortalityRate = self.data.demo['Maternal mortality (per 1,000 live births)']
        mortalityCorrected = {}
        for index in range(len(self.settings.pw_ages)):
            age = self.settings.pw_ages[index]
            if index == 0:
                mortalityCorrected[age] = (mortalityRate * liveBirths / 1000.) * (4. / 34.) / agePop[index]
            else:
                mortalityCorrected[age] = (mortalityRate * liveBirths / 1000.) * (9. / 34.) / agePop[index]
        # Calculate LHS for each age and cause of death then solve for X
        for age_group in self.age_groups:
            age = age_group.age
            age_group.referenceMortality = {}
            for cause in self.data.causes_death:
                LHS_age_cause = mortalityCorrected[age] * self.data.death_dist[cause][age]
                age_group.referenceMortality[cause] = LHS_age_cause / RHS[age][cause]

    def update_mortality(self):
        for age_group in self.age_groups:
            age = age_group.age
            for anaemiaCat in self.settings.anaemia_list:
                count = 0
                for cause in self.data.causes_death:
                    t1 = age_group.referenceMortality[cause]
                    t2 = self.default.rr_death['Anaemia'][age][anaemiaCat].get(cause,1)
                    count += t1 * t2
                age_group.boxes[anaemiaCat].mortalityRate = count

    def _set_prob_anaem(self, prog_areas):
        risk = 'Anaemia'
        relev_progs = prog_areas[risk]
        for age_group in self.age_groups:
            age = age_group.age
            age_group.probConditionalCoverage[risk] = {}
            for program in relev_progs:
                age_group.probConditionalCoverage[risk][program] = {}
                fracCovered = self.previousCov[program]
                fracImpacted = sum(age_group.anaemia_dist[cat] for cat in self.settings.anaemic_list)
                if self.default.or_anaem_prog.get(program) is None:
                    RR = self.default.rr_anaem_prog[program][age]
                    pn = fracImpacted / (RR * fracCovered + (1. - fracCovered))
                    pc = RR * pn
                else:
                    OR = self.default.or_anaem_prog[program][age]
                    pn, pc = solve_quad(OR, fracCovered, fracImpacted)
                age_group.probConditionalCoverage[risk][program]['covered'] = pc
                age_group.probConditionalCoverage[risk][program]['not covered'] = pn

class NonPregnantWomen(object):
    def __init__(self, data, default_params):
        self.name = 'Non-pregnant women'
        self.data = data
        self.proj = dcp(data.proj)
        self.pop_areas = default_params.pop_areas
        self.anaemia_dist = self.data.risk_dist['Anaemia']
        self.birth_dist = self.data.demo['Birth dist']
        self.default = default_params
        self.settings = settings.Settings()
        self.age_groups = []
        self._make_pop_sizes()
        self._make_boxes()
        self._set_time_trends()

    def getTotalPopulation(self):
        return sum(age_group.getAgeGroupPopulation() for age_group in self.age_groups)

    def getTotalNumberAnaemic(self):
        return sum(age_group.getAgeGroupNumberAnaemic() for age_group in self.age_groups)

    def getTotalFracAnaemic(self):
        totalAnaemia = self.getTotalNumberAnaemic()
        totalPop = self.getTotalPopulation()
        return totalAnaemia / totalPop

    ##### DATA WRANGLING ######

    def set_probs(self, prog_areas):
        self._set_prob_anaem(prog_areas)

    def _make_pop_sizes(self):
        wra_proj = self.data.wra_proj
        self.popSizes = [proj[0] for proj in wra_proj]

    def _make_boxes(self):
        for i, age in enumerate(self.settings.wra_ages):
            popSize = self.popSizes[i]
            boxes = {}
            anaemia_dist = self.anaemia_dist[age]
            for anaemiaCat in self.settings.anaemia_list:
                thisPop = popSize * anaemia_dist[anaemiaCat]
                boxes[anaemiaCat] = Box(thisPop)
            self.age_groups.append(NonPWAgeGroup(age, popSize, boxes, anaemia_dist, self.birth_dist,
                                                self.data.birth_age, self.data.birth_int, self.settings))

    def _set_prob_anaem(self, prog_areas):
        risk = 'Anaemia'
        relev_progs = prog_areas[risk]
        for age_group in self.age_groups:
            age = age_group.age
            age_group.probConditionalCoverage[risk] = {}
            for program in relev_progs:
                age_group.probConditionalCoverage[risk][program] = {}
                fracCovered = self.previousCov[program]
                fracImpacted = sum(age_group.anaemia_dist[cat] for cat in self.settings.anaemic_list)
                if self.default.or_anaem_prog.get(program) is None:
                    RR = self.default.rr_anaem_prog[program][age]
                    pn = fracImpacted / (RR * fracCovered + (1. - fracCovered))
                    pc = RR * pn
                else:
                    OR = self.default.or_anaem_prog[program][age]
                    pn, pc = solve_quad(OR, fracCovered, fracImpacted)
                age_group.probConditionalCoverage[risk][program]['covered'] = pc
                age_group.probConditionalCoverage[risk][program]['not covered'] = pn

    def _setBPInfo(self, coverage):
        self.update_preg_averted(coverage)
        numPregnant = self.data.proj['Estimated pregnant women'][0]
        numWRA = self.data.proj['Total WRA'][0]
        rate = numPregnant/numWRA/(1.- self.fracPregnancyAverted)
        # reduce rate by % difference between births and pregnancies to get birth rate
        projectedBirths = self.data.proj['Number of births']
        projectedPWpop = self.data.proj['Estimated pregnant women']
        percentDiff = [ai/bi for ai,bi in zip(projectedBirths, projectedPWpop)]
        averagePercentDiff = sum(percentDiff) / float(len(percentDiff))
        self.pregnancyRate = rate
        self.birthRate = averagePercentDiff * rate

    def update_preg_averted(self, coverage): # TODO: don't like the way this is implemented
        if coverage == 0: # if missing or 0 cov
            self.fracPregnancyAverted = 0.
        else:
            self.fracPregnancyAverted = sum(self.data.famplan_methods[prog]['Effectiveness'] *
                self.data.famplan_methods[prog]['Distribution'] * coverage
                for prog in self.data.famplan_methods.iterkeys())

    def _set_time_trends(self):
        risk = 'Anaemia'
        trend = self.data.time_trends[risk]
        for age_group in self.age_groups:
            age_group.trends[risk] = fit_poly(1, trend)


def set_pops(data, default_params):
    children = Children(data, default_params)
    pregnantWomen = PregnantWomen(data, default_params)
    nonPregnantWomen = NonPregnantWomen(data, default_params)
    return [children, pregnantWomen, nonPregnantWomen]