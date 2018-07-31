from .utils import solve_quad, restratify, fit_poly, system, check_sol
from . import settings
import sciris.core as sc
from math import pow
import numpy as np
from scipy.optimize import fsolve
from functools import partial

class AgeGroup(object):
    def __init__(self, age, pop_size, anaemia_dist):
        self.age = age
        self.pop_size = pop_size
        self.ss = settings.Settings()
        self.anaemia_dist = sc.dcp(anaemia_dist)

        self.anaemiaUpdate = None

    def reset_storage(self):
        self.anaemiaUpdate = 1

    def frac_risk(self, risk):
        risk = risk.lower()
        if any(sub in risk for sub in ['an', 'anaem', 'amaemia', 'amaemic']):
            return self.frac_anaemic()
        else:
            raise Exception('::ERROR:: age group "{}" does not have "{}" attribute'.format(self.age, risk))

    def num_risk(self, risk):
        risk = risk.lower()
        if any(sub in risk for sub in ['an', 'anaem', 'amaemia', 'amaemic']):
            return self.num_anaemic()
        else:
            raise Exception('::ERROR:: age group "{}" does not have "{}" attribute'.format(self.age, risk))

    def frac_anaemic(self):
        return sum(self.anaemia_dist[cat] for cat in self.ss.anaemic_list)

    def num_anaemic(self):
        return self.pop_size * sum(self.anaemia_dist[cat] for cat in self.ss.anaemic_list)

    def num_notanaemic(self):
        num_notanamic = self.pop_size - (self.num_anaemic())
        return num_notanamic

class NonPWAgeGroup(AgeGroup):
    def __init__(self, age, pop_size, anaemia_dist, birth_space, correct_space):
        AgeGroup.__init__(self, age, pop_size, anaemia_dist)
        self.birth_space = sc.dcp(birth_space)
        self.correct_space = correct_space
        self.preg_av = 0 # initially 0, but updated if coverage changes
        self.probConditionalCoverage = {}
        self.trends = {}
        self.reset_storage()

    def reset_storage(self):
        super(NonPWAgeGroup, self).reset_storage()
        self.birthspace_update = self.birth_space[self.ss.optimal_space]

class PWAgeGroup(AgeGroup):
    def __init__(self, age, pop_size, anaemia_dist, ageingRate, causes_death, age_dist):
        AgeGroup.__init__(self, age, pop_size, anaemia_dist)
        self.mortality = np.zeros(len(self.ss.anaemia_list)) # flattened array
        self.ageingRate = ageingRate
        self.causes_death = sc.dcp(causes_death)
        self.age_dist = age_dist
        self.probConditionalCoverage = {}
        self.trends = {}
        self.reset_storage()

    def reset_storage(self):
        super(PWAgeGroup, self).reset_storage()
        # this update will impact Newborn age group
        self.birthUpdate = {}
        for BO in self.ss.birth_outcomes:
            self.birthUpdate[BO] = 1
        self.mortalityUpdate = {}
        for cause in self.causes_death:
            self.mortalityUpdate[cause] = 1

class ChildAgeGroup(AgeGroup):
    def __init__(self, age, pop_size, anaemia_dist, incidences, stunting_dist, wasting_dist, bf_dist,
                 ageingRate, causes_death, default_params, frac_severe_dia):
        AgeGroup.__init__(self, age, pop_size, anaemia_dist)
        self.mortality = np.zeros(len(self.ss.all_cats)) # flattened array
        self.stunting_dist = sc.dcp(stunting_dist)
        self.wasting_dist = sc.dcp(wasting_dist)
        self.bf_dist = sc.dcp(bf_dist)
        self.incidences = sc.dcp(incidences)
        self.causes_death = sc.dcp(causes_death)
        self.default = default_params
        self.frac_severe_dia = frac_severe_dia
        self.correct_bf = self.ss.correct_bf[age]
        self.incorrect_bf = list(set(self.ss.bf_list) - {self.correct_bf})
        self.ageingRate = ageingRate
        self.probConditionalCoverage = {}
        self.probConditionalDiarrhoea = {}
        self.probConditionalStunting = {}
        self.prog_eff = {}
        self.trends = {}
        self.reset_storage()
        self._updatesForAgeingAndBirths()

    def _updatesForAgeingAndBirths(self):
        """
        Stunting & wasting have impact on births and ageing, which needs to be adjusted at each time step
        :return:
        """
        self.continuedStuntingImpact = 1
        self.continuedWastingImpact = {}
        for wastingCat in self.ss.wasted_list:
            self.continuedWastingImpact[wastingCat] = 1

    def reset_storage(self):
        super(ChildAgeGroup, self).reset_storage()
        # storing updates
        self.stuntingUpdate = 1
        self.bfUpdate = {}
        self.diarrhoeaUpdate = {}
        self.bfPracticeUpdate = self.bf_dist[self.correct_bf]
        for risk in ['Stunting', 'Anaemia'] + self.ss.wasted_list:
            self.bfUpdate[risk] = 1
        self.mortalityUpdate = {}
        for cause in self.causes_death:
            self.mortalityUpdate[cause] = 1
        self.diarrhoeaIncidenceUpdate = 1
        self.diarrhoeaUpdate = {}
        for risk in self.ss.wasted_list + ['Stunting', 'Anaemia']:
            self.diarrhoeaUpdate[risk] = 1
        self.wastingPreventionUpdate = {}
        self.wastingTreatmentUpdate = {}
        for wastingCat in self.ss.wasted_list:
            self.wastingPreventionUpdate[wastingCat] = 1
            self.wastingTreatmentUpdate[wastingCat] = 1

    ###### POPULATION CALCULATIONS ######

    def frac_risk(self, risk):
        risk = risk.lower()
        if any(sub in risk for sub in ['stun', 'stunt', 'stunting', 'stunted']):
            return self.frac_stunted()
        elif any(sub in risk for sub in ['ma', 'mam']):
            return self.frac_wasted('MAM')
        elif any(sub in risk for sub in ['sa', 'sam']):
            return self.frac_wasted('SAM')
        elif any(sub in risk for sub in ['was', 'wast', 'wasting', 'wasted']):
            return sum(self.frac_wasted(cat) for cat in self.ss.wasted_list)
        elif any(sub in risk for sub in ['an', 'anaem', 'amaemia', 'amaemic']):
            return self.frac_anaemic()
        else:
            raise Exception('::ERROR:: age group "{}" does not have "{}" attribute'.format(self.age, risk))


    def num_risk(self, risk):
        risk = risk.lower()
        if any(sub in risk for sub in ['stun', 'stunt', 'stunting', 'stunted']):
            return self.num_stunted()
        elif any(sub in risk for sub in ['ma', 'mam']):
            return self.num_wasted('MAM')
        elif any(sub in risk for sub in ['sa', 'sam']):
            return self.num_wasted('SAM')
        elif any(sub in risk for sub in ['was', 'wast', 'wasting', 'wasted']):
            return sum(self.num_wasted(cat) for cat in self.ss.wasted_list)
        elif any(sub in risk for sub in ['an', 'anaem', 'amaemia', 'amaemic']):
            return self.num_anaemic()
        else:
            raise Exception('::ERROR:: age group "{}" does not have "{}" attribute'.format(self.age, risk))

    def num_stunted(self):
        return self.pop_size * sum(self.stunting_dist[cat] for cat in self.ss.stunted_list)

    def num_notstunted(self):
        return self.pop_size - (self.num_stunted())

    def num_wasted(self, cat):
        return self.pop_size * self.wasting_dist[cat]

    def num_notwasted(self):
        return self.pop_size - sum(self.num_wasted(cat) for cat in self.ss.wasted_list)

    def num_correctbf(self):
        return self.pop_size * self.bf_dist[self.correct_bf]

    def frac_stunted(self):
        return sum(self.stunting_dist[cat] for cat in self.ss.stunted_list)

    def frac_wasted(self, cat):
        return self.wasting_dist[cat]

    def _getFracDiarrhoeaFixedZ(self):
        beta = {}
        RRnot = self.default.rr_dia[self.age]['None']
        for bfCat in self.ss.bf_list:
            RDa = self.default.rr_dia[self.age][bfCat]
            beta[bfCat] = RDa/RRnot
        return beta

    def _getFracDiarrhoea(self, Z0, Zt):
        beta = {}
        RRnot = self.default.rr_dia[self.age]['None']
        for bfCat in self.ss.bf_list:
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
        return sum(self.default.rr_dia[self.age][bfCat] * self.bf_dist[bfCat] for bfCat in self.ss.bf_list)

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
        for wastingCat in self.ss.wasted_list:
            AO = self._getAverageOR(Zt, wastingCat)
            Omega0 = self.probConditionalDiarrhoea[wastingCat]['no diarrhoea']
            self.probConditionalDiarrhoea[wastingCat]['diarrhoea'] = Omega0 * AO / (1. - Omega0 + AO * Omega0)

class Newborn(ChildAgeGroup):
    def __init__(self, age, pop_size, anaemia_dist, incidences, stunting_dist, wasting_dist, bf_dist,
                 ageingRate, birth_dist, causes_death, default_params, frac_severe_dia):
        """
        This is the <1 month age group, distinguished from the other age groups by birth outcomes, spacing etc etc.
        """
        super(Newborn, self).__init__(age, pop_size, anaemia_dist, incidences, stunting_dist, wasting_dist, bf_dist,
                 ageingRate, causes_death, default_params, frac_severe_dia)
        self.birth_dist = birth_dist
        self.probRiskAtBirth = {}

####### Population classes #########

class Population(object):
    def __init__(self, name, data, default):
        self.name = name
        self.data = data
        self.default = default
        self.pop_areas = default.pop_areas
        self.ss = settings.Settings()
        self.age_groups = []

    def total_pop(self):
        return sum(age_group.pop_size for age_group in self.age_groups)

    def frac_risk(self, risk):
        risk = risk.lower()
        if any(sub in risk for sub in ['an', 'anaem', 'anaemia', 'anaemic']):
            return self.frac_anaemic()
        else:
            raise Exception('::ERROR:: population "{}" does not have "{}" attribute'.format(risk, self.name))

    def num_risk(self, risk):
        risk = risk.lower()
        if any(sub in risk for sub in ['an', 'anaem', 'anaemia', 'anaemic']):
            return self.num_anaemic()
        else:
            raise Exception('::ERROR:: population "{}" does not have "{}" attribute'.format(risk, self.name))

    def num_anaemic(self):
        return sum(age_group.num_anaemic() for age_group in self.age_groups)

    def frac_anaemic(self):
        return self.num_anaemic() / self.total_pop()

class Children(Population):
    def __init__(self, data, default_params):
        Population.__init__(self, 'Children', data, default_params)
        self.proj = sc.dcp(data.proj)
        self.birth_dist = self.data.demo['Birth dist']
        self.stunting_dist = self.data.risk_dist['Stunting']
        self.anaemia_dist = self.data.risk_dist['Anaemia']
        self.wasting_dist = self.data.risk_dist['Wasting']
        self.bf_dist = self.data.risk_dist['Breastfeeding']
        self.mamtosam = self.data.mamtosam
        self.samtomam = self.data.samtomam
        self._make_pop_sizes()
        self._make_age_groups()
        self._set_child_mortality()
        self.update_mortality()
        self._set_progeff()
        self._set_time_trends()
        self._set_correctbf()
        self._set_future_stunting()
        self._set_stunted_birth()
        self._set_wasted_birth()
        self._set_bo_space()

    ##### DATA WRANGLING ######

    def set_probs(self, prog_areas):
        self._set_prob_stunted(prog_areas)
        self._set_prob_anaem(prog_areas)
        self._set_prob_wasted(prog_areas)
        self._set_prob_bf(prog_areas)
        self._set_stunted_dia()
        self._set_anaemic_dia()
        self._set_wasted_dia()

    def frac_risk(self, risk):
        risk = risk.lower()
        if any(sub in risk for sub in ['stun', 'stunt', 'stunting', 'stunted']):
            return self.frac_stunted()
        elif any(sub in risk for sub in ['ma', 'mam']):
            return self.frac_wasted('MAM')
        elif any(sub in risk for sub in ['sa', 'sam']):
            return self.frac_wasted('SAM')
        elif any(sub in risk for sub in ['was', 'wast', 'wasting', 'wasted']):
            return sum(self.frac_wasted(cat) for cat in self.ss.wasted_list)
        if any(sub in risk for sub in ['an', 'anaem', 'anaemia', 'anaemic']):
            return self.frac_anaemic()
        else:
            raise Exception('::ERROR:: population "{}" does not have "{}" attribute'.format(risk, self.name))

    def num_risk(self, risk):
        risk = risk.lower()
        if any(sub in risk for sub in ['stun', 'stunt', 'stunting', 'stunted']):
            return self.num_stunted()
        elif any(sub in risk for sub in ['ma', 'mam']):
            return self.num_wasted('MAM')
        elif any(sub in risk for sub in ['sa', 'sam']):
            return self.num_wasted('SAM')
        elif any(sub in risk for sub in ['was', 'wast', 'wasting', 'wasted']):
            return sum(self.num_wasted(cat) for cat in self.ss.wasted_list)
        elif any(sub in risk for sub in ['an', 'anaem', 'anaemia', 'anaemic']):
            return self.frac_anaemic()
        else:
            raise Exception('::ERROR:: population "{}" does not have "{}" attribute'.format(risk, self.name))

    def num_stunted(self):
        return sum(age_group.num_stunted() for age_group in self.age_groups)

    def frac_stunted(self):
        return self.num_stunted() / self.total_pop()

    def num_wasted(self, cat):
        return sum(age_group.num_wasted(cat) for age_group in self.age_groups)

    def frac_wasted(self, cat):
        return self.num_wasted(cat) / self.total_pop()

    def _setConditionalDiarrhoea(self):
        self._set_stunted_dia()
        self._set_anaemic_dia()
        self._set_wasted_dia()

    def _make_pop_sizes(self):
        # for children less than 1 year, annual live births
        monthlyBirths = self.data.proj['Number of births'][0] / 12.
        popSize = [pop * monthlyBirths for pop in self.ss.child_age_spans[:3]]
        # children > 1 year, who are not counted in annual 'live births'
        months = sum(self.ss.child_age_spans[3:])
        popRemainder = self.data.proj['Children under 5'][0] - monthlyBirths * 12.
        monthlyRate = popRemainder/months
        popSize += [pop * monthlyRate for pop in self.ss.child_age_spans[3:]]
        self.popSizes = {age:pop for age, pop in zip(self.ss.child_ages, popSize)}

    def _make_age_groups(self):
        for i, age in enumerate(self.ss.child_ages):
            popSize = self.popSizes[age]
            stunting_dist = self.stunting_dist[age]
            stunting_dist = restratify(sum(stunting_dist[cat] for cat in self.ss.stunted_list))
            anaemia_dist = self.anaemia_dist[age]
            wasting_dist = self.wasting_dist[age]
            probWasted = sum(wasting_dist[cat] for cat in self.ss.wasted_list)
            nonwasting_dist = restratify(probWasted)
            for cat in self.ss.non_wasted_list:
                wasting_dist[cat] = nonwasting_dist[cat]
            bf_dist = self.bf_dist[age]
            birth_dist = self.birth_dist
            incidences = self.data.incidences[age]
            incidences = {condition: incidence * self.ss.timestep for condition, incidence in incidences.iteritems()}
            ageingRate = 1./self.ss.child_age_spans[i]
            if age == '<1 month': # <1 month age group has slightly different functionality
                self.age_groups.append(Newborn(age, popSize,
                                           anaemia_dist, incidences, stunting_dist, wasting_dist, bf_dist,
                                                ageingRate, birth_dist, self.data.causes_death, self.default,
                                               self.data.demo['Percentage of diarrhea that is severe']))
            else:
                self.age_groups.append(ChildAgeGroup(age, popSize,
                                           anaemia_dist, incidences, stunting_dist, wasting_dist, bf_dist,
                                                ageingRate, self.data.causes_death, self.default,
                                                     self.data.demo['Percentage of diarrhea that is severe']))

    def _set_child_mortality(self):
        # Equation is:  LHS = RHS * X
        # we are solving for X
        # Calculate RHS for each age and cause
        RHS = {}
        for age in self.ss.child_ages:
            RHS[age] = {}
            for cause in self.data.causes_death:
                RHS[age][cause] = 0.
                for stuntingCat in self.ss.stunting_list:
                    for wastingCat in self.ss.wasting_list:
                        for bfCat in self.ss.bf_list:
                            for anaemiaCat in self.ss.anaemia_list:
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
            for breastfeedingCat in self.ss.bf_list:
                Pbf = self.bf_dist[age][breastfeedingCat]
                RRbf = self.default.rr_death['Breastfeeding'][age][breastfeedingCat].get(cause,1)
                for birthoutcome in self.ss.birth_outcomes:
                    Pbo = self.birth_dist[birthoutcome]
                    RRbo = self.default.rr_death['Birth outcomes'][birthoutcome].get(cause,1)
                    for anaemiaCat in self.ss.anaemia_list:
                        Pan = self.anaemia_dist[age][anaemiaCat]
                        RRan = self.default.rr_death['Anaemia'][age][anaemiaCat].get(cause,1)
                        RHS[age][cause] += Pbf * RRbf * Pbo * RRbo * Pan * RRan
        # calculate total mortality by age (corrected for units)
        AgePop = [_age.pop_size for _age in self.age_groups]
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
            for c,cause in enumerate(self.data.causes_death):
                LHS_age_cause = MortalityCorrected[age] * self.data.death_dist[cause][age]
                age_group.referenceMortality[cause] = LHS_age_cause / RHS[age][cause]

    def update_mortality(self):
        # Newborns first
        age_group = self.age_groups[0]
        age = age_group.age
        for bfCat in self.ss.bf_list:
            count = 0.
            for cause in self.data.causes_death:
                Rb = self.default.rr_death['Breastfeeding'][age][bfCat].get(cause,1)
                for outcome in self.ss.birth_outcomes:
                    pbo = age_group.birth_dist[outcome]
                    Rbo = self.default.rr_death['Birth outcomes'][outcome].get(cause,1)
                    count += Rb * pbo * Rbo * age_group.referenceMortality[cause]
            age_group.mortality[:] = count
        # over 1 months
        
        for age_group in self.age_groups[1:]:
            age = age_group.age
            refmort = np.zeros(len(self.data.causes_death))
            for c,cause in enumerate(self.data.causes_death):
                refmort[c] = age_group.referenceMortality[cause] # Copy to an array for faster calculations
            for i,cats in enumerate(self.ss.all_cats):
                rr_death = self.default.arr_rr_death[age][i,:]
                age_group.mortality[i] = sum(refmort*rr_death)

    def _set_future_stunting(self):
        """Calculate the probability of stunting given previous stunting between age groups"""
        for i, age_group in enumerate(self.age_groups[1:],1):
            thisAge = age_group.age
            prevAgeGroup = self.age_groups[i-1]
            OR = self.default.or_cond['Stunting']['Prev stunting'][thisAge]
            fracStuntedThisAge = age_group.frac_stunted()
            fracStuntedPrev = prevAgeGroup.frac_stunted()
            pn, pc = solve_quad(OR, fracStuntedPrev, fracStuntedThisAge)
            age_group.probConditionalStunting['stunted'] = pc
            age_group.probConditionalStunting['not stunted'] = pn

    def _set_prob_stunted(self, prog_areas):
        risk = 'Stunting'
        relev_progs = prog_areas[risk]
        for age_group in self.age_groups:
            age = age_group.age
            fracStunted = sum(age_group.stunting_dist[cat] for cat in self.ss.stunted_list)
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
            fracAnaemic = sum(age_group.anaemia_dist[cat] for cat in self.ss.anaemic_list)
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

    def _set_prob_bf(self, prog_areas):
        risk = 'Breastfeeding'
        relev_progs = prog_areas[risk]
        for age_group in self.age_groups:
            age = age_group.age
            age_group.probConditionalCoverage[risk] = {}
            fracAppropriate = age_group.bf_dist[age_group.correct_bf]
            for program in relev_progs:
                age_group.probConditionalCoverage[risk][program] = {}
                OR = self.default.or_bf_prog[program][age]
                fracCovered = self.previousCov[program]
                pn, pc = solve_quad(OR, fracCovered, fracAppropriate)
                age_group.probConditionalCoverage[risk][program]['covered'] = pc
                age_group.probConditionalCoverage[risk][program]['not covered'] = pn

    def _set_prob_wasted(self, prog_areas):
        risk = 'Wasting treatment' # only treatment have ORs for wasting
        relev_progs = prog_areas[risk]
        for wastingCat in self.ss.wasted_list:
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

    def _set_stunted_dia(self):
        risk = 'Stunting'
        for age_group in self.age_groups:
            age_group.probConditionalDiarrhoea[risk] = {}
            Z0 = age_group._getZa()
            Zt = Z0 # true for initialisation
            beta = age_group._getFracDiarrhoea(Z0, Zt)
            AO = age_group._getAverageOR(Zt, risk)
            fracDiarrhoea = sum(beta[bfCat] * age_group.bf_dist[bfCat] for bfCat in self.ss.bf_list)
            fracImpactedThisAge = sum(age_group.stunting_dist[cat] for cat in self.ss.stunted_list)
            pn, pc = solve_quad(AO, fracDiarrhoea, fracImpactedThisAge)
            age_group.probConditionalDiarrhoea[risk]['diarrhoea'] = pc
            age_group.probConditionalDiarrhoea[risk]['no diarrhoea'] = pn

    def _set_anaemic_dia(self):
        risk = 'Anaemia'
        for age_group in self.age_groups:
            age_group.probConditionalDiarrhoea[risk] = {}
            Z0 = age_group._getZa()
            Zt = Z0 # true for initialisation
            beta = age_group._getFracDiarrhoea(Z0, Zt)
            Yt = Zt * self.data.demo['Percentage of diarrhea that is severe']
            AO = age_group._getAverageOR(Yt, risk)
            fracDiarrhoea = sum(beta[bfCat] * age_group.bf_dist[bfCat] for bfCat in self.ss.bf_list)
            fracimp = age_group.frac_anaemic()
            pn, pc = solve_quad(AO, fracDiarrhoea, fracimp)
            age_group.probConditionalDiarrhoea[risk]['diarrhoea'] = pc
            age_group.probConditionalDiarrhoea[risk]['no diarrhoea'] = pn

    def _set_wasted_dia(self):
        for age_group in self.age_groups:
            Z0 = age_group._getZa()
            Zt = Z0 # true for initialisation
            beta = age_group._getFracDiarrhoea(Z0, Zt)
            for wastingCat in self.ss.wasted_list:
                A0 = age_group._getAverageOR(Zt, wastingCat)
                age_group.probConditionalDiarrhoea[wastingCat] = {}
                fracDiarrhoea = sum(beta[bfCat] * age_group.bf_dist[bfCat] for bfCat in self.ss.bf_list)
                fracThisCat = age_group.wasting_dist[wastingCat]
                pn, pc = solve_quad(A0, fracDiarrhoea, fracThisCat)
                age_group.probConditionalDiarrhoea[wastingCat]['no diarrhoea'] = pn
                age_group.probConditionalDiarrhoea[wastingCat]['diarrhoea'] = pc

    def _set_stunted_birth(self):
        """Sets the probabilty of stunting conditional on birth outcome"""
        newborns = self.age_groups[0]
        probs = self._solve_system('Stunting')
        newborns.probRiskAtBirth['Stunting'] = {cat:prob for cat,prob in
                                                zip(self.ss.birth_outcomes, probs)}

    def _set_wasted_birth(self):
        newborns = self.age_groups[0]
        probWastedAtBirth = {}
        for wastingCat in self.ss.wasted_list:
            probs = self._solve_system(wastingCat)
            probWastedAtBirth[wastingCat] = {cat: prob for cat, prob in
                                                    zip(self.ss.birth_outcomes,
                                                        probs)}
        newborns.probRiskAtBirth['Wasting'] = probWastedAtBirth

    def _set_bo_space(self):
        """ Find the probability of a birth outcome conditional on birth spacing.
        Using law of total probability and definition of relative risks,
         we solve for P(BOi | space1), and use this to solve for the rest"""
        newborns = self.age_groups[0]
        prob_bospace = sc.odict()
        birth_space = self.data.birth_space
        RRs = self.default.rr_space_bo
        for bo in self.ss.birth_outcomes:
            # get P(BO | space1)
            prob_bospace[bo] = sc.odict()
            fracbo = newborns.birth_dist[bo]
            p1 = fracbo / sum(RRs[name][bo] * birth_space[name] for name in birth_space.iterkeys())
            for name in birth_space.iterkeys():
                prob_bospace[bo][name] = RRs[name][bo] * p1
        newborns.prob_bospace = prob_bospace

    def _solve_system(self, risk):
        OR = [1.] * 4
        OR[1] = self.default.or_cond_bo[risk]["Term SGA"]
        OR[2] = self.default.or_cond_bo[risk]["Pre-term AGA"]
        OR[3] = self.default.or_cond_bo[risk]["Pre-term SGA"]
        newborns = self.age_groups[0]
        bo = [0.] * 4
        bo[0] = newborns.birth_dist["Term AGA"]
        bo[1] = newborns.birth_dist["Term SGA"]
        bo[2] = newborns.birth_dist["Pre-term AGA"]
        bo[3] = newborns.birth_dist["Pre-term SGA"]
        p0 = newborns.frac_risk(risk)
        sol = fsolve(partial(system, OR, bo, p0), (0.5, 0.5, 0.5, 0.5), xtol=1e-12)
        check_sol(sol)
        return sol

    def _set_progeff(self):
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

    def _set_correctbf(self):
        for age_group in self.age_groups:
            age = age_group.age
            age_group.correct_bf = self.ss.correct_bf[age]

class PregnantWomen(Population):
    def __init__(self, data, default_params):
        Population.__init__(self, 'Pregnant women', data, default_params)
        self.proj = sc.dcp(data.proj)
        self.age_dist = data.pw_agedist
        self.anaemia_dist = self.data.risk_dist['Anaemia']
        self._make_pop_sizes()
        self._make_age_groups()
        self._setPWReferenceMortality()
        self.update_mortality()
        self._set_progeff()
        self._set_time_trends()

    ##### DATA WRANGLING ######

    def _set_progeff(self):
        for age_group in self.age_groups:
            age = age_group.age
            age_group.prog_eff = self.default.pw_progs[age]
            # effectiveness for birth outcomes
            age_group.bo_eff = self.default.bo_progs

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

    def _make_age_groups(self):
        for i, age in enumerate(self.ss.pw_ages):
            popSize = self.popSizes[i]
            anaemia_dist = self.anaemia_dist[age]
            ageingRate = self.ss.women_age_rates[i]
            age_dist = self.data.pw_agedist[i]
            self.age_groups.append(PWAgeGroup(age, popSize, anaemia_dist, ageingRate,
                                              self.data.causes_death, age_dist))

    def _setPWReferenceMortality(self):
        #Equation is:  LHS = RHS * X
        #we are solving for X
        # Calculate RHS for each age and cause
        RHS = {}
        for age in self.ss.pw_ages:
            RHS[age] = {}
            for cause in self.data.causes_death:
                RHS[age][cause] = 0.
                for anaemiaCat in self.ss.anaemia_list:
                    t1 = self.anaemia_dist[age][anaemiaCat]
                    t2 = self.default.rr_death['Anaemia'][age][anaemiaCat].get(cause,1)
                    RHS[age][cause] += t1 * t2
        # get age populations
        agePop = [age.pop_size for age in self.age_groups]
        # Correct raw mortality for units (per 1000 live births)
        liveBirths = self.data.proj['Number of births'][0]
        # The following assumes we only have a single mortality rate for PW
        mortalityRate = self.data.demo['Maternal mortality (per 1,000 live births)']
        mortalityCorrected = {}
        for index in range(len(self.ss.pw_ages)):
            age = self.ss.pw_ages[index]
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
            for i, cat in enumerate(self.ss.anaemia_list):
                count = 0
                for cause in self.data.causes_death:
                    t1 = age_group.referenceMortality[cause]
                    t2 = self.default.rr_death['Anaemia'][age][cat].get(cause,1)
                    count += t1 * t2
                age_group.mortality[i] = count

    def _set_prob_anaem(self, prog_areas):
        risk = 'Anaemia'
        relev_progs = prog_areas[risk]
        for age_group in self.age_groups:
            age = age_group.age
            age_group.probConditionalCoverage[risk] = {}
            for program in relev_progs:
                age_group.probConditionalCoverage[risk][program] = {}
                fracCovered = self.previousCov[program]
                fracImpacted = sum(age_group.anaemia_dist[cat] for cat in self.ss.anaemic_list)
                if self.default.or_anaem_prog.get(program) is None:
                    RR = self.default.rr_anaem_prog[program][age]
                    pn = fracImpacted / (RR * fracCovered + (1. - fracCovered))
                    pc = RR * pn
                else:
                    OR = self.default.or_anaem_prog[program][age]
                    pn, pc = solve_quad(OR, fracCovered, fracImpacted)
                age_group.probConditionalCoverage[risk][program]['covered'] = pc
                age_group.probConditionalCoverage[risk][program]['not covered'] = pn

class NonPregnantWomen(Population):
    def __init__(self, data, default_params):
        Population.__init__(self, 'Non-pregnant women', data, default_params)
        self.anaemia_dist = self.data.risk_dist['Anaemia']
        self.proj = {age:pops for age, pops in data.proj.iteritems() if age in self.ss.wra_ages + ['Total WRA']}
        self._make_pop_sizes()
        self._make_age_groups()
        self._set_time_trends()

    ##### DATA WRANGLING ######

    def set_probs(self, prog_areas):
        self._set_prob_anaem(prog_areas)
        self._set_prob_space(prog_areas)

    def get_pregav(self):
        return sum(age_group.preg_av for age_group in self.age_groups)

    def _make_pop_sizes(self):
        wra_proj = self.data.wra_proj
        self.popSizes = [proj[0] for proj in wra_proj]

    def _make_age_groups(self):
        for i, age in enumerate(self.ss.wra_ages):
            popSize = self.popSizes[i]
            anaemia_dist = self.anaemia_dist[age]
            self.age_groups.append(NonPWAgeGroup(age, popSize, anaemia_dist, self.data.birth_space,
                                                 self.ss.optimal_space))

    def _set_prob_anaem(self, prog_areas):
        risk = 'Anaemia'
        relev_progs = prog_areas[risk]
        for age_group in self.age_groups:
            age = age_group.age
            age_group.probConditionalCoverage[risk] = {}
            for program in relev_progs:
                age_group.probConditionalCoverage[risk][program] = {}
                fracCovered = self.previousCov[program]
                fracImpacted = sum(age_group.anaemia_dist[cat] for cat in self.ss.anaemic_list)
                if self.default.or_anaem_prog.get(program) is None:
                    RR = self.default.rr_anaem_prog[program][age]
                    pn = fracImpacted / (RR * fracCovered + (1. - fracCovered))
                    pc = RR * pn
                else:
                    OR = self.default.or_anaem_prog[program][age]
                    pn, pc = solve_quad(OR, fracCovered, fracImpacted)
                age_group.probConditionalCoverage[risk][program]['covered'] = pc
                age_group.probConditionalCoverage[risk][program]['not covered'] = pn

    def _set_prob_space(self, prog_areas):
        risk = 'Birth spacing'
        relev_progs = prog_areas[risk]
        for age_group in self.age_groups:
            age = age_group.age
            age_group.probConditionalCoverage[risk] = {}
            frac_correct = age_group.birth_space[age_group.correct_space]
            for prog in relev_progs:
                age_group.probConditionalCoverage[risk][prog] = {}
                OR = self.default.or_space_prog[prog][age]
                frac_cov = self.previousCov[prog]
                pn, pc = solve_quad(OR, frac_cov, frac_correct)
                age_group.probConditionalCoverage[risk][prog]['covered'] = pc
                age_group.probConditionalCoverage[risk][prog]['not covered'] = pn

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