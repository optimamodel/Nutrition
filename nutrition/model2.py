import data
from copy import deepcopy as dcp
import populations
import program_info
from constants import Constants
from scipy.special import ndtri, ndtr # these are much faster than calling scipy.stats.norm

class Model:
    def __init__(self, pops, prog_info, start_year, end_year, adjustCoverage=False, timeTrends=False, calibrate=True):
        # simpars could include data, populations, progSets
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
            for ageGroup in pop.ageGroups:
                ageGroup.set_update_storage()

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
        ageGroups = list(filter(lambda x: x.age in applicableAgeNames, population.ageGroups))
        return ageGroups

    def _update_pop(self, population):
        for risk in self.ProgramInfo.programAreas.keys():
            # get relevant programs and age groups, determined by risk area
            applicableProgs = self._applicable_progs(risk)
            ageGroups = self._applicable_ages(population, risk)
            for ageGroup in ageGroups:
                for program in applicableProgs:
                    if ageGroup.age in program.agesImpacted:
                        if risk == 'Stunting':
                            program._stuntingUpdate(ageGroup)
                        elif risk == 'Anaemia':
                            program._anaemiaUpdate(ageGroup)
                        elif risk == 'Wasting prevention':
                            program._wastingPreventUpdate(ageGroup)
                        elif risk == 'Wasting treatment':
                            program._wastingTreatUpdate(ageGroup)
                        elif risk == 'Breastfeeding':
                            program._BFUpdate(ageGroup)
                        elif risk == 'Diarrhoea':
                            program._DiaIncidUpdate(ageGroup)
                        elif risk == 'Mortality':
                            program._getMortalityUpdate(ageGroup)
                        elif risk == 'Birth outcomes':
                            program._getBirthOutcomeUpdate(ageGroup)
                        # elif risk == 'Birth age': # TODO: change implementation from previous mode version -- Calculate probabilities using RR etc.
                        #     program._getBirthAgeUpdate(ageGroup)
                        else:
                            print ":: Risk _{}_ not found. No update applied ::".format(risk)
                            continue
                    else:
                        continue
                if risk == 'Breastfeeding':  # flow on effects to diarrhoea (does not diarrhoea incidence & is independent of below)
                    self._bf_effects(ageGroup)
                if risk == 'Diarrhoea': # flow-on effects from incidence
                    self._dia_indirect_effects(ageGroup)
                if risk == 'Wasting treatment':
                    # need to account for flow between MAM and SAM
                    self._wasting_trans(ageGroup)

    def _combine_updates(self, population):
        """
        Each risk area modelled can be impacted from direct and indirect pathways, so we combine these here
        :param population:
        :return:
        """
        if population.name == 'Children':
            for ageGroup in population.ageGroups:
                # stunting: direct, diarrhoea, breastfeeding
                ageGroup.totalStuntingUpdate = ageGroup.stuntingUpdate * ageGroup.diarrhoeaUpdate['Stunting'] \
                                               * ageGroup.bfUpdate['Stunting']
                ageGroup.continuedStuntingImpact *= ageGroup.totalStuntingUpdate
                # anaemia: direct, diarrhoea, breastfeeding
                ageGroup.totalAnaemiaUpdate = ageGroup.anaemiaUpdate * ageGroup.diarrhoeaUpdate['Anaemia'] \
                                              * ageGroup.bfUpdate['Anaemia']
                # wasting: direct (prevalence, incidence), flow between MAM & SAM, diarrhoea, breastfeeding
                ageGroup.totalWastingUpdate = {}
                for wastingCat in self.constants.wastedList:
                    ageGroup.totalWastingUpdate[wastingCat] = ageGroup.wastingTreatmentUpdate[wastingCat] \
                                                  * ageGroup.wastingPreventionUpdate[wastingCat] \
                                                  * ageGroup.bfUpdate[wastingCat] \
                                                  * ageGroup.diarrhoeaUpdate[wastingCat] \
                                                  * ageGroup.fromMAMtoSAMupdate[wastingCat] \
                                                  * ageGroup.fromSAMtoMAMupdate[wastingCat]
                    ageGroup.continuedWastingImpact[wastingCat] *= ageGroup.totalWastingUpdate[wastingCat]
        elif population.name == 'Pregnant women':
            for ageGroup in population.ageGroups:
                ageGroup.totalAnaemiaUpdate = ageGroup.anaemiaUpdate
        elif population.name == 'Non-pregnant women':
            for ageGroup in population.ageGroups:
                ageGroup.totalAnaemiaUpdate = ageGroup.anaemiaUpdate
                ageGroup.totalBAUpdate = ageGroup.birthAgeUpdate

    def _update_dists(self, population):
        """
        Uses assumption that each ageGroup in a population has a default update
        value which exists (not across populations though)
        :return:
        """
        if population.name == 'Children':
            for ageGroup in population.ageGroups:
                for cause in self.constants.causesOfDeath:
                    ageGroup.referenceMortality[cause] *= ageGroup.mortalityUpdate[cause]
                # stunting
                oldProbStunting = ageGroup.getFracRisk('Stunting')
                newProbStunting = oldProbStunting * ageGroup.totalStuntingUpdate
                ageGroup.stuntingDist = self.restratify(newProbStunting)
                # anaemia
                oldProbAnaemia = ageGroup.getFracRisk('Anaemia')
                newProbAnaemia = oldProbAnaemia * ageGroup.totalAnaemiaUpdate
                ageGroup.anaemiaDist['anaemic'] = newProbAnaemia
                ageGroup.anaemiaDist['not anaemic'] = 1.-newProbAnaemia
                # wasting
                newProbWasted = 0.
                for wastingCat in ['SAM', 'MAM']:
                    oldProbThisCat = ageGroup.getWastedFrac(wastingCat)
                    newProbThisCat = oldProbThisCat * ageGroup.totalWastingUpdate[wastingCat]
                    ageGroup.wastingDist[wastingCat] = newProbThisCat
                    newProbWasted += newProbThisCat
                # normality constraint on non-wasted proportions only
                nonWastedDist = self.restratify(newProbWasted)
                for nonWastedCat in self.constants.nonWastedList:
                    ageGroup.wastingDist[nonWastedCat] = nonWastedDist[nonWastedCat]
                ageGroup.distrib_pop()
        elif population.name == 'Pregnant women':
            # update PW anaemia but also birth distribution for <1 month age group
            # update birth distribution
            newBorns = self.children.ageGroups[0]
            #PWpopSize = population.getTotalPopulation()
            # weighted sum accounts for different effects and target pops across PW age groups.
            firstPW = self.PW.ageGroups[0]
            for BO in self.constants.birthOutcomes:
                newBorns.birthDist[BO] *= firstPW.birthUpdate[BO]
            newBorns.birthDist['Term AGA'] = 1. - sum(newBorns.birthDist[BO] for BO in list(set(self.constants.birthOutcomes) - {'Term AGA'}))
            # update anaemia distribution
            for ageGroup in population.ageGroups:
                # mortality
                for cause in self.constants.causesOfDeath:
                    ageGroup.referenceMortality[cause] *= ageGroup.mortalityUpdate[cause]
                oldProbAnaemia = ageGroup.getFracRisk('Anaemia')
                newProbAnaemia = oldProbAnaemia * ageGroup.totalAnaemiaUpdate
                ageGroup.anaemiaDist['anaemic'] = newProbAnaemia
                ageGroup.anaemiaDist['not anaemic'] = 1.-newProbAnaemia
                ageGroup.distrib_pop()
        elif population.name == 'Non-pregnant women':
            for ageGroup in population.ageGroups:
                # anaemia
                oldProbAnaemia = ageGroup.getFracRisk('Anaemia')
                newProbAnaemia = oldProbAnaemia * ageGroup.totalAnaemiaUpdate
                ageGroup.anaemiaDist['anaemic'] = newProbAnaemia
                ageGroup.anaemiaDist['not anaemic'] = 1.-newProbAnaemia
                ageGroup.distrib_pop()
            # weighted sum account for different effect and target pops across nonPW age groups # TODO: is this true or need to scale by frac targeted?
            # nonPWpop = population.getTotalPopulation()
            # FPcov = sum(nonPWage.FPupdate * nonPWage.getAgeGroupPopulation() for nonPWage in population.ageGroups) / nonPWpop
            # population._updateFracPregnancyAverted(FPcov)

    def _wasting_trans(self, ageGroup):
        """Calculates the transitions between MAM and SAM categories"""
        ageGroup.fromSAMtoMAMupdate = {}
        ageGroup.fromMAMtoSAMupdate = {}
        ageGroup.fromSAMtoMAMupdate['MAM'] = (1. + (1.-ageGroup.wastingTreatmentUpdate['SAM']) * self.constants.demographics['fraction SAM to MAM'])
        ageGroup.fromSAMtoMAMupdate['SAM'] = 1.
        ageGroup.fromMAMtoSAMupdate['SAM'] = (1. - (1.-ageGroup.wastingTreatmentUpdate['MAM']) * self.constants.demographics['fraction MAM to SAM'])
        ageGroup.fromMAMtoSAMupdate['MAM'] = 1.

    def _dia_indirect_effects(self, ageGroup):
        # get flow-on effects to stunting, anaemia and wasting
        Z0 = ageGroup._getZa()
        ageGroup.incidences['Diarrhoea'] *= ageGroup.diarrhoeaIncidenceUpdate
        Zt = ageGroup._getZa() # updated incidence
        beta = ageGroup._getFracDiarrhoea(Z0, Zt)
        ageGroup._updateProbConditionalDiarrhoea(Zt)
        for risk in ['Stunting', 'Anaemia']:
            ageGroup.diarrhoeaUpdate[risk] *= self._frac_dia_update(beta, ageGroup, risk)
        wastingUpdate = self._wasting_update_dia(beta, ageGroup)
        for wastingCat in self.constants.wastedList:
            ageGroup.diarrhoeaUpdate[wastingCat] *= wastingUpdate[wastingCat]

    def _bf_effects(self, ageGroup):
        oldProb = ageGroup.bfDist[ageGroup.correctBF]
        percentIncrease = (ageGroup.bfPracticeUpdate - oldProb)/oldProb
        if percentIncrease > 0.0001:
            ageGroup.bfDist[ageGroup.correctBF] = ageGroup.bfPracticeUpdate
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
        ageGroups = self.children.ageGroups
        for ageGroup in ageGroups:
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
        ageGroups = self.children.ageGroups
        ageingOut = [None] * len(ageGroups)
        for i, ageGroup in enumerate(ageGroups):
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
        newborns = ageGroups[0]
        for stuntingCat in self.constants.stuntingList:
            for wastingCat in self.constants.wastingList:
                for bfCat in self.constants.bfList:
                    for anaemiaCat in self.constants.anaemiaList:
                        newbornBox = newborns.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat]
                        newbornBox.populationSize -= ageingOut[0][stuntingCat][wastingCat][bfCat][anaemiaCat]

        # for older age groups, account for previous stunting (binary)
        for i, ageGroup in enumerate(ageGroups[1:], 1):
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
                restratifiedProb = self.restratify(totalProbStunted)
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
            ageGroup.stuntingDist = self.restratify(probStunting)
            ageGroup.distrib_pop()

    def _track_outcomes(self):
        oldest = self.children.ageGroups[-1]
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
        newBorns = self.children.ageGroups[0]
        restratifiedStuntingAtBirth = {}
        restratifiedWastingAtBirth = {}
        for outcome in self.constants.birthOutcomes:
            totalProbStunted = newBorns.probRiskAtBirth['Stunting'][outcome] * newBorns.continuedStuntingImpact
            restratifiedStuntingAtBirth[outcome] = self.restratify(totalProbStunted)
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
                wastingDist = self.restratify(totalProbWasted)
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
        for ageGroup in self.PW.ageGroups:
            for anaemiaCat in self.constants.anaemiaList:
                thisBox = ageGroup.boxes[anaemiaCat]
                deaths = thisBox.populationSize * thisBox.mortalityRate
                thisBox.cumulativeDeaths += deaths
                self.pw_deaths[self.year] += deaths
        oldest = self.PW.ageGroups[-1]
        self.pw_exit[self.year] += oldest.getAgeGroupPopulation() * oldest.ageingRate

    def _update_pw(self):
        """Use pregnancy rate to distribute PW into age groups.
        Distribute into age bands by age distribution, assumed constant over time."""
        numWRA = sum(self.constants.popProjections[age][self.year] for age in self.constants.WRAages)
        PWpop = self.nonPW.pregnancyRate * numWRA * (1. - self.nonPW.fracPregnancyAverted)
        for ageGroup in self.PW.ageGroups:
            popSize = PWpop * self.constants.PWageDistribution[ageGroup.age] # TODO: could put this in PW age groups for easy access
            for anaemiaCat in self.constants.anaemiaList:
                thisBox = ageGroup.boxes[anaemiaCat]
                thisBox.populationSize = popSize * ageGroup.anaemiaDist[anaemiaCat]

    def _update_wra_pop(self):
        """Uses projected figures to determine the population of WRA not pregnant in a given age band and year
        warning: PW pop must be updated first."""
        #assuming WRA and PW have same age bands
        ageGroups = self.nonPW.ageGroups
        for idx in range(len(ageGroups)):
            ageGroup = ageGroups[idx]
            projectedWRApop = self.constants.popProjections[ageGroup.age][self.year]
            PWpop = self.PW.ageGroups[idx].getAgeGroupPopulation()
            nonPW = projectedWRApop - PWpop
            #distribute over risk factors
            for anaemiaCat in self.constants.anaemiaList:
                thisBox = ageGroup.boxes[anaemiaCat]
                thisBox.populationSize = nonPW * ageGroup.anaemiaDist[anaemiaCat]

    def restratify(self, fractionYes): # TODO: currently have this and in 'Children'. Don't want two static methods
        # Going from binary stunting/wasting to four fractions
        # Yes refers to more than 2 standard deviations below the global mean/median
        # in our notes, fractionYes = alpha
        if fractionYes > 1:
            fractionYes = 1
        invCDFalpha = ndtri(fractionYes)
        fractionHigh     = ndtr(invCDFalpha - 1.)
        fractionModerate = fractionYes - ndtr(invCDFalpha - 1.)
        fractionMild     = ndtr(invCDFalpha + 1.) - fractionYes
        fractionNormal   = 1. - ndtr(invCDFalpha + 1.)
        restratification = {}
        restratification["normal"] = fractionNormal
        restratification["mild"] = fractionMild
        restratification["moderate"] = fractionModerate
        restratification["high"] = fractionHigh
        return restratification

    def update_child_dists(self):
        for ageGroup in self.children.ageGroups:
            ageGroup.updateStuntingDist()
            ageGroup.updateWastingDist()
            ageGroup.updateBFDist()
            ageGroup.updateAnaemiaDist()

    def update_women_dists(self):
        for pop in self.pops[1:]:
            for ageGroup in pop.ageGroups:
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
            for ageGroup in pop.ageGroups:
                ageGroup.distrib_pop()

    def _applyPrevTimeTrends(self): # TODO: haven't done mortality yet
        for ageGroup in self.children.ageGroups:
            # stunting
            probStunted = sum(ageGroup.stuntingDist[cat] for cat in self.constants.stuntedList)
            newProb = probStunted * ageGroup.annualPrevChange['Stunting']
            ageGroup.stuntingDist = self.restratify(newProb)
            # wasting
            probWasted = sum(ageGroup.wastingDist[cat] for cat in self.constants.wastedList)
            newProb = probWasted * ageGroup.annualPrevChange['Wasting']
            nonWastedProb = self.restratify(newProb)
            for nonWastedCat in self.constants.nonWastedList:
                ageGroup.wastingDist[nonWastedCat] = nonWastedProb[nonWastedCat]
            # anaemia
            probAnaemic = sum(ageGroup.anaemiaDist[cat] for cat in self.constants.anaemicList)
            newProb = probAnaemic * ageGroup.annualPrevChange['Anaemia']
            ageGroup.anaemiaDist['anaemic'] = newProb
            ageGroup.anaemiaDist['not anaemic'] = 1 - newProb
        for ageGroup in self.PW.ageGroups + self.nonPW.ageGroups:
            probAnaemic = sum(ageGroup.anaemiaDist[cat] for cat in self.constants.anaemicList)
            newProb = probAnaemic * ageGroup.annualPrevChange['Anaemia']
            ageGroup.anaemiaDist['anaemic'] = newProb
            ageGroup.anaemiaDist['not anaemic'] = 1-newProb

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
            neonates = self.children.ageGroups[0]
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