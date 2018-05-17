from numpy import exp, log, interp, isnan, array, logical_not
from copy import deepcopy as dcp

class Program(object):
    """Each instance of this class is an intervention,
    and all necessary data will be stored as attributes. Will store name, targetpop, popsize, coverage, edges etc
    Also want it to set absolute number covered, coverage frac (coverage amongst entire pop), normalised coverage (coverage amongst target pop)"""
    def __init__(self, name, default_params, settings): # TODO: would like to put cov info into another object, read in from the relevant data book.
        self.name = name
        self.default = default_params # TODO: not all data can be found in here (i.e. prog data)
        self.settings = settings
        self.year = None
        self.all_years = None
        self.annual_cov = None
        self.unrestr_init_cov = None

        # TODO: this should all be handed over through Project, read in from input data book
        self.target_pops = self.default.programTargetPop[self.name] # frac of each population which is targeted
        self.unit_cost = self.default.costCurveInfo['unit cost'][self.name]
        self.saturation = self.default.costCurveInfo['saturation coverage'][self.name]
        self.coverageProjections = dcp(self.default.programAnnualSpending[self.name]) # will be altered
        self.restr_init_cov = self.default.costCurveInfo['baseline coverage'][self.name]

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
        self.annual_cov = {year: self.unrestr_init_cov for year in all_years} # default assuming constant over time

    def update_cov(self, cov, restr_cov):
        """Main function for providing new coverages for a program
        Lists must not have any missing values, so interpolate if missing"""
        # check the data type of cov
        if isinstance(cov, list):
            self._interp_cov(cov, restr_cov)
        else: # scalar
            self._set_scalar(cov, restr_cov)

    def _interp_cov(self, cov, restr_cov):
        """cov: a list of values with length equal to simulation period, excluding first year"""
        years = array(self.all_years[1:]) # TODO: depends if baseline cov included in this or not.
        cov_list = array(cov)
        not_nan = logical_not(isnan(cov_list))
        if any(not_nan):
            # for 1 or more present values, baseline up to first present value, interpolate between, then constant if end values missing
            trueIndx = [i for i, x in enumerate(not_nan) if x]
            firstTrue = trueIndx[0]
            startCov = [self.restr_init_cov for x in cov_list[:firstTrue]]
            # scaledCov = coverages * self.restrictedPopSize / self.unrestrictedPopSize # convert to unrestricted coverages
            endCov = list(interp(years[firstTrue:], years[not_nan], cov_list[not_nan]))
            # scale each coverage
            if restr_cov:
                interped = {year: self.get_unrestr_cov(cov) for year, cov in zip(years, startCov + endCov)}
            else: # no need to scale
                interped = {year: cov for year, cov in zip(years, startCov + endCov)}
        else:
            # is all nan, assume constant at baseline
            interped = {year: self.unrestr_init_cov for year in years}
        self.annual_cov.update(interped)

    def _set_scalar(self, cov, restr_cov):
        if restr_cov:
            scaled_cov = self.get_unrestr_cov(cov)
        interpolated = {year: scaled_cov for year in self.all_years}
        self.annual_cov.update(interpolated)

    def get_unrestr_cov(self, restr_cov):
        return restr_cov*self.restrictedPopSize / self.unrestrictedPopSize

    def set_pop_sizes(self, pops):
        self._setRestrictedPopSize(pops)
        self._setUnrestrictedPopSize(pops)

    def set_init_unrestr(self):
        self.unrestr_init_cov = (self.restr_init_cov * self.restrictedPopSize) / \
                                          self.unrestrictedPopSize
        # self.unrestrictedCalibrationCov = (self.restrictedCalibrationCov * self.restrictedPopSize) / \
        #                                   self.unrestrictedPopSize

    def _adjustCoverage(self, pops, year):
        # set unrestricted pop size so coverages account for growing population size
        oldURP = dcp(self.unrestrictedPopSize)
        self.set_pop_sizes(pops)# TODO: is this the optimal place to do this?
        oldCov = self.annual_cov[year]
        newCov = oldURP * oldCov / self.unrestrictedPopSize
        self.annual_cov.update({year:newCov})

    def updateCoverage(self, newCoverage, pops):
        """Update all values pertaining to coverage for a program"""
        self.proposedCoverageNum = newCoverage
        self.set_pop_sizes(pops)
        self.proposedCoverageFrac = self.proposedCoverageNum / self.unrestrictedPopSize

    def updateCoverageFromPercentage(self, newCoverage, pops): # TODO: wrong b/c coverages already converted in UR coverages
        """Update all values pertaining to coverage for a program.
        Assumes new coverage is restricted coverage"""
        self.set_pop_sizes(pops)
        restrictedCovNum = self.restrictedPopSize * newCoverage
        self.proposedCoverageFrac = restrictedCovNum / self.unrestrictedPopSize

    def _set_target_ages(self):
        """
        The ages at whom programs are targeted
        :return:
        """
        self.agesTargeted = []
        for age in self.default.allAges:
            fracTargeted = self.default.programTargetPop[self.name][age]
            if fracTargeted > 0.001: # floating point tolerance
                self.agesTargeted.append(age)

    def _set_impacted_ages(self):
        """
        The ages who are impacted by this program
        :return:
        """
        self.agesImpacted = []
        for age in self.default.allAges:
            impacted = self.default.programImpactedPop[self.name][age]
            if impacted > 0.001: # floating point tolerance
                self.agesImpacted.append(age)

    def _setUnrestrictedPopSize(self, populations):
        """
        sum of the total pop for each targeted age group
        """
        # TMP SOLUTION: THE DENOMINATOR FOR CALCULATING PROGRAM COVERAGE WILL USE sum(CEILING(FRAC TARGETED) * POP SIZE) over all pops targeted. I.E. FOR IYCF WITH FRAC >1, we get normalised sum
        from math import ceil
        self.unrestrictedPopSize = 0.
        for pop in populations:
            self.unrestrictedPopSize += sum(ceil(self.target_pops[age.age])*age.getAgeGroupPopulation() for age in pop.ageGroups
                                           if age.age in self.agesTargeted)

    def _setRestrictedPopSize(self, populations):
        self.restrictedPopSize = 0.
        for pop in populations:
            self.restrictedPopSize += sum(age.getAgeGroupPopulation() * self.target_pops[age.age] for age in pop.ageGroups
                                         if age.age in self.agesTargeted)

    def _set_exclusion_deps(self):
        """
        List containing the names of programs which restrict the coverage of this program to (1 - coverage of independent program)
        :return:
        """
        self.exclusionDependencies = []
        dependencies = self.default.programDependency[self.name]['Exclusion dependency']
        for program in dependencies:
            self.exclusionDependencies.append(program)

    def _set_threshold_deps(self):
        """
        List containing the name of programs which restrict the coverage of this program to coverage of independent program
        :return:
        """
        self.thresholdDependencies = []
        dependencies = self.default.programDependency[self.name]['Threshold dependency']
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
        for wastingCat in self.default.wastedList:
            age_group.wastingPreventionUpdate[wastingCat] *= update[wastingCat]

    def wasting_treat_update(self, age_group):
        update = self.__wasting_prev_update(age_group)
        for wastingCat in self.default.wastedList:
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
        for cause in self.default.causesOfDeath:
            age_group.mortalityUpdate[cause] *= update[cause]

    def get_bo_update(self, age_group):
        """
        Programs which directly impact birth outcomes
        :return:
        """
        update = self._bo_update()
        for BO in self.default.birthOutcomes:
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
        for wastingCat in self.default.wastedList:
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
        for condition in self.default.wastedList:
            newIncidence = age_group.incidences[condition] * incidenceUpdate[condition]
            reduction = (age_group.incidences[condition] - newIncidence)/newIncidence
            update[condition] = 1-reduction
        return update

    def _wasting_incid_update(self, age_group):
        update = {}
        oldCov = self.annual_cov[self.year-1]
        for condition in self.default.wastedList:
            affFrac = age_group.programEffectiveness[self.name][condition]['Affected fraction']
            effectiveness = age_group.programEffectiveness[self.name][condition]['Effectiveness incidence']
            reduction = affFrac * effectiveness * (self.annual_cov[self.year] - oldCov) / (1. - effectiveness*oldCov)
            update[condition] = 1.-reduction
        return update

    def _effectiveness_update(self, age_group, effType):
        """This covers mortality and incidence updates (except wasting)"""
        if 'incidence' in effType:
            toIterate = ['Diarrhoea'] # only model diarrhoea incidence
        else: # mortality
            toIterate = self.default.causesOfDeath
        update = {cause: 1. for cause in toIterate}
        oldCov = self.annual_cov[self.year-1]
        for cause in toIterate:
            affFrac = age_group.programEffectiveness[self.name][cause]['Affected fraction']
            effectiveness = age_group.programEffectiveness[self.name][cause][effType]
            reduction = affFrac * effectiveness * (self.annual_cov[self.year] - oldCov) / (1. - effectiveness*oldCov)
            update[cause] *= 1. - reduction
        return update

    def _bo_update(self):
        BOupdate = {BO: 1. for BO in self.default.birthOutcomes}
        oldCov = self.annual_cov[self.year-1]
        for outcome in self.default.birthOutcomes:
            affFrac = self.default.BOprograms[self.name]['affected fraction'][outcome]
            eff = self.default.BOprograms[self.name]['effectiveness'][outcome]
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
        self.costCurveOb = CostCovCurve(self.unit_cost, self.saturation, self.restrictedPopSize, self.unrestrictedPopSize)
        self.costCurveFunc = self.costCurveOb._setCostCovCurve()

    def get_spending(self):
        # spending is base on BASELINE coverages
        return self.costCurveOb.get_spending(self.unrestr_init_cov) # TODO: want to change this so that uses annual Coverages

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

    def _setCostCovCurve(self):
        if self.curveType == 'linear':
            curve = self._linearCostCurve()
        else:
            curve = self._increasingCostsLogisticCurve()
        return curve

    def _increasingCostsLogisticCurve(self):
        B = self.saturation * self.restrictedPop
        A = -B
        C = 0.
        D = self.unit_cost*B/2.
        curve = self._getLogisticCurve(A, B, C, D)
        return curve

    def _getLogisticCurve(self, A, B, C, D):
        """This is a logistic curve with each parameter (A,B,C,D) provided by the user"""
        logisticCurve = lambda x: (A + (B - A) / (1 + exp(-(x - C) / D)))
        return logisticCurve

    def get_spending(self, covFrac):
        """Assumes standard increasing marginal costs curve or linear """
        covNumber = covFrac * self.unrestrictedPop
        if self.curveType == 'linear':
            m = 1. / self.unit_cost
            x0, y0 = [0., 0.]  # extra point
            if x0 == 0.:
                c = y0
            else:
                c = y0 / (m * x0)
            spending = (covNumber - c)/m
        else:
            B = self.saturation * self.restrictedPop
            A = -B
            C = 0.
            D = self.unit_cost * B / 2.
            curve = self.inverseLogistic(A, B, C, D)
            spending = curve(covNumber)
        return spending

    def _linearCostCurve(self):
        m = 1. / self.unit_cost
        x0, y0 = [0.,0.] #extra point
        if x0 == 0.:
            c = y0
        else:
            c = y0 / (m * x0)
        maxCoverage = self.restrictedPop * self.saturation
        linearCurve = lambda x: (min(m * x + c, maxCoverage))
        return linearCurve

    # def _plotCurve(self):
    #     import matplotlib.pyplot as plt
    #     from numpy import linspace
    #     xpts = linspace(0, 100000000, 10000)
    #     funcVal = []
    #     for x in xpts:
    #         funcVal.append(self.curve(x))
    #     plt.plot(xpts, funcVal)

    def inverseLogistic(self, A, B, C, D):
        if D == 0.: # this is a temp fix for removing interventions
            inverseCurve = lambda y: 0.
        else:
            inverseCurve = lambda y: -D * log((B - y) / (y - A)) + C
        return inverseCurve

def set_programs(default_params, prog_set):
    programs = [Program(prog_name, default_params) for prog_name in prog_set] # list of all program objects
    return programs