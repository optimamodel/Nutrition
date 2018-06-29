import numpy as np
from .utils import restratify
from . import settings

def default_trackers():
    ''' Not sure if his should be a function or just a definition -- store the key outputs of the model '''
    output = [
        'stunting_prev',
        'wasting_prev',
        'anaemia_prev',
        'child_deaths',
        'pw_deaths',
        'child_exit',
        'pw_exit',
        'stunted',
        'thrive',
        'child_not_anaemic',
        'neo_deaths',
        'births',
        'child_healthy']
    return output

class Model:
    def __init__(self, name, pops, prog_info, all_years, adjust_cov=False, timeTrends=False):
        self.name = name
        self.pops = pops
        self.children, self.pw, self.nonpw = self.pops
        self.prog_info = prog_info
        self.settings = settings.Settings()

        # get key items
        self.n_years = len(all_years)
        self.all_years = all_years
        self.base_year = self.all_years[0]
        self.year = self.base_year

        self.calib_years = []
        self.sim_years = self.all_years[1:]

        self._set_trackers()

        # set requirements for populations -- conditional probs
        self.setup()
        self.calibrate()

        self.adjust_cov = adjust_cov
        self.timeTrends = timeTrends

    def setup(self):
        self.set_progs()
        self._set_preg_info()
        self._set_pop_probs(self.base_year)
        self._reset_storage()
        self._track_prevs()

    def set_progs(self):
        self.prog_info.set_years(self.all_years)
        self.prog_info.set_init_covs(self.pops, self.all_years)
        self.prog_info.set_costcovs() # enables getting coverage from cost

    def calibrate(self):
        for year in self.calib_years:
            self.update_year(year)
            self._set_pop_probs(year)
            self._reset_storage()
            self._apply_prog_covs()
            self._distrib_pops()
            self.integrate()
    
    def _set_trackers(self):
        """ Lists to store outcomes """
        for tracker in default_trackers():
            arr = np.zeros(self.n_years)
            setattr(self, tracker, arr)

    def _track_outcomes(self):
        oldest = self.children.age_groups[-1]
        self.stunted[self.year] += oldest.get_num_stunted() * oldest.ageingRate
        self.thrive[self.year] += oldest.get_num_notstunted() * oldest.ageingRate
        self.child_not_anaemic[self.year] += oldest.get_num_notanaemic() * oldest.ageingRate

    def _track_prevs(self):
        self.stunting_prev[self.year] = self.children.getTotalFracStunted()
        self.wasting_prev[self.year] = self.children.getTotalFracWasted()
        self.anaemia_prev[self.year] = [pop.getTotalNumberAnaemic() for pop in self.pops][0] / \
                                       [pop.get_totalpop() for pop in self.pops][0]

    def _set_pop_probs(self, year):
        init_cov = self.prog_info.get_ann_covs(year-1)
        prog_areas = self.prog_info.prog_areas
        for pop in self.pops:
            pop.previousCov = init_cov
            pop.set_probs(prog_areas)

    def _reset_storage(self):
        for pop in self.pops:
            for age_group in pop.age_groups:
                age_group.set_update_storage()

    def update_year(self, year):
        self.year = year
        self.prog_info.update_prog_year(year)

    def run_sim(self, covs, restr_cov=True):
        self.prog_info.update_prog_covs(self.pops, covs, restr_cov)
        for year in self.sim_years:
            self.update_year(year)
            # determine if there are cov changes from previous year
            change = self.prog_info.determine_cov_change()
            if change:
                # update for next year
                self._set_pop_probs(year)
                self._reset_storage()
                self._apply_prog_covs()
            if self.adjust_cov: # account for pop growth
                self.prog_info.adjust_covs(self.pops, year)
            self.integrate()
            self._track_prevs()

    def _apply_prog_covs(self):
        # update populations
        for pop in self.pops:
            self._update_pop(pop)
            if pop.name == 'Non-pregnant women': # TODO: don't like this.
                self._famplan_update(pop)
            # combine direct and indirect updates to each risk area that we model
            self._combine_updates(pop)
            self._update_dists(pop)
            self._update_pop_mort(pop)

    def integrate(self):
        self._move_children()
        self._apply_pw_mort()
        self._update_pw()
        self._update_wra_pop()

    def _set_preg_info(self):
        FP = [prog for prog in self.prog_info.programs if prog.name == 'Family Planning']
        if FP:
            FPprog = FP[0]
            self.nonpw._setBPInfo(FPprog.unrestr_init_cov)
        else:
            self.nonpw._setBPInfo(0) # TODO: not best way to handle missing program

    def _famplan_update(self, pop):
        """ This update is not age-specified but instead applies to all non-pw.
        Also uses programs which are not explicitly treated elsewhere in model"""
        progList = self._applicable_progs('Family planning') # returns 'Family Planning' program
        if progList:
            prog = progList[0]
            pop.update_preg_averted(prog.annual_cov[self.year])

    def _update_pop_mort(self, pop):
        if pop.name != 'Non-pregnant women':
            pop.update_mortality()

    def _applicable_progs(self, risk):
        applicableProgNames = self.prog_info.prog_areas[risk]
        programs = list(filter(lambda x: x.name in applicableProgNames, self.prog_info.programs))
        return programs

    def _applicable_ages(self, population, risk):
        applicableAgeNames = population.pop_areas[risk]
        age_groups = list(filter(lambda x: x.age in applicableAgeNames, population.age_groups))
        return age_groups

    def _update_pop(self, population):
        for risk in self.prog_info.prog_areas.iterkeys():
            # get relevant programs and age groups, determined by risk area
            applicableProgs = self._applicable_progs(risk)
            age_groups = self._applicable_ages(population, risk)
            for age_group in age_groups:
                for program in applicableProgs:
                    if age_group.age in program.agesImpacted:
                        if risk == 'Stunting':
                            program.stunting_update(age_group)
                        elif risk == 'Anaemia':
                            program.anaemia_update(age_group)
                        elif risk == 'Wasting prevention':
                            program.wasting_prevent_update(age_group)
                        elif risk == 'Wasting treatment':
                            program.wasting_treat_update(age_group)
                        elif risk == 'Breastfeeding':
                            program.bf_update(age_group)
                        elif risk == 'Diarrhoea':
                            program.dia_incidence_update(age_group)
                        elif risk == 'Mortality':
                            program.get_mortality_update(age_group)
                        elif risk == 'Birth outcomes':
                            program.get_bo_update(age_group)
                        # elif risk == 'Birth age': # TODO: change implementation from previous mode version -- Calculate probabilities using RR etc.
                        #     program.get_birthage_update(age_group)
                        else:
                            print ":: Risk _{}_ not found. No update applied ::".format(risk)
                            continue
                    else:
                        continue
                if risk == 'Breastfeeding':  # flow on effects to diarrhoea (does not diarrhoea incidence & is independent of below)
                    self._bf_effects(age_group)
                if risk == 'Diarrhoea': # flow-on effects from incidence
                    self._dia_indirect_effects(age_group)
                if risk == 'Wasting treatment':
                    # need to account for flow between MAM and SAM
                    self._wasting_trans(age_group)

    def _combine_updates(self, population):
        """
        Each risk area modelled can be impacted from direct and indirect pathways, so we combine these here
        :param population:
        :return:
        """
        if population.name == 'Children':
            for age_group in population.age_groups:
                # stunting: direct, diarrhoea, breastfeeding
                age_group.totalStuntingUpdate = age_group.stuntingUpdate * age_group.diarrhoeaUpdate['Stunting'] \
                                               * age_group.bfUpdate['Stunting']
                age_group.continuedStuntingImpact *= age_group.totalStuntingUpdate
                # anaemia: direct, diarrhoea, breastfeeding
                age_group.totalAnaemiaUpdate = age_group.anaemiaUpdate * age_group.diarrhoeaUpdate['Anaemia'] \
                                              * age_group.bfUpdate['Anaemia']
                # wasting: direct (prevalence, incidence), flow between MAM & SAM, diarrhoea, breastfeeding
                age_group.totalWastingUpdate = {}
                for wastingCat in self.settings.wasted_list:
                    age_group.totalWastingUpdate[wastingCat] = age_group.wastingTreatmentUpdate[wastingCat] \
                                                  * age_group.wastingPreventionUpdate[wastingCat] \
                                                  * age_group.bfUpdate[wastingCat] \
                                                  * age_group.diarrhoeaUpdate[wastingCat] \
                                                  * age_group.fromMAMtoSAMupdate[wastingCat] \
                                                  * age_group.fromSAMtoMAMupdate[wastingCat]
                    age_group.continuedWastingImpact[wastingCat] *= age_group.totalWastingUpdate[wastingCat]
        elif population.name == 'Pregnant women':
            for age_group in population.age_groups:
                age_group.totalAnaemiaUpdate = age_group.anaemiaUpdate
        elif population.name == 'Non-pregnant women':
            for age_group in population.age_groups:
                age_group.totalAnaemiaUpdate = age_group.anaemiaUpdate
                age_group.totalBAUpdate = age_group.birthAgeUpdate

    def _update_dists(self, population):
        """
        Uses assumption that each age_group in a population has a default update
        value which exists (not across populations though)
        :return:
        """
        if population.name == 'Children':
            for age_group in population.age_groups:
                for cause in age_group.causes_death:
                    age_group.referenceMortality[cause] *= age_group.mortalityUpdate[cause]
                # stunting
                oldProbStunting = age_group.getFracRisk('Stunting')
                newProbStunting = oldProbStunting * age_group.totalStuntingUpdate
                age_group.stunting_dist = restratify(newProbStunting)
                # anaemia
                oldProbAnaemia = age_group.getFracRisk('Anaemia')
                newProbAnaemia = oldProbAnaemia * age_group.totalAnaemiaUpdate
                age_group.anaemia_dist['Anaemic'] = newProbAnaemia
                age_group.anaemia_dist['Not anaemic'] = 1.-newProbAnaemia
                # wasting
                newProbWasted = 0.
                for wastingCat in self.settings.wasted_list:
                    oldProbThisCat = age_group.getWastedFrac(wastingCat)
                    newProbThisCat = oldProbThisCat * age_group.totalWastingUpdate[wastingCat]
                    age_group.wasting_dist[wastingCat] = newProbThisCat
                    newProbWasted += newProbThisCat
                # normality constraint on non-wasted proportions only
                nonWastedDist = restratify(newProbWasted)
                for nonWastedCat in self.settings.non_wasted_list:
                    age_group.wasting_dist[nonWastedCat] = nonWastedDist[nonWastedCat]
        elif population.name == 'Pregnant women':
            # update pw anaemia but also birth distribution for <1 month age group
            # update birth distribution
            newBorns = self.children.age_groups[0]
            #PWpopSize = population.get_totalpop()
            # weighted sum accounts for different effects and target pops across pw age groups.
            firstPW = self.pw.age_groups[0]
            for BO in self.settings.birth_outcomes:
                newBorns.birth_dist[BO] *= firstPW.birthUpdate[BO]
            newBorns.birth_dist['Term AGA'] = 1. - sum(newBorns.birth_dist[BO] for BO in list(set(self.settings.birth_outcomes) - {'Term AGA'}))
            # update anaemia distribution
            for age_group in population.age_groups:
                # mortality
                for cause in age_group.causes_death:
                    age_group.referenceMortality[cause] *= age_group.mortalityUpdate[cause]
                oldProbAnaemia = age_group.getFracRisk('Anaemia')
                newProbAnaemia = oldProbAnaemia * age_group.totalAnaemiaUpdate
                age_group.anaemia_dist['Anaemic'] = newProbAnaemia
                age_group.anaemia_dist['Not anaemic'] = 1.-newProbAnaemia
        elif population.name == 'Non-pregnant women':
            for age_group in population.age_groups:
                # anaemia
                oldProbAnaemia = age_group.getFracRisk('Anaemia')
                newProbAnaemia = oldProbAnaemia * age_group.totalAnaemiaUpdate
                age_group.anaemia_dist['Anaemic'] = newProbAnaemia
                age_group.anaemia_dist['Not anaemic'] = 1.-newProbAnaemia
            # weighted sum account for different effect and target pops across nonpw age groups # TODO: is this true or need to scale by frac targeted?
            # nonPWpop = population.get_totalpop()
            # FPcov = sum(nonPWage.FPupdate * nonPWage.pop_size for nonPWage in population.age_groups) / nonPWpop
            # population.update_preg_averted(FPcov)

    def _wasting_trans(self, age_group):
        """Calculates the transitions between MAM and SAM categories"""
        age_group.fromSAMtoMAMupdate = {}
        age_group.fromMAMtoSAMupdate = {}
        age_group.fromSAMtoMAMupdate['MAM'] = (1. + (1.-age_group.wastingTreatmentUpdate['SAM']) * self.children.samtomam)
        age_group.fromSAMtoMAMupdate['SAM'] = 1.
        age_group.fromMAMtoSAMupdate['SAM'] = (1. - (1.-age_group.wastingTreatmentUpdate['MAM']) * self.children.mamtosam)
        age_group.fromMAMtoSAMupdate['MAM'] = 1.

    def _dia_indirect_effects(self, age_group):
        # get flow-on effects to stunting, anaemia and wasting
        Z0 = age_group._getZa()
        age_group.incidences['Diarrhoea'] *= age_group.diarrhoeaIncidenceUpdate
        Zt = age_group._getZa() # updated incidence
        beta = age_group._getFracDiarrhoea(Z0, Zt)
        age_group._updateProbConditionalDiarrhoea(Zt)
        for risk in ['Stunting', 'Anaemia']:
            age_group.diarrhoeaUpdate[risk] *= self._frac_dia_update(beta, age_group, risk)
        wastingUpdate = self._wasting_update_dia(beta, age_group)
        for wastingCat in self.settings.wasted_list:
            age_group.diarrhoeaUpdate[wastingCat] *= wastingUpdate[wastingCat]

    def _bf_effects(self, age_group):
        oldProb = age_group.bf_dist[age_group.correct_bf]
        percentIncrease = (age_group.bfPracticeUpdate - oldProb)/oldProb
        # get number at risk before
        sumBefore = age_group._getDiarrhoeaRiskSum()
        # update distribution of incorrect practices
        popSize = age_group.pop_size
        numCorrectBefore = age_group.getNumberCorrectlyBF()
        numCorrectAfter = popSize * age_group.bfPracticeUpdate
        numShifting = numCorrectAfter - numCorrectBefore
        numIncorrectBefore = popSize - numCorrectBefore
        fracCorrecting = numShifting / numIncorrectBefore if numIncorrectBefore > 0.01 else 0.
        # update breastfeeding distribution
        for practice in age_group.incorrect_bf:
            age_group.bf_dist[practice] *= 1. - fracCorrecting
        if percentIncrease > 0.0001:
            age_group.bf_dist[age_group.correct_bf] = age_group.bfPracticeUpdate
        # number at risk after
        sumAfter = age_group._getDiarrhoeaRiskSum()
        # update diarrhoea incidence baseline, even though not directly used in this calculation
        age_group.incidences['Diarrhoea'] *= sumAfter / sumBefore
        beta = age_group._getFracDiarrhoeaFixedZ()  # TODO: this could probably be calculated prior to update coverages
        for risk in ['Stunting', 'Anaemia']:
            age_group.bfUpdate[risk] = self._frac_dia_update(beta, age_group, risk)
        age_group.bfUpdate.update(self._wasting_update_dia(beta, age_group))

    def _frac_dia_update(self, beta, age_group, risk):
        oldProb = age_group.getRiskFromDist(risk)
        newProb = 0.
        probThisRisk = age_group.probConditionalDiarrhoea[risk]
        for bfCat in self.settings.bf_list:
            pab = age_group.bf_dist[bfCat]
            t1 = beta[bfCat] * probThisRisk['diarrhoea']
            t2 = (1.-beta[bfCat]) * probThisRisk['no diarrhoea']
            newProb += pab * (t1 + t2)
        reduction = (oldProb - newProb) / oldProb
        update = 1. - reduction
        return update

    def _wasting_update_dia(self, beta, age_group):
        update = {}
        for wastingCat in self.settings.wasted_list:
            update[wastingCat] = 1.
            probWasted = age_group.probConditionalDiarrhoea[wastingCat]
            oldProb = age_group.wasting_dist[wastingCat]
            newProb = 0.
            for bfCat in self.settings.bf_list:
                pab = age_group.bf_dist[bfCat]
                t1 = beta[bfCat] * probWasted['diarrhoea']
                t2 = (1.-beta[bfCat]) * probWasted['no diarrhoea']
                newProb += pab*(t1+t2)
            reduction = (oldProb - newProb)/oldProb
            update[wastingCat] *= 1. - reduction
        return update

    def _apply_child_mort(self):
        age_groups = self.children.age_groups
        for age_group in age_groups:
            for i, cats in enumerate(self.settings.all_cats):
                thisPop = age_group.pop_size * age_group.stunting_dist[cats[0]] * age_group.wasting_dist[cats[1]] * \
                          age_group.anaemia_dist[cats[2]] * age_group.bf_dist[cats[3]]
                deaths = thisPop * age_group.mortality[i] * self.settings.timestep
                age_group.pop_size -= deaths
                self.child_deaths[self.year] += deaths
                import traceback; traceback.print_exc(); import pdb; pdb.set_trace()

    def _apply_child_ageing(self):
        self._track_outcomes()
        # get number ageing out of each age group
        age_groups = self.children.age_groups
        ageingOut = []
        for i, age_group in enumerate(age_groups):
            ageingOut.append(age_group.pop_size * age_group.ageingRate)
            # age children
            age_group.pop_size -= ageingOut[i]
        numAgeingIn = {}
        for i in range(1, len(age_groups)):
            prev_age = age_groups[i-1]
            age_group = age_groups[i]
            numAgeingIn['stunted'] = ageingOut[i-1] * sum(prev_age.stunting_dist[cat] for cat in self.settings.stunted_list)
            numAgeingIn['not stunted'] = ageingOut[i-1] * sum(prev_age.stunting_dist[cat] for cat in self.settings.non_stunted_list)
            # those ageing in moving into the 4 categories
            numAgeingInStratified = {}
            for stuntingCat in self.settings.stunting_list:
                numAgeingInStratified[stuntingCat] = 0.
            for prevStunt in ['stunted', 'not stunted']:
                totalProbStunted = age_group.probConditionalStunting[prevStunt] * age_group.continuedStuntingImpact
                restratifiedProb = restratify(totalProbStunted)
                numaged = numAgeingIn[prevStunt]
                for stuntingCat in self.settings.stunting_list:
                    numAgeingInStratified[stuntingCat] += restratifiedProb[stuntingCat] * numaged
            # update distribution in each age group
            # (number of new children stunted + number of old stunted) / (new + old children)
            popgrowth = sum(numAgeingIn.values())
            extra_stunted = sum(numAgeingInStratified[cat] for cat in self.settings.stunted_list)
            probStunting = (extra_stunted + age_group.get_num_stunted()) / (popgrowth + age_group.pop_size)
            # add children
            age_group.pop_size += popgrowth
            # new distribution
            age_group.stunting_dist = restratify(probStunting)

    def _apply_births(self):
        # num annual births = birth rate x num WRA x (1 - frac preg averted)
        numWRA = self.nonpw.proj['Total WRA'][self.year]
        births = self.nonpw.birthRate * numWRA * (1. - self.nonpw.fracPregnancyAverted)
        # calculate total number of new babies and add to cumulative births
        numNewBabies = births * self.settings.timestep
        self.births[self.year] += numNewBabies
        # restratify stunting and wasting
        newBorns = self.children.age_groups[0]
        # add births to population size
        newBorns.pop_size += numNewBabies
        restratifiedStuntingAtBirth = {}
        restratifiedWastingAtBirth = {}
        for outcome in self.settings.birth_outcomes:
            totalProbStunted = newBorns.probRiskAtBirth['Stunting'][outcome] * newBorns.continuedStuntingImpact
            restratifiedStuntingAtBirth[outcome] = restratify(totalProbStunted)
            #wasting
            restratifiedWastingAtBirth[outcome] = {}
            probWastedAtBirth = newBorns.probRiskAtBirth['Wasting']
            totalProbWasted = 0
            # distribute proportions for wasted categories
            for wastingCat in self.settings.wasted_list:
                probWastedThisCat = probWastedAtBirth[wastingCat][outcome] * newBorns.continuedWastingImpact[wastingCat]
                restratifiedWastingAtBirth[outcome][wastingCat] = probWastedThisCat
                totalProbWasted += probWastedThisCat
            # normality constraint on non-wasted proportions
            for nonWastedCat in self.settings.non_wasted_list:
                wasting_dist = restratify(totalProbWasted)
                restratifiedWastingAtBirth[outcome][nonWastedCat] = wasting_dist[nonWastedCat]
        # sum over birth outcome for full stratified stunting and wasting fractions, then apply to birth distribution
        stuntingFractions = {}
        wastingFractions = {}
        for wastingCat in self.settings.wasting_list:
            wastingFractions[wastingCat] = 0.
            for outcome in self.settings.birth_outcomes:
                wastingFractions[wastingCat] += restratifiedWastingAtBirth[outcome][wastingCat] * newBorns.birth_dist[outcome]
        for stuntingCat in self.settings.stunting_list:
            stuntingFractions[stuntingCat] = 0
            for outcome in self.settings.birth_outcomes:
                stuntingFractions[stuntingCat] += restratifiedStuntingAtBirth[outcome][stuntingCat] * newBorns.birth_dist[outcome]
        # (new children at risk + old children at risk) / all children
        probStunted = sum(stuntingFractions[cat] for cat in self.settings.stunted_list)
        probWasted = sum(wastingFractions[cat] for cat in self.settings.wasted_list)
        stunt_dist = restratify(probStunted)
        # normality constraint only on non-wasted cats
        wast_dist = {}
        for cat in self.settings.non_wasted_list:
            dist = restratify(probWasted)
            wast_dist[cat] = dist[cat]
        for cat in self.settings.wasted_list:
            wast_dist[cat] = wastingFractions[cat]
        newBorns.stunting_dist = stunt_dist
        newBorns.wasting_dist = wast_dist

    def _apply_pw_mort(self):
        for age_group in self.pw.age_groups:
            for i, cat in enumerate(self.settings.anaemia_list):
                thisPop = age_group.pop_size * age_group.anaemia_dist[cat]
                deaths = thisPop * age_group.mortality[i]
                self.pw_deaths[self.year] += deaths
        oldest = self.pw.age_groups[-1]
        self.pw_exit[self.year] += oldest.pop_size * oldest.ageingRate

    def _update_pw(self):
        """Use pregnancy rate to distribute pw into age groups.
        Distribute into age bands by age distribution, assumed constant over time."""
        numWRA = self.nonpw.proj['Total WRA'][self.year]
        PWpop = self.nonpw.pregnancyRate * numWRA * (1. - self.nonpw.fracPregnancyAverted)
        for age_group in self.pw.age_groups:
           age_group.pop_size = PWpop * age_group.age_dist

    def _update_wra_pop(self):
        """Uses projected figures to determine the population of WRA not pregnant in a given age band and year
        warning: pw pop must be updated first."""
        #assuming WRA and pw have same age bands
        age_groups = self.nonpw.age_groups
        for i, age_group in enumerate(age_groups):
            projectedWRApop = self.nonpw.proj[age_group.age][self.year]
            PWpop = self.pw.age_groups[i].pop_size
            nonpw = projectedWRApop - PWpop
            age_group.pop_size = nonpw

    def _update_women_dists(self):
        for pop in self.pops[1:]:
            for age_group in pop.age_groups:
                age_group.update_anaemia_dist()

    def _move_children(self):
        """
        Responsible for updating children since they have monthly time steps
        :return:
        """
        for month in range(12):
            self._apply_child_mort()
            self._apply_child_ageing()
            self._apply_births()
            # self.update_child_dists()

    def _distrib_pops(self):
        for pop in self.pops:
            for age_group in pop.age_groups:
                age_group.distrib_pop()

    def _applyPrevTimeTrends(self): # TODO: haven't done mortality yet
        for age_group in self.children.age_groups:
            # stunting
            probStunted = sum(age_group.stunting_dist[cat] for cat in self.settings.stunted_list)
            newProb = probStunted * age_group.trends['Stunting']
            age_group.stunting_dist = restratify(newProb)
            # wasting
            probWasted = sum(age_group.wasting_dist[cat] for cat in self.settings.wasted_list)
            newProb = probWasted * age_group.trends['Wasting']
            nonWastedProb = restratify(newProb)
            for nonWastedCat in self.settings.non_wasted_list:
                age_group.wasting_dist[nonWastedCat] = nonWastedProb[nonWastedCat]
            # anaemia
            probAnaemic = sum(age_group.anaemia_dist[cat] for cat in self.settings.anaemic_list)
            newProb = probAnaemic * age_group.trends['Anaemia']
            age_group.anaemia_dist['Anaemic'] = newProb
            age_group.anaemia_dist['Not anaemic'] = 1 - newProb
        for age_group in self.pw.age_groups + self.nonpw.age_groups:
            probAnaemic = sum(age_group.anaemia_dist[cat] for cat in self.settings.anaemic_list)
            newProb = probAnaemic * age_group.trends['Anaemia']
            age_group.anaemia_dist['Anaemic'] = newProb
            age_group.anaemia_dist['Not anaemic'] = 1-newProb

    def get_seq(self, outcome):
        try:
            return getattr(self, outcome)
        except AttributeError:
            raise Exception(" ::ERROR:: {} not an attribute of Model class ".format(outcome))

    def get_output(self, outcome, seq=False):
        # todo: could add in __dict__ call to list all attributes, then do partial string matching to find the correct one
        outlist = self.get_seq(outcome)
        if seq: # return entire list
            return outlist
        else:
            if 'prev' in outcome: # only want final entry
                return outlist[-1]
            else: # want total
                return sum(outlist)