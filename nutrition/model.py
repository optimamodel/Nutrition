from utils import restratify
from copy import deepcopy as dcp
from constants import Constants

class Model:
    def __init__(self, name, pops, prog_info, start_year, end_year, adjustCoverage=False, timeTrends=False, calibrate=True):
        self.name = name
        self.pops = dcp(pops)
        self.children, self.PW, self.nonPW = self.pops
        self.prog_info = dcp(prog_info)

        # get key items
        self.all_years = range(start_year, end_year)
        self.sim_years = self.all_years # TODO: find out if we want a 'calibration' year. Regardless, design optional.
        self.year = None

        # set requirements for programs -- initial coverages, years
        self.prog_info.set_init_covs(self.pops, self.all_years)
        self.prog_info.set_years(self.all_years)

        # set requirements for populations -- conditional probs
        self._set_pop_probs()
        self._preg_info()

        self.year = start_year

        self.constants = Constants(self.data)
        self.adjustCoverage = adjustCoverage
        self.timeTrends = timeTrends
        self.num_years = len(self.sim_years)

        self._set_trackers()

    def _set_trackers(self):
        """Dicts with (years, num) as (key,value) pairs. Each value is an annual value"""
        self.child_deaths = {year: 0 for year in self.all_years}
        self.pw_deaths = {year: 0 for year in self.all_years}
        self.child_exit = {year: 0 for year in self.all_years}
        self.pw_exit = {year: 0 for year in self.all_years}
        self.stunted = {year: 0 for year in self.all_years}
        self.child_thrive = {year: 0 for year in self.all_years}
        self.child_not_anaemic = {year: 0 for year in self.all_years}
        self.neo_deaths = {year: 0 for year in self.all_years}
        self.births = {year: 0 for year in self.all_years}
        self.child_healthy = {year: 0 for year in self.all_years}

    def _set_pop_probs(self): # TODO: only want this to update if previous year is different from current
        init_cov = self.prog_info.get_ann_covs(self.year) # TODO: check this year is correct
        for pop in self.pops:
            pop.previousCov = init_cov
            pop.set_probs()

    def _reset_storage(self):
        for pop in self.pops:
            for age_group in pop.age_groups:
                age_group.set_update_storage()

    def update_year(self, year):
        self.year = year
        self.ProgramInfo.update_prog_year(year)

    def run_sim(self, covs):
        self.prog_info.update_prog_covs(covs)
        # TODO: figure out the starting point for the years
        # TODO: include pop size update
        for year in self.all_years: # TODO: recall cond. probs must be 1 year behind current year to get impact
            self.update_year(year)
            # determine if there are cov changes from previous year
            change = self.prog_info.determine_cov_change()
            if change:
                self._apply_prog_covs()
                self._set_pop_probs()
                self._reset_storage()
            # distribute pops according to new distributions and move model
            self._distrib_pops()
            self.integrate()

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
        # TODO: could move these to an 'update populations' function, which can be called even if the others are not called.
        for month in range(12):
            self.move_children()
        self._apply_pw_mort()
        self._update_pw()
        self._update_wra_pop()
        self.update_women_dists()

    def _preg_info(self):
        FP = [prog for prog in self.prog_info.programs if prog.name == 'Family Planning']
        if FP:
            FPprog = FP[0]
            self.nonPW._setBPInfo(FPprog.unrestrictedBaselineCov)
        else:
            self.nonPW._setBPInfo(0) # TODO: not best way to handle missing program

    def _famplan_update(self, pop):
        """ This update is not age-specified but instead applies to all non-PW.
        Also uses programs which are not explicitly treated elsewhere in model"""
        progList = self._applicable_progs('Family planning') # returns 'Family Planning' program
        if progList:
            prog = progList[0]
            pop._updateFracPregnancyAverted(prog.annualCoverage[self.year])

    def _update_pop_mort(self, pop):
        if pop.name != 'Non-pregnant women':
            pop._update_mort()

    def _applicable_progs(self, risk):
        applicableProgNames = self.ProgramInfo.programAreas[risk]
        programs = list(filter(lambda x: x.name in applicableProgNames, self.ProgramInfo.programs))
        return programs

    def _applicable_ages(self, population, risk):
        applicableAgeNames = population.populationAreas[risk]
        age_groups = list(filter(lambda x: x.age in applicableAgeNames, population.age_groups))
        return age_groups

    def _update_pop(self, population):
        for risk in self.ProgramInfo.programAreas.keys():
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
                for wastingCat in self.constants.wastedList:
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
                for cause in self.constants.causesOfDeath:
                    age_group.referenceMortality[cause] *= age_group.mortalityUpdate[cause]
                # stunting
                oldProbStunting = age_group.getFracRisk('Stunting')
                newProbStunting = oldProbStunting * age_group.totalStuntingUpdate
                age_group.stuntingDist = restratify(newProbStunting)
                # anaemia
                oldProbAnaemia = age_group.getFracRisk('Anaemia')
                newProbAnaemia = oldProbAnaemia * age_group.totalAnaemiaUpdate
                age_group.anaemiaDist['anaemic'] = newProbAnaemia
                age_group.anaemiaDist['not anaemic'] = 1.-newProbAnaemia
                # wasting
                newProbWasted = 0.
                for wastingCat in ['SAM', 'MAM']:
                    oldProbThisCat = age_group.getWastedFrac(wastingCat)
                    newProbThisCat = oldProbThisCat * age_group.totalWastingUpdate[wastingCat]
                    age_group.wastingDist[wastingCat] = newProbThisCat
                    newProbWasted += newProbThisCat
                # normality constraint on non-wasted proportions only
                nonWastedDist = restratify(newProbWasted)
                for nonWastedCat in self.constants.nonWastedList:
                    age_group.wastingDist[nonWastedCat] = nonWastedDist[nonWastedCat]
                age_group.distrib_pop()
        elif population.name == 'Pregnant women':
            # update PW anaemia but also birth distribution for <1 month age group
            # update birth distribution
            newBorns = self.children.age_groups[0]
            #PWpopSize = population.getTotalPopulation()
            # weighted sum accounts for different effects and target pops across PW age groups.
            firstPW = self.PW.age_groups[0]
            for BO in self.constants.birthOutcomes:
                newBorns.birthDist[BO] *= firstPW.birthUpdate[BO]
            newBorns.birthDist['Term AGA'] = 1. - sum(newBorns.birthDist[BO] for BO in list(set(self.constants.birthOutcomes) - {'Term AGA'}))
            # update anaemia distribution
            for age_group in population.age_groups:
                # mortality
                for cause in self.constants.causesOfDeath:
                    age_group.referenceMortality[cause] *= age_group.mortalityUpdate[cause]
                oldProbAnaemia = age_group.getFracRisk('Anaemia')
                newProbAnaemia = oldProbAnaemia * age_group.totalAnaemiaUpdate
                age_group.anaemiaDist['anaemic'] = newProbAnaemia
                age_group.anaemiaDist['not anaemic'] = 1.-newProbAnaemia
                age_group.distrib_pop()
        elif population.name == 'Non-pregnant women':
            for age_group in population.age_groups:
                # anaemia
                oldProbAnaemia = age_group.getFracRisk('Anaemia')
                newProbAnaemia = oldProbAnaemia * age_group.totalAnaemiaUpdate
                age_group.anaemiaDist['anaemic'] = newProbAnaemia
                age_group.anaemiaDist['not anaemic'] = 1.-newProbAnaemia
                age_group.distrib_pop()
            # weighted sum account for different effect and target pops across nonPW age groups # TODO: is this true or need to scale by frac targeted?
            # nonPWpop = population.getTotalPopulation()
            # FPcov = sum(nonPWage.FPupdate * nonPWage.getAgeGroupPopulation() for nonPWage in population.age_groups) / nonPWpop
            # population._updateFracPregnancyAverted(FPcov)

    def _wasting_trans(self, age_group):
        """Calculates the transitions between MAM and SAM categories"""
        age_group.fromSAMtoMAMupdate = {}
        age_group.fromMAMtoSAMupdate = {}
        age_group.fromSAMtoMAMupdate['MAM'] = (1. + (1.-age_group.wastingTreatmentUpdate['SAM']) * self.constants.demo['fraction SAM to MAM'])
        age_group.fromSAMtoMAMupdate['SAM'] = 1.
        age_group.fromMAMtoSAMupdate['SAM'] = (1. - (1.-age_group.wastingTreatmentUpdate['MAM']) * self.constants.demo['fraction MAM to SAM'])
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
        for wastingCat in self.constants.wastedList:
            age_group.diarrhoeaUpdate[wastingCat] *= wastingUpdate[wastingCat]

    def _bf_effects(self, age_group):
        oldProb = age_group.bfDist[age_group.correctBF]
        percentIncrease = (age_group.bfPracticeUpdate - oldProb)/oldProb
        if percentIncrease > 0.0001:
            age_group.bfDist[ageGroup.correctBF] = ageGroup.bfPracticeUpdate
        # get number at risk before
        sumBefore = ageGroup._getDiarrhoeaRiskSum()
        # update distribution of incorrect practices
        popSize = ageGroup.getAgeGroupPopulation()
        numCorrectBefore = ageGroup.getNumberCorrectlyBF()
        numCorrectAfter = popSize * ageGroup.bfDist[ageGroup.correctBF]
        numShifting = numCorrectAfter - numCorrectBefore
        numIncorrectBefore = popSize - numCorrectBefore
        fracCorrecting = numShifting / numIncorrectBefore if numIncorrectBefore > 0.01 else 0.
        for practice in ageGroup.incorrectBF:
            ageGroup.bfDist[practice] *= 1. - fracCorrecting
        ageGroup.distrib_pop()
        # number at risk after
        sumAfter = ageGroup._getDiarrhoeaRiskSum()
        # update diarrhoea incidence baseline, even though not directly used in this calculation
        ageGroup.incidences['Diarrhoea'] *= sumAfter / sumBefore
        beta = ageGroup._getFracDiarrhoeaFixedZ()  # TODO: this could probably be calculated prior to update coverages
        for risk in ['Stunting', 'Anaemia']:
            ageGroup.bfUpdate[risk] = self._frac_dia_update(beta, ageGroup, risk)
        ageGroup.bfUpdate.update(self._wasting_update_dia(beta, ageGroup))

    def _frac_dia_update(self, beta, ageGroup, risk): # TODO: this is static
        oldProb = ageGroup.getRiskFromDist(risk)
        newProb = 0.
        probThisRisk = ageGroup.probConditionalDiarrhoea[risk]
        for bfCat in ageGroup.const.bfList:
            pab = ageGroup.bfDist[bfCat]
            t1 = beta[bfCat] * probThisRisk['diarrhoea']
            t2 = (1.-beta[bfCat]) * probThisRisk['no diarrhoea']
            newProb += pab * (t1 + t2)
        reduction = (oldProb - newProb) / oldProb
        update = 1. - reduction
        return update

    def _wasting_update_dia(self, beta, ageGroup):
        update = {}
        for wastingCat in self.constants.wastedList:
            update[wastingCat] = 1.
            probWasted = ageGroup.probConditionalDiarrhoea[wastingCat]
            oldProb = ageGroup.wastingDist[wastingCat]
            newProb = 0.
            for bfCat in self.constants.bfList:
                pab = ageGroup.bfDist[bfCat]
                t1 = beta[bfCat] * probWasted['diarrhoea']
                t2 = (1.-beta[bfCat]) * probWasted['no diarrhoea']
                newProb += pab*(t1+t2)
            reduction = (oldProb - newProb)/oldProb
            update[wastingCat] *= 1. - reduction
        return update

    def _apply_child_mort(self):
        age_groups = self.children.age_groups
        for ageGroup in age_groups:
            for stuntingCat in self.constants.stuntingList:
                for wastingCat in self.constants.wastingList:
                    for bfCat in self.constants.bfList:
                        for anaemiaCat in self.constants.anaemiaList:
                            thisBox = ageGroup.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat]
                            deaths = thisBox.populationSize * thisBox.mortalityRate * self.constants.timestep # monthly deaths
                            thisBox.populationSize -= deaths
                            thisBox.cumulativeDeaths += deaths
                            self.child_deaths[self.year] += deaths

    def _apply_child_ageing(self):
        # TODO: longer term, I think this should be re-written
        # get number ageing out of each age group
        age_groups = self.children.age_groups
        ageingOut = [None] * len(age_groups)
        for i, ageGroup in enumerate(age_groups):
            ageingOut[i] = {}
            for stuntingCat in self.constants.stuntingList:
                ageingOut[i][stuntingCat] = {}
                for wastingCat in self.constants.wastingList:
                    ageingOut[i][stuntingCat][wastingCat] = {}
                    for bfCat in self.constants.bfList:
                        ageingOut[i][stuntingCat][wastingCat][bfCat] = {}
                        for anaemiaCat in self.constants.anaemiaList:
                            thisBox = ageGroup.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat]
                            ageingOut[i][stuntingCat][wastingCat][bfCat][anaemiaCat] = thisBox.populationSize * ageGroup.ageingRate
        self._track_outcomes()
        # first age group does not have ageing in
        newborns = age_groups[0]
        for stuntingCat in self.constants.stuntingList:
            for wastingCat in self.constants.wastingList:
                for bfCat in self.constants.bfList:
                    for anaemiaCat in self.constants.anaemiaList:
                        newbornBox = newborns.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat]
                        newbornBox.populationSize -= ageingOut[0][stuntingCat][wastingCat][bfCat][anaemiaCat]

        # for older age groups, account for previous stunting (binary)
        for i, ageGroup in enumerate(age_groups[1:], 1):
            numAgeingIn = {}
            numAgeingIn['stunted'] = 0.
            numAgeingIn['not stunted'] = 0.
            for prevBF in self.constants.bfList:
                for prevWT in self.constants.wastingList:
                    for prevAN in self.constants.anaemiaList:
                        numAgeingIn['stunted'] += sum(ageingOut[i-1][stuntingCat][prevWT][prevBF][prevAN] for stuntingCat in ['high', 'moderate'])
                        numAgeingIn['not stunted'] += sum(ageingOut[i-1][stuntingCat][prevWT][prevBF][prevAN] for stuntingCat in ['mild', 'normal'])
            # those ageing in moving into the 4 categories
            numAgeingInStratified = {}
            for stuntingCat in self.constants.stuntingList:
                numAgeingInStratified[stuntingCat] = 0.
            for prevStunt in ['stunted', 'not stunted']:
                totalProbStunted = ageGroup.probConditionalStunting[prevStunt] * ageGroup.continuedStuntingImpact
                restratifiedProb = restratify(totalProbStunted)
                for stuntingCat in self.constants.stuntingList:
                    numAgeingInStratified[stuntingCat] += restratifiedProb[stuntingCat] * numAgeingIn[prevStunt]
            # distribute those ageing in amongst those stunting categories but also BF, wasting and anaemia
            for wastingCat in self.constants.wastingList:
                pw = ageGroup.wastingDist[wastingCat]
                for bfCat in self.constants.bfList:
                    pbf = ageGroup.bfDist[bfCat]
                    for anaemiaCat in self.constants.anaemiaList:
                        pa = ageGroup.anaemiaDist[anaemiaCat]
                        for stuntingCat in self.constants.stuntingList:
                            thisBox = ageGroup.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat]
                            thisBox.populationSize -= ageingOut[i][stuntingCat][wastingCat][bfCat][anaemiaCat]
                            thisBox.populationSize += numAgeingInStratified[stuntingCat] * pw * pbf * pa
            # gaussianise
            distributionNow = ageGroup.getStuntingDistribution()
            probStunting = sum(distributionNow[stuntingCat] for stuntingCat in self.constants.stuntedList)
            ageGroup.stuntingDist = restratify(probStunting)
            ageGroup.distrib_pop()

    def _track_outcomes(self):
        oldest = self.children.age_groups[-1]
        self.child_exit[self.year] += oldest.getAgeGroupPopulation() * oldest.ageingRate
        self.stunted[self.year] += oldest.getAgeGroupNumberStunted() * oldest.ageingRate
        self.child_thrive[self.year] += oldest.getAgeGroupNumberNotStunted() * oldest.ageingRate
        self.child_not_anaemic[self.year] += oldest.getAgeGroupNumberchild_not_anaemic() * oldest.ageingRate
        self.child_healthy[self.year] += oldest.getAgeGroupNumberchild_healthy() * oldest.ageingRate

    def _apply_births(self): # TODO; re-write this function in future
        # num annual births = birth rate x num WRA x (1 - frac preg averted)
        numWRA = sum(self.constants.popProjections[age][self.year] for age in self.constants.WRAages)
        births = self.nonPW.birthRate * numWRA * (1. - self.nonPW.fracPregnancyAverted)
        # calculate total number of new babies and add to cumulative births
        numNewBabies = births * self.constants.timestep
        self.births[self.year] += numNewBabies
        # restratify stunting and wasting
        newBorns = self.children.age_groups[0]
        restratifiedStuntingAtBirth = {}
        restratifiedWastingAtBirth = {}
        for outcome in self.constants.birthOutcomes:
            totalProbStunted = newBorns.probRiskAtBirth['Stunting'][outcome] * newBorns.continuedStuntingImpact
            restratifiedStuntingAtBirth[outcome] = restratify(totalProbStunted)
            #wasting
            restratifiedWastingAtBirth[outcome] = {}
            probWastedAtBirth = newBorns.probRiskAtBirth['Wasting']
            totalProbWasted = 0
            # distribute proportions for wasted categories
            for wastingCat in self.constants.wastedList:
                probWastedThisCat = probWastedAtBirth[wastingCat][outcome] * newBorns.continuedWastingImpact[wastingCat]
                restratifiedWastingAtBirth[outcome][wastingCat] = probWastedThisCat
                totalProbWasted += probWastedThisCat
            # normality constraint on non-wasted proportions
            for nonWastedCat in self.constants.nonWastedList:
                wastingDist = restratify(totalProbWasted)
                restratifiedWastingAtBirth[outcome][nonWastedCat] = wastingDist[nonWastedCat]
        # sum over birth outcome for full stratified stunting and wasting fractions, then apply to birth distribution
        stuntingFractions = {}
        wastingFractions = {}
        for wastingCat in self.constants.wastingList:
            wastingFractions[wastingCat] = 0.
            for outcome in self.constants.birthOutcomes:
                wastingFractions[wastingCat] += restratifiedWastingAtBirth[outcome][wastingCat] * newBorns.birthDist[outcome]
        for stuntingCat in self.constants.stuntingList:
            stuntingFractions[stuntingCat] = 0
            for outcome in self.constants.birthOutcomes:
                stuntingFractions[stuntingCat] += restratifiedStuntingAtBirth[outcome][stuntingCat] * newBorns.birthDist[outcome]
        for stuntingCat in self.constants.stuntingList:
            for wastingCat in self.constants.wastingList:
                for bfCat in self.constants.bfList:
                    pbf = newBorns.bfDist[bfCat]
                    for anaemiaCat in self.constants.anaemiaList:
                        pa = newBorns.anaemiaDist[anaemiaCat]
                        newBorns.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize += numNewBabies * \
                                                                                                     pbf * pa * \
                                                                                                     stuntingFractions[stuntingCat] * \
                                                                                                     wastingFractions[wastingCat]

    def _apply_pw_mort(self):
        for ageGroup in self.PW.age_groups:
            for anaemiaCat in self.constants.anaemiaList:
                thisBox = ageGroup.boxes[anaemiaCat]
                deaths = thisBox.populationSize * thisBox.mortalityRate
                thisBox.cumulativeDeaths += deaths
                self.pw_deaths[self.year] += deaths
        oldest = self.PW.age_groups[-1]
        self.pw_exit[self.year] += oldest.getAgeGroupPopulation() * oldest.ageingRate

    def _update_pw(self):
        """Use pregnancy rate to distribute PW into age groups.
        Distribute into age bands by age distribution, assumed constant over time."""
        numWRA = sum(self.constants.popProjections[age][self.year] for age in self.constants.WRAages)
        PWpop = self.nonPW.pregnancyRate * numWRA * (1. - self.nonPW.fracPregnancyAverted)
        for ageGroup in self.PW.age_groups:
            popSize = PWpop * self.constants.PWageDistribution[ageGroup.age] # TODO: could put this in PW age groups for easy access
            for anaemiaCat in self.constants.anaemiaList:
                thisBox = ageGroup.boxes[anaemiaCat]
                thisBox.populationSize = popSize * ageGroup.anaemiaDist[anaemiaCat]

    def _update_wra_pop(self):
        """Uses projected figures to determine the population of WRA not pregnant in a given age band and year
        warning: PW pop must be updated first."""
        #assuming WRA and PW have same age bands
        age_groups = self.nonPW.age_groups
        for idx in range(len(age_groups)):
            ageGroup = age_groups[idx]
            projectedWRApop = self.constants.popProjections[ageGroup.age][self.year]
            PWpop = self.PW.age_groups[idx].getAgeGroupPopulation()
            nonPW = projectedWRApop - PWpop
            #distribute over risk factors
            for anaemiaCat in self.constants.anaemiaList:
                thisBox = ageGroup.boxes[anaemiaCat]
                thisBox.populationSize = nonPW * ageGroup.anaemiaDist[anaemiaCat]

    def update_child_dists(self):
        for ageGroup in self.children.age_groups:
            ageGroup.updateStuntingDist()
            ageGroup.updateWastingDist()
            ageGroup.updateBFDist()
            ageGroup.updateAnaemiaDist()

    def update_women_dists(self):
        for pop in self.pops[1:]:
            for ageGroup in pop.age_groups:
                ageGroup.updateAnaemiaDist()

    def move_children(self):
        """
        Responsible for updating children since they have monthly time steps
        :return:
        """
        self._apply_child_mort()
        self._apply_child_ageing()
        self._apply_births()
        self.update_child_dists()

    def _distrib_pops(self):
        for pop in self.pops:
            for ageGroup in pop.age_groups:
                ageGroup.distrib_pop()

    def _applyPrevTimeTrends(self): # TODO: haven't done mortality yet
        for ageGroup in self.children.age_groups:
            # stunting
            probStunted = sum(ageGroup.stuntingDist[cat] for cat in self.constants.stuntedList)
            newProb = probStunted * ageGroup.annualPrevChange['Stunting']
            ageGroup.stuntingDist = restratify(newProb)
            # wasting
            probWasted = sum(ageGroup.wastingDist[cat] for cat in self.constants.wastedList)
            newProb = probWasted * ageGroup.annualPrevChange['Wasting']
            nonWastedProb = restratify(newProb)
            for nonWastedCat in self.constants.nonWastedList:
                ageGroup.wastingDist[nonWastedCat] = nonWastedProb[nonWastedCat]
            # anaemia
            probAnaemic = sum(ageGroup.anaemiaDist[cat] for cat in self.constants.anaemicList)
            newProb = probAnaemic * ageGroup.annualPrevChange['Anaemia']
            ageGroup.anaemiaDist['anaemic'] = newProb
            ageGroup.anaemiaDist['not anaemic'] = 1 - newProb
        for ageGroup in self.PW.age_groups + self.nonPW.age_groups:
            probAnaemic = sum(ageGroup.anaemiaDist[cat] for cat in self.constants.anaemicList)
            newProb = probAnaemic * ageGroup.annualPrevChange['Anaemia']
            ageGroup.anaemiaDist['anaemic'] = newProb
            ageGroup.anaemiaDist['not anaemic'] = 1-newProb

    def _get_parset(self):
        """ Returns the full parameter set used by the model
        Mortality rates
        prevalences
        frac poor, in food groups, attendance
        program coverages, unit costs"""
        # TODO: what data type to return? Would like a reference so users can modify parsets in this form and will alter in model.
        pass


    # def calibrate(self):
    #     self.ProgramInfo.set_init_covs(self.pops)
    #     self._BPInfo()
    #     for year in self.constants.calibrationYears:
    #         self.update_year(year)
    #         self._updateEverything()
    #         self._progressModel()


    def getOutcome(self, outcome):
        if outcome == 'total_stunted':
            return sum(self.stunted.values())
        elif outcome == 'neg_child_healthy_children_rate':
            return -sum(self.child_healthy.values()) / sum(self.child_exit.values())
        elif outcome == 'neg_child_healthy_children':
            return -sum(self.child_healthy.values())
        elif outcome == 'child_healthy_children':
            return sum(self.child_healthy.values())
        elif outcome == 'stunting_prev':
            return self.children.getTotalFracStunted()
        elif outcome == 'thrive':
            return sum(self.child_thrive.values())
        elif outcome == 'neg_thrive':
            return -sum(self.child_thrive.values())
        elif outcome == 'deaths_children':
            return sum(self.child_deaths.values())
        elif outcome == 'deaths_PW':
            return sum(self.pw_deaths.values())
        elif outcome == 'total_deaths':
            return sum(self.pw_deaths.values() + self.child_deaths.values())
        elif outcome == 'mortality_rate':
            return (self.child_deaths[self.year] + self.pw_deaths[self.year])/(self.child_exit[self.year] + self.pw_exit[self.year])
        elif outcome == 'mortality_rate_children':
            return self.child_deaths[self.year] / self.child_exit[self.year]
        elif outcome == 'mortality_rate_PW':
            return self.pw_deaths[self.year] / self.pw_exit[self.year]
        elif outcome == 'neonatal_deaths':
            neonates = self.children.age_groups[0]
            return neonates.getCumulativeDeaths()
        elif outcome == 'anaemia_prev_PW':
            return self.PW.getTotalFracAnaemic()
        elif outcome == 'anaemia_prev_WRA':
            return self.nonPW.getTotalFracAnaemic()
        elif outcome == 'anaemia_prev_children':
            return self.children.getTotalFracAnaemic()
        elif outcome == 'total_anaemia_prev':
            totalPop = 0
            totalAnaemic = 0
            for pop in self.pops:
                totalPop += pop.getTotalPopulation()
                totalAnaemic += pop.getTotalNumberAnaemic()
            return totalAnaemic / totalPop
        elif outcome == 'wasting_prev':
            return self.children.getTotalFracWasted()
        elif outcome == 'SAM_prev':
            return self.children.getFracWastingCat('SAM')
        elif outcome == 'MAM_prev':
            return self.children.getFracWastingCat('MAM')
        else:
            raise Exception('::: ERROR: outcome string not found ' + str(outcome) + ' :::')