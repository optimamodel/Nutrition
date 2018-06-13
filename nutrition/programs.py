import settings, numpy, functools

class Program(object):
    """Each instance of this class is an intervention,
    and all necessary data will be stored as attributes. Will store name, targetpop, popsize, coverage, edges etc
    Also want it to set absolute number covered, coverage frac (coverage amongst entire pop), normalised coverage (coverage amongst target pop)"""
    def __init__(self, name, prog_data, default_params):
        self.name = name
        self.default = default_params
        self.prog_deps = prog_data.prog_deps
        self.famplan_methods = prog_data.famplan_methods
        self.settings = settings.Settings()
        self.year = None
        self.all_years = None
        self.annual_cov = None
        self.unrestr_init_cov = None
        self.cov_scen = None
        self.func = None
        self.inv_func = None
        self.twin_ind = None

        self.target_pops = prog_data.prog_target[self.name] # frac of each population which is targeted
        self.unit_cost = prog_data.prog_info['unit cost'][self.name]
        self.saturation = prog_data.prog_info['saturation coverage of target population'][self.name]
        self.restr_init_cov = prog_data.prog_info['baseline coverage'][self.name]

        self._set_target_ages()
        self._set_impacted_ages() # TODO: This func could contain the info for how many multiples needed for unrestricted population calculation (IYCF)
        self._set_exclusion_deps()
        self._set_threshold_deps()

    def set_annual_cov(self, pops, all_years):
        """
        Sets values for 'annual_covs' for the baseline and calibration (typically first 2 years) only.
        If a calibration coverage has been specified in the workbook, this will override the baseline coverage.
        This feature allows different costs to be calculated from the calibration coverage
        :return:
        """
        self.set_pop_sizes(pops)
        self.set_init_unrestr()
        self.annual_cov = [self.unrestr_init_cov]*len(all_years) # default assuming constant over time

    def update_cov(self, cov, restr_cov):
        """Main function for providing new coverages for a program
        Lists must not have any missing values, so interpolate if missing"""
        # check the data type of cov
        if isinstance(cov, list):
            self.annual_cov = self.interp_cov(cov, restr_cov)
        else: # scalar
            self._set_scalar(cov, restr_cov)

    def interp_cov(self, cov, restr_cov):
        """cov: a list of values with length equal to simulation period, excluding first year"""
        years = numpy.array(self.all_years)
        cov_list = numpy.array(cov)
        not_nan = numpy.logical_not(numpy.isnan(cov_list))
        if any(not_nan):
            # for 1 or more present values, baseline up to first present value, interpolate between, then constant if end values missing
            trueIndx = [i for i, x in enumerate(not_nan) if x]
            firstTrue = trueIndx[0]
            startCov = [self.restr_init_cov]*len(cov_list[:firstTrue])
            # scaledCov = coverages * self.restrictedPopSize / self.unrestrictedPopSize # convert to unrestricted coverages
            endCov = list(numpy.interp(years[firstTrue:], years[not_nan], cov_list[not_nan]))
            # scale each coverage
            if restr_cov:
                interped = [self.get_unrestr_cov(cov) for cov in startCov + endCov]
            else: # no need to scale
                interped = [cov for cov in startCov + endCov]
        else:
            # is all nan, assume constant at baseline
            interped = [self.unrestr_init_cov] * len(years)
        return interped

    def _set_scalar(self, cov, restr_cov):
        if restr_cov:
            cov = self.get_unrestr_cov(cov)
        interpolated = [cov] * len(self.all_years)
        self.annual_cov = [self.unrestr_init_cov] + interpolated

    def get_unrestr_cov(self, restr_cov):
        return restr_cov*self.restrictedPopSize / self.unrestr_popsize

    def set_pop_sizes(self, pops):
        self._setRestrictedPopSize(pops)
        self._setUnrestrictedPopSize(pops)

    def set_init_unrestr(self):
        self.unrestr_init_cov = (self.restr_init_cov * self.restrictedPopSize) / \
                                          self.unrestr_popsize
        # self.unrestrictedCalibrationCov = (self.restrictedCalibrationCov * self.restrictedPopSize) / \
        #                                   self.unrestrictedPopSize

    def adjust_cov(self, pops, year):
        # set unrestricted pop size so coverages account for growing population size
        oldURP = self.unrestr_popsize
        self.set_pop_sizes(pops)# TODO: is this the optimal place to do this?
        oldCov = self.annual_cov[year]
        newCov = oldURP * oldCov / self.unrestr_popsize
        self.annual_cov.append(newCov)

    def _set_target_ages(self):
        """
        The ages at whom programs are targeted
        :return:
        """
        self.agesTargeted = []
        for age in self.settings.all_ages:
            fracTargeted = self.target_pops[age]
            if fracTargeted > 0.001: # floating point tolerance
                self.agesTargeted.append(age)

    def _set_impacted_ages(self):
        """
        The ages who are impacted by this program
        :return:
        """
        self.agesImpacted = []
        for age in self.settings.all_ages:
            impacted = self.default.impacted_pop[self.name][age]
            if impacted > 0.001: # floating point tolerance
                self.agesImpacted.append(age)

    def _setUnrestrictedPopSize(self, populations):
        """
        sum of the total pop for each targeted age group
        """
        # TMP SOLUTION: THE DENOMINATOR FOR CALCULATING PROGRAM COVERAGE WILL USE sum(CEILING(FRAC TARGETED) * POP SIZE) over all pops targeted. I.E. FOR IYCF WITH FRAC >1, we get normalised sum
        from math import ceil
        self.unrestr_popsize = 0.
        for pop in populations:
            self.unrestr_popsize += sum(ceil(self.target_pops[age.age]) * age.pop_size for age in pop.age_groups
                                        if age.age in self.agesTargeted)

    def _setRestrictedPopSize(self, populations):
        self.restrictedPopSize = 0.
        for pop in populations:
            self.restrictedPopSize += sum(age.pop_size * self.target_pops[age.age] for age in pop.age_groups
                                         if age.age in self.agesTargeted)

    def _set_exclusion_deps(self):
        """
        List containing the names of programs which restrict the coverage of this program to (1 - coverage of independent program)
        :return:
        """
        self.exclusionDependencies = []
        try: # TODO: don't like this, perhaps switch order or cleanup before hand?
            dependencies = self.prog_deps[self.name]['Exclusion dependency']
        except KeyError:
            dependencies = []
        for program in dependencies:
            self.exclusionDependencies.append(program)

    def _set_threshold_deps(self):
        """
        List containing the name of programs which restrict the coverage of this program to coverage of independent program
        :return:
        """
        self.thresholdDependencies = []
        try:
            dependencies = self.prog_deps[self.name]['Threshold dependency']
        except KeyError:
            dependencies = []
        for program in dependencies:
            self.thresholdDependencies.append(program)

    def stunting_update(self, age_group):
        """
        Will get the total stunting update for a single program.
        Since we assume independence between each kind of stunting update
        and across programs (that is, after we have accounted for dependencies),
        the order of multiplication of updates does not matter.
        """
        age_group.stuntingUpdate *= self._get_cond_prob_update(age_group, 'Stunting')

    def anaemia_update(self, age_group):
        """
        Program which directly impact anaemia.
        :param age_group: instance of age_group class
        """
        age_group.anaemiaUpdate *= self._get_cond_prob_update(age_group, 'Anaemia')

    def get_wasting_update(self, age_group):
        """
        Programs which directly impact wasting prevalence or incidence.
        Wasting update is comprised of two parts:
            1. Prevention interventions, which alter the incidence of wasting
            2. Treatment interventions, which alter the prevalence of wasting
        Update of type 1. is converted into a prevalence update.
        The total update is the product of these two.
        :param age_group:
        :return:
        """
        prevUpdate = self.__wasting_prev_update(age_group)
        incidUpdate = self._wasting_update_incid(age_group)
        for wastingCat in ['MAM', 'SAM']:
            combined = prevUpdate[wastingCat] * incidUpdate[wastingCat]
            age_group.wastingUpdate[wastingCat] *= combined

    def get_famplan_update(self, age_group):
        age_group.FPupdate *= self.annual_cov[self.year]

    def wasting_prevent_update(self, age_group):
        update = self._wasting_incid_update(age_group)
        for wastingCat in self.settings.wasted_list:
            age_group.wastingPreventionUpdate[wastingCat] *= update[wastingCat]

    def wasting_treat_update(self, age_group):
        update = self.__wasting_prev_update(age_group)
        for wastingCat in self.settings.wasted_list:
            age_group.wastingTreatmentUpdate[wastingCat] *= update[wastingCat]

    def dia_incidence_update(self, age_group):
        """
        This function accounts for the _direct_ impact of programs on diarrhoea incidence
        :param age_group:
        :return:
        """
        update = self._effectiveness_update(age_group, 'Effectiveness incidence')
        age_group.diarrhoeaIncidenceUpdate *= update['Diarrhoea']

    def bf_update(self, age_group):
        """
        Accounts for the program's direct impact on breastfeeding practices
        :param age_group:
        :return:
        """
        age_group.bfPracticeUpdate += self._bf_practice_update(age_group)


    def get_mortality_update(self, age_group):
        """
        Programs which directly impact mortality rates
        :return:
        """
        update = self._effectiveness_update(age_group, 'Effectiveness mortality')
        for cause in age_group.causes_death:
            age_group.mortalityUpdate[cause] *= update[cause]

    def get_bo_update(self, age_group):
        """
        Programs which directly impact birth outcomes
        :return:
        """
        update = self._bo_update()
        for BO in self.settings.birth_outcomes:
            age_group.birthUpdate[BO] *= update[BO]

    def get_birthage_update(self, age_group):
        update = self._ba_update()
        for BA in self.default.birthAges:
            age_group.birthUpdate[BA] *= update[BA]

    def _get_new_prob(self, coverage, probCovered, probNotCovered):
        return coverage * probCovered + (1.-coverage) * probNotCovered

    def _get_cond_prob_update(self, age_group, risk):
        """This uses law of total probability to update a given age groups for risk types
        Possible risk types are 'Stunting' & 'Anaemia' """
        oldProb = age_group.getFracRisk(risk)
        probIfCovered = age_group.probConditionalCoverage[risk][self.name]['covered']
        probIfNotCovered = age_group.probConditionalCoverage[risk][self.name]['not covered']
        newProb = self._get_new_prob(self.annual_cov[self.year], probIfCovered, probIfNotCovered)
        reduction = (oldProb - newProb) / oldProb
        update = 1.-reduction
        return update

    def __wasting_prev_update(self, age_group):
        # overall update to prevalence of MAM and SAM
        update = {}
        for wastingCat in self.settings.wasted_list:
            oldProb = age_group.getWastedFrac(wastingCat)
            probWastedIfCovered = age_group.probConditionalCoverage[wastingCat][self.name]['covered']
            probWastedIfNotCovered = age_group.probConditionalCoverage[wastingCat][self.name]['not covered']
            newProb = self._get_new_prob(self.annual_cov[self.year], probWastedIfCovered, probWastedIfNotCovered)
            reduction = (oldProb - newProb) / oldProb
            update[wastingCat] = 1-reduction
        return update

    def _wasting_update_incid(self, age_group):
        incidenceUpdate = self._wasting_incid_update(age_group)
        update = {}
        for condition in self.settings.wasted_list:
            newIncidence = age_group.incidences[condition] * incidenceUpdate[condition]
            reduction = (age_group.incidences[condition] - newIncidence)/newIncidence
            update[condition] = 1-reduction
        return update

    def _wasting_incid_update(self, age_group):
        update = {}
        oldCov = self.annual_cov[self.year-1]
        for condition in self.settings.wasted_list:

            affFrac = age_group.prog_eff[(self.name, condition, 'Affected fraction')]
            effectiveness = age_group.prog_eff[(self.name, condition,'Effectiveness incidence')]
            reduction = affFrac * effectiveness * (self.annual_cov[self.year] - oldCov) / (1. - effectiveness*oldCov)
            update[condition] = 1.-reduction
        return update

    def _effectiveness_update(self, age_group, effType):
        """This covers mortality and incidence updates (except wasting)"""
        if 'incidence' in effType:
            toIterate = ['Diarrhoea'] # only model diarrhoea incidence
        else: # mortality
            toIterate = age_group.causes_death
        update = {cause: 1. for cause in toIterate}
        oldCov = self.annual_cov[self.year-1]
        for cause in toIterate:
            affFrac = age_group.prog_eff.get((self.name,cause,'Affected fraction'),0)
            effectiveness = age_group.prog_eff.get((self.name,cause,effType),0)
            reduction = affFrac * effectiveness * (self.annual_cov[self.year] - oldCov) / (1. - effectiveness*oldCov)
            update[cause] *= 1. - reduction
        return update

    def _bo_update(self):
        BOupdate = {BO: 1. for BO in self.settings.birth_outcomes}
        oldCov = self.annual_cov[self.year-1]
        for outcome in self.settings.birth_outcomes:
            affFrac = self.default.bo_progs[self.name]['affected fraction'][outcome]
            eff = self.default.bo_progs[self.name]['effectiveness'][outcome]
            reduction = affFrac * eff * (self.annual_cov[self.year] - oldCov) / (1. - eff*oldCov)
            BOupdate[outcome] = 1. - reduction
        return BOupdate

    def _ba_update(self):
        BAupdate = {BA: 1. for BA in self.default.birthAges}
        oldCov = self.annual_cov[self.year-1]
        for BA in self.default.birthAges:
            affFrac = self.default.birthAgeProgram[BA]['affected fraction']
            eff = self.default.birthAgeProgram[BA]['effectiveness']
            reduction = affFrac * eff * (self.annual_cov[self.year] - oldCov) / (1. - eff*oldCov)
            BAupdate[BA] = 1. - reduction
        return BAupdate

    def _bf_practice_update(self, age_group):
        correctPrac = age_group.correctBFpractice
        correctFracOld = age_group.bfDist[correctPrac]
        probCorrectCovered = age_group.probConditionalCoverage['Breastfeeding'][self.name]['covered']
        probCorrectNotCovered = age_group.probConditionalCoverage['Breastfeeding'][self.name]['not covered']
        probNew = self._get_new_prob(self.annual_cov[self.year], probCorrectCovered, probCorrectNotCovered)
        fracChange = probNew - correctFracOld
        return fracChange

    def set_costcov(self):
        costcurve = CostCovCurve(self.unit_cost, self.saturation, self.restrictedPopSize, self.unrestr_popsize)
        self.func, self.inv_func = costcurve.set_cost_curve()

    def get_spending(self):
        # spending is base on BASELINE coverages
        return self.inv_func(self.unrestr_init_cov)

    def scale_unit_costs(self, scaleFactor):
        self.unit_cost *= scaleFactor
        self.set_costcov()

class CostCovCurve:
    def __init__(self, unit_cost, saturation, restrictedPop, unrestrictedPop, curveType='linear'):
        self.curveType = curveType
        self.unit_cost = unit_cost
        self.saturation = saturation
        self.restrictedPop = restrictedPop
        self.unrestrictedPop = unrestrictedPop

    def set_cost_curve(self):
        if self.curveType == 'linear':
            curve = self._get_lin_curve()
            invcurve = self._get_inv_lin()
        else:
            curve = self._get_log_curve()
            invcurve = self._get_inv_log()
        return curve, invcurve

    def _get_lin_curve(self):
        m = 1. / self.unit_cost
        x0, y0 = [0., 0.]  # extra point
        if x0 == 0.:
            c = y0
        else:
            c = y0 / (m * x0)
        maxCoverage = self.restrictedPop * self.saturation
        linearCurve = functools.partial(self._lin_func, m, c, maxCoverage)
        return linearCurve

    def _get_inv_lin(self):
        m = 1. / self.unit_cost
        x0, y0 = [0., 0.]  # extra point
        if x0 == 0.:
            c = y0
        else:
            c = y0 / (m * x0)
        curve = functools.partial(self._inv_lin_func, m, c)
        return curve

    def _get_log_curve(self):
        """ Returns an increasing marginal costs logistic curve"""
        B = self.saturation * self.restrictedPop
        A = -B
        C = 0.
        D = self.unit_cost*B/2.
        curve = functools.partial(self._log_func, A, B, C, D)
        return curve

    def _get_inv_log(self):
        """ Inverse of the increasing marginal costs logistic curve
        WARNING: if coverage exceed saturation, will return infinity"""
        B = self.saturation * self.restrictedPop
        A = -B
        C = 0.
        D = self.unit_cost*B/2.
        curve = functools.partial(self._inv_log, A, B, C, D)
        return curve

    def _lin_func(self, m, c, max_cov, x):
        unres_maxcov = max_cov / self.unrestrictedPop
        return min((m * x + c)/self.unrestrictedPop, unres_maxcov)

    def _log_func(self, A, B, C, D, x):
        return (A + (B - A) / (1 + numpy.exp(-(x - C) / D))) / self.unrestrictedPop

    def _inv_lin_func(self, m, c, cov_frac):
        return (cov_frac*self.unrestrictedPop - c)/m

    def _inv_log(self, A, B, C, D, y):
        if D == 0:
            return 0
        else:
            return -D * numpy.log((B - y) / (y - A)) + C

def set_programs(prog_set, prog_data, default_params):
    programs = [Program(prog_name, prog_data, default_params) for prog_name in prog_set] # list of all program objects
    return programs