from utils import restratify
from . import settings
import sciris.core as sc
from .utils import default_trackers
import numpy as np

class Model:
    def __init__(self, pops, prog_info, t=None, adjust_cov=False, timeTrends=False):
        self.pops = sc.dcp(pops)
        self.children, self.pw, self.nonpw = self.pops
        self.prog_info = sc.dcp(prog_info)
        self.ss = settings.Settings()

        self.monthly_births = None
        self.t = t if t else self.ss.t
        self.all_years = np.arange(0, self.t[1]-self.t[0]+1)
        self.n_years = len(self.all_years)
        self.sim_years = self.all_years[1:]
        self.year = self.all_years[0]

        # this is for extracting baseline coverage/spending in gui (before prog_set set)
        self._set_progs(self.prog_info.base_progset())

        self.adjust_cov = adjust_cov
        self.timeTrends = timeTrends

    def setup(self, scen, setcovs=True):
        """ Sets scenario-specific parameters within the model.
        - simulation period
        - programs for scenario
        - population conditional probabilities
        - storage for updates
        - coverage scenario for programs
         """
        self._set_progs(scen.prog_set) # overwrite baseline prog_set
        self._set_pop_probs(self.year)
        self._reset_storage()
        self._set_trackers()
        self._track_prevs()
        if setcovs:
            # scenario coverages
            self.update_covs(scen.vals, scen.scen_type)

    def get_allocs(self, add_funds, fix_curr, rem_curr):
        self.prog_info.get_allocs(add_funds, fix_curr, rem_curr)

    def _set_progs(self, prog_set):
        self.prog_info.make_progs(prog_set, self.all_years)
        self.prog_info.set_init_covs(self.pops)
        self.prog_info.set_costcovs() # enables getting coverage from cost
        self.prog_info.get_base_spend()
    
    def update_covs(self, covs, scentype):
        covs, spend = self.prog_info.get_cov_scen(covs, scentype, self.all_years)
        self.prog_info.update_covs(covs, spend)

    def _set_trackers(self):
        """ Arrays to store annual outputs """
        for tracker in default_trackers():
            arr = np.zeros(self.n_years)
            setattr(self, tracker, arr)

    def _track_outcomes(self):
        oldest = self.children.age_groups[-1]
        self.thrive[self.year] += oldest.num_notstunted() * oldest.ageingRate

    def _track_prevs(self):
        """ Tracks the prevalences of conditions over time.
         Begins at baseline year so that all scenario prevalences begin at the same point """

        self.stunting_prev[self.year] = self.children.frac_stunted()
        self.wasting_prev[self.year] = self.children.frac_risk('wast')
        self.child_anaemprev[self.year] = self.children.frac_risk('an')
        self.pw_anaemprev[self.year] = self.pw.frac_risk('an')
        self.nonpw_anaemprev[self.year] = self.nonpw.frac_risk('an')

    def _set_pop_probs(self, year):
        init_cov = self.prog_info.get_ann_covs(year-1)
        prog_areas = self.prog_info.prog_areas
        for pop in self.pops:
            pop.previousCov = init_cov
            pop.set_probs(prog_areas)

    def _reset_storage(self):
        for pop in self.pops:
            for age_group in pop.age_groups:
                age_group.reset_storage()

    def update_year(self, year):
        self.year = year
        self.prog_info.update_prog_year(year)

    def run_sim(self):
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
            # combine direct and indirect updates to each risk area that we model
            self._combine_updates(pop)
            self._update_dists(pop)
            self._update_pop_mort(pop)

    def integrate(self):
        self._move_children()
        self._apply_pw_mort()
        self._update_pw()
        self._update_wra_pop()

    def _update_pop_mort(self, pop):
        if pop.name != 'Non-pregnant women':
            pop.update_mortality()

    def _applicable_progs(self, risk):
        applicableProgNames = self.prog_info.prog_areas[risk]
        programs = self.prog_info.programs[applicableProgNames]
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
                        elif risk == 'Birth number':
                            program.get_pregav_update(age_group)
                        elif risk == 'Birth spacing':
                            program.get_birthspace_update(age_group)
                        else:
                            print('Warning: Risk "%s" not found. No update applied '%risk)
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
                for wastingCat in self.ss.wasted_list:
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
                oldProbStunting = age_group.frac_stunted()
                newProbStunting = oldProbStunting * age_group.totalStuntingUpdate
                age_group.update_dist('stunt', newProbStunting)
                # anaemia
                oldProbAnaemia = age_group.frac_anaemic()
                newProbAnaemia = oldProbAnaemia * age_group.totalAnaemiaUpdate
                age_group.update_dist('anaem', newProbAnaemia)
                # wasting
                wast_dist = sc.odict()
                newProbWasted = 0.
                for wastingCat in self.ss.wasted_list:
                    oldProbThisCat = age_group.frac_wasted(wastingCat)
                    newProbThisCat = oldProbThisCat * age_group.totalWastingUpdate[wastingCat]
                    wast_dist[wastingCat] = newProbThisCat
                    newProbWasted += newProbThisCat
                # normality constraint on non-wasted proportions only
                age_group.update_dist('wast', newProbWasted, wast_dist)
        elif population.name == 'Pregnant women':
            # update pw anaemia but also birth distribution for <1 month age group
            # update birth distribution
            newBorns = self.children.age_groups[0]
            # weighted sum accounts for different effects and target pops across pw age groups.
            firstPW = self.pw.age_groups[0]
            for BO in self.ss.birth_outcomes:
                newBorns.birth_dist[BO] *= firstPW.birthUpdate[BO]
            newBorns.birth_dist['Term AGA'] = 1. - sum(newBorns.birth_dist[BO] for BO in self.ss.birth_outcomes[1:])
            # update anaemia distribution
            for age_group in population.age_groups:
                # mortality
                for cause in age_group.causes_death:
                    age_group.referenceMortality[cause] *= age_group.mortalityUpdate[cause]
                oldProbAnaemia = age_group.frac_anaemic()
                newProbAnaemia = oldProbAnaemia * age_group.totalAnaemiaUpdate
                age_group.update_dist('anaem', newProbAnaemia)
        elif population.name == 'Non-pregnant women':
            # get birth outcome update from birth spacing
            self._birthspace_effects()
            # update dists for nonPW
            for age_group in population.age_groups:
                # anaemia
                oldProbAnaemia = age_group.frac_anaemic()
                newProbAnaemia = oldProbAnaemia * age_group.totalAnaemiaUpdate
                age_group.update_dist('anaem', newProbAnaemia)

    def _wasting_trans(self, age_group):
        """Calculates the transitions between MAM and SAM categories
        Currently only accounting for the movement from sam to mam, because the other direction is complicated """
        numsam = age_group.num_risk('SAM')
        nummam = age_group.num_risk('MAM')
        age_group.fromSAMtoMAMupdate['MAM'] = 1 + (1. - age_group.wastingTreatmentUpdate['SAM']) * numsam / nummam

    def _dia_indirect_effects(self, age_group):
        # get flow-on effects to stunting, anaemia and wasting
        Z0 = age_group._getZa()
        age_group.incidences['Diarrhoea'] *= age_group.diarrhoeaIncidenceUpdate
        Zt = age_group._getZa() # updated incidence
        beta = age_group._getFracDiarrhoea(Z0, Zt)
        age_group._updateProbConditionalDiarrhoea(Zt)
        for risk in ['Stunting', 'Anaemia']: # todo: remove link between dia and anaemia?
            age_group.diarrhoeaUpdate[risk] *= self._frac_dia_update(beta, age_group, risk)
        wastingUpdate = self._wasting_update_dia(beta, age_group)
        for wastingCat in self.ss.wasted_list:
            age_group.diarrhoeaUpdate[wastingCat] *= wastingUpdate[wastingCat]

    def _bf_effects(self, age_group):
        # get number at risk before
        sumBefore = age_group._getDiarrhoeaRiskSum()
        # update distribution of incorrect practices
        popSize = age_group.pop_size
        numCorrectBefore = age_group.num_correctbf()
        numCorrectAfter = popSize * age_group.bfPracticeUpdate
        numShifting = numCorrectAfter - numCorrectBefore
        numIncorrectBefore = popSize - numCorrectBefore
        fracCorrecting = numShifting / numIncorrectBefore if numIncorrectBefore > 0.01 else 0.
        # update breastfeeding distribution
        for practice in age_group.incorrect_bf:
            age_group.bf_dist[practice] *= 1. - fracCorrecting
        age_group.bf_dist[age_group.correct_bf] = age_group.bfPracticeUpdate
        # number at risk after
        sumAfter = age_group._getDiarrhoeaRiskSum()
        # update diarrhoea incidence baseline, even though not directly used in this calculation
        age_group.incidences['Diarrhoea'] *= sumAfter / sumBefore
        beta = age_group._getFracDiarrhoeaFixedZ()  # TODO: this could probably be calculated prior to update coverages
        for risk in ['Stunting', 'Anaemia']:
            age_group.bfUpdate[risk] = self._frac_dia_update(beta, age_group, risk)
        age_group.bfUpdate.update(self._wasting_update_dia(beta, age_group))

    def _birthspace_effects(self):
        """ From the birth space update, take from both <18 months and 18-23 month categories evenly """
        # todo: I think there is an issue here b/c don't correctly account for the 'first birth' distribution. change later
        nonpw = self.nonpw.age_groups[0] # only impacted this pop
        newborns = self.children.age_groups[0]
        oldprob = nonpw.birth_space[self.ss.optimal_space]
        num_corrbefore = oldprob * newborns.pop_size
        num_corrafter = newborns.pop_size * nonpw.birthspace_update
        num_shift = num_corrafter - num_corrbefore
        num_wrongbefore = newborns.pop_size - num_corrbefore
        frac_correcting = num_shift / num_wrongbefore if num_wrongbefore > 0.01 else 0.
        # update birth spacing
        for space in nonpw.birth_space:
            nonpw.birth_space[space] *= 1 - frac_correcting
        nonpw.birth_space[self.ss.optimal_space] = nonpw.birthspace_update
        # update birth outcomes
        for bo in self.ss.birth_outcomes:
            newborns.birth_dist[bo] = sum(newborns.prob_bospace[bo][name] * value for name, value in nonpw.birth_space.iteritems())

    def _frac_dia_update(self, beta, age_group, risk):
        oldProb = age_group.frac_risk(risk)
        newProb = 0.
        probThisRisk = age_group.probConditionalDiarrhoea[risk]
        for bfCat in self.ss.bf_list:
            pab = age_group.bf_dist[bfCat]
            t1 = beta[bfCat] * probThisRisk['diarrhoea']
            t2 = (1.-beta[bfCat]) * probThisRisk['no diarrhoea']
            newProb += pab * (t1 + t2)
        reduction = (oldProb - newProb) / oldProb
        update = 1. - reduction
        return update

    def _wasting_update_dia(self, beta, age_group):
        update = {}
        for wastingCat in self.ss.wasted_list:
            update[wastingCat] = 1.
            probWasted = age_group.probConditionalDiarrhoea[wastingCat]
            oldProb = age_group.wasting_dist[wastingCat]
            newProb = 0.
            for bfCat in self.ss.bf_list:
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
            stunting = np.array([age_group.stunting_dist[k] for k in self.ss.stunting_list])
            wasting = np.array([age_group.wasting_dist[k] for k in self.ss.wasting_list])
            anaemia = np.array([age_group.anaemia_dist[k] for k in self.ss.anaemia_list])
            bf = np.array([age_group.bf_dist[k] for k in self.ss.bf_list])
            outer = np.einsum('i,j,k,l', stunting, wasting, anaemia, bf).flatten()
            deaths = sum(age_group.pop_size * outer[:] * age_group.mortality[:] * self.ss.timestep)
            age_group.pop_size -= deaths
            self.child_deaths[self.year] += deaths

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
            numAgeingIn['stunted'] = ageingOut[i-1] * prev_age.frac_stunted()
            numAgeingIn['not stunted'] = ageingOut[i-1] * (1.- prev_age.frac_stunted())
            # those ageing in moving into the 4 categories
            numAgeingInStratified = {}
            for stuntingCat in self.ss.stunting_list:
                numAgeingInStratified[stuntingCat] = 0.
            for prevStunt in ['stunted', 'not stunted']:
                totalProbStunted = age_group.probConditionalStunting[prevStunt] * age_group.continuedStuntingImpact
                restratifiedProb = restratify(totalProbStunted)
                numaged = numAgeingIn[prevStunt]
                for stuntingCat in self.ss.stunting_list:
                    numAgeingInStratified[stuntingCat] += restratifiedProb[stuntingCat] * numaged
            # update distribution in each age group
            # (number of new children stunted + number of old stunted) / (new + old children)
            popgrowth = sum(numAgeingIn.values())
            extra_stunted = sum(numAgeingInStratified[cat] for cat in self.ss.stunted_list)
            probStunting = (extra_stunted + age_group.num_stunted()) / (popgrowth + age_group.pop_size)
            # add children
            age_group.pop_size += popgrowth
            # new distribution
            age_group.update_dist('stunt', probStunting)

    def _apply_births(self):
        # restratify stunting and wasting
        newBorns = self.children.age_groups[0]
        # add births to population size
        newBorns.pop_size += self.monthly_births
        # get stunting and wasting distributions for each birth outcome.
        restratifiedStuntingAtBirth = {}
        restratifiedWastingAtBirth = {}
        for outcome in self.ss.birth_outcomes:
            totalProbStunted = newBorns.probRiskAtBirth['Stunting'][outcome] * newBorns.continuedStuntingImpact
            restratifiedStuntingAtBirth[outcome] = restratify(totalProbStunted)
            #wasting
            restratifiedWastingAtBirth[outcome] = {}
            probWastedAtBirth = newBorns.probRiskAtBirth['Wasting']
            totalProbWasted = 0
            # distribute proportions for wasted categories
            for wastingCat in self.ss.wasted_list:
                probWastedThisCat = probWastedAtBirth[wastingCat][outcome] * newBorns.continuedWastingImpact[wastingCat]
                restratifiedWastingAtBirth[outcome][wastingCat] = probWastedThisCat
                totalProbWasted += probWastedThisCat
            # normality constraint on non-wasted proportions
            for nonWastedCat in self.ss.non_wasted_list:
                wasting_dist = restratify(totalProbWasted)
                restratifiedWastingAtBirth[outcome][nonWastedCat] = wasting_dist[nonWastedCat]
        # sum over birth outcome for full stratified stunting and wasting fractions, then apply to birth distribution
        stuntingFractions = {}
        wastingFractions = {}
        for wastingCat in self.ss.wasting_list:
            wastingFractions[wastingCat] = 0.
            for outcome in self.ss.birth_outcomes:
                wastingFractions[wastingCat] += restratifiedWastingAtBirth[outcome][wastingCat] * newBorns.birth_dist[outcome]
        for stuntingCat in self.ss.stunting_list:
            stuntingFractions[stuntingCat] = 0
            for outcome in self.ss.birth_outcomes:
                stuntingFractions[stuntingCat] += restratifiedStuntingAtBirth[outcome][stuntingCat] * newBorns.birth_dist[outcome]
        # (new children at risk + old children at risk) / all children
        probStunted = sum(stuntingFractions[cat] for cat in self.ss.stunted_list)
        probWasted = sum(wastingFractions[cat] for cat in self.ss.wasted_list)
        newBorns.update_dist('stunt', probStunted)
        newBorns.update_dist('wast', probWasted, wastingFractions)

    def _apply_pw_mort(self):
        for age_group in self.pw.age_groups:
            for i, cat in enumerate(self.ss.anaemia_list):
                thisPop = age_group.pop_size * age_group.anaemia_dist[cat]
                deaths = thisPop * age_group.mortality[i]
                self.pw_deaths[self.year] += deaths

    def _update_pw(self):
        """Use pregnancy rate to distribute pw into age groups.
        Distribute into age bands by age distribution, assumed constant over time."""
        numpw = self.pw.proj['Estimated pregnant women'][self.year]
        adj_pw = numpw * (1. - self.nonpw.get_pregav())
        for age_group in self.pw.age_groups:
           age_group.pop_size = adj_pw * age_group.age_dist

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

    def _move_children(self):
        """
        Responsible for updating children since they have monthly time steps
        :return:
        """
        self.get_births()
        for month in range(12):
            self._apply_child_mort()
            self._apply_child_ageing()
            self._apply_births()

    def get_births(self):
        """ Set monthly number of births """
        numbirths = self.pw.proj['Number of births'][self.year]
        adj_births = numbirths * (1. - self.nonpw.get_pregav())
        self.monthly_births = adj_births * self.ss.timestep

    def _applyPrevTimeTrends(self): # TODO: haven't done mortality yet
        for age_group in self.children.age_groups:
            # stunting
            probStunted = sum(age_group.stunting_dist[cat] for cat in self.ss.stunted_list)
            newProb = probStunted * age_group.trends['Stunting']
            age_group.update_dist('stunt', newProb)
            # wasting
            probWasted = sum(age_group.wasting_dist[cat] for cat in self.ss.wasted_list)
            newProb = probWasted * age_group.trends['Wasting']
            nonWastedProb = restratify(newProb)
            for nonWastedCat in self.ss.non_wasted_list:
                age_group.wasting_dist[nonWastedCat] = nonWastedProb[nonWastedCat]
            # anaemia
            probAnaemic = sum(age_group.anaemia_dist[cat] for cat in self.ss.anaemic_list)
            newProb = probAnaemic * age_group.trends['Anaemia']
            age_group.update_dist('anaem', newProb)
        for age_group in self.pw.age_groups + self.nonpw.age_groups:
            probAnaemic = sum(age_group.anaemia_dist[cat] for cat in self.ss.anaemic_list)
            newProb = probAnaemic * age_group.trends['Anaemia']
            age_group.update_dist('anaem', newProb)

    def get_seq(self, outcome):
        try:
            return getattr(self, outcome)
        except AttributeError:
            raise Exception(" ::ERROR:: %s not an attribute of Model class " % outcome)

    def get_output(self, outcomes=None, seq=False):
        """ Always returns a list, but of variable length"""
        if outcomes is None: outcomes = default_trackers()
        if seq:
            outputs = np.zeros((len(outcomes), self.n_years))
            for i, out in enumerate(outcomes):
                outputs[i] = self.get_seq(out)
        else:
            outputs = np.zeros(len(outcomes))
            for i, out in enumerate(outcomes):
                outseq = self.get_seq(out)
                if 'prev' in out: # only want final entry
                    output = outseq[-1]
                else: # want total
                    output = sum(outseq)
                outputs[i] = output
        return outputs
