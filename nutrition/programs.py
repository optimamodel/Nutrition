import numpy as np
from .settings import Settings
from functools import partial
import sciris.core as sc

class Program(object):
    """Each instance of this class is an intervention,
    and all necessary data will be stored as attributes. Will store name, targetpop, popsize, coverage, edges etc
    Also want it to set absolute number covered, coverage frac (coverage amongst entire pop), normalised coverage (coverage amongst target pop)"""
    def __init__(self, name, prog_data, all_years):
        self.name = name
        self.prog_deps = prog_data.prog_deps
        self.famplan_methods = prog_data.famplan_methods # todo: want these here or in nonPW class???
        self.settings = Settings()
        self.all_years = all_years # todo: may want this in ProgInfo
        self.sim_years = all_years[1:]
        self.year = all_years[0]
        self.annual_cov = np.zeros(len(all_years))
        self.annual_spend = np.zeros(len(all_years))
        self.func = None
        self.inv_func = None

        self.target_pops = prog_data.prog_target[self.name] # frac of each population which is targeted
        self.unit_cost = prog_data.prog_info['unit cost'][self.name]
        self.saturation = prog_data.prog_info['saturation coverage of target population'][self.name]
        self.restr_init_cov = prog_data.prog_info['baseline coverage'][self.name]

        self._set_target_ages()
        self._set_impacted_ages(prog_data.impacted_pop[self.name]) # TODO: This func could contain the info for how many multiples needed for unrestricted population calculation (IYCF)
        self._set_exclusion_deps()
        self._set_threshold_deps()

    def update_cov(self, cov, spend):
        self.annual_cov = cov
        self.annual_spend = spend

    def interp_cov(self, cov, restr_cov):
        """ cov: a list of coverages with one-to-one correspondence with sim_years
        restr_cov: boolean indicating if the coverages are restricted or unrestricted """
        if restr_cov:
            cov = map(self.get_unrestr_cov, cov)
        years = np.array(self.all_years)
        cov = np.array(cov, dtype=float) # force conversion to treat None as nan
        cov[0] = self.annual_cov[0]
        not_nan = ~np.isnan(cov)
        interped = np.interp(years, years[not_nan], cov[not_nan])
        return interped

    def check_cov(self, cov, years):
        numyears = len(years)
        if isinstance(cov, float):
            new = np.full(numyears, cov)
        elif len(cov) < numyears:
            new = np.concatenate((cov, np.full(numyears, cov[-1])), axis=0)
        return new

    def get_unrestr_cov(self, restr_cov):
        return restr_cov*self.restr_popsize / self.unrestr_popsize

    def set_pop_sizes(self, pops):
        self._setRestrictedPopSize(pops)
        self._setUnrestrictedPopSize(pops)

    def set_init_unrestr(self):
        unrestr_cov = (self.restr_init_cov * self.restr_popsize) / self.unrestr_popsize
        self.annual_cov[0] = unrestr_cov

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

    def _set_impacted_ages(self, impacted_pop):
        """
        The ages who are impacted by this program
        :return:
        """
        self.agesImpacted = []
        for age in self.settings.all_ages:
            impacted = impacted_pop[age]
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
        self.restr_popsize = 0.
        for pop in populations:
            self.restr_popsize += sum(age.pop_size * self.target_pops[age.age] for age in pop.age_groups
                                         if age.age in self.agesTargeted)

    def _set_exclusion_deps(self):
        """
        List containing the names of programs which restrict the coverage of this program to (1 - coverage of independent program)
        :return:
        """
        self.exclusionDependencies = []
        try: # TODO: don't like this, perhaps switch order or cleanup before hand?
            dependencies = self.prog_deps[self.name]['Exclusion dependency']
        except:
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
        except:
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
        update = self._bo_update(age_group)
        for BO in self.settings.birth_outcomes:
            age_group.birthUpdate[BO] *= update[BO]

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

    def _bo_update(self, age_group):
        BOupdate = {BO: 1. for BO in self.settings.birth_outcomes}
        oldCov = self.annual_cov[self.year-1]
        for outcome in self.settings.birth_outcomes:
            affFrac = age_group.bo_eff[self.name]['affected fraction'][outcome]
            eff = age_group.bo_eff[self.name]['effectiveness'][outcome]
            reduction = affFrac * eff * (self.annual_cov[self.year] - oldCov) / (1. - eff*oldCov)
            BOupdate[outcome] = 1. - reduction
        return BOupdate

    def _bf_practice_update(self, age_group):
        correctPrac = age_group.correct_bf
        correctFracOld = age_group.bf_dist[correctPrac]
        probCorrectCovered = age_group.probConditionalCoverage['Breastfeeding'][self.name]['covered']
        probCorrectNotCovered = age_group.probConditionalCoverage['Breastfeeding'][self.name]['not covered']
        probNew = self._get_new_prob(self.annual_cov[self.year], probCorrectCovered, probCorrectNotCovered)
        fracChange = probNew - correctFracOld
        return fracChange

    def set_costcov(self):
        costcurve = CostCovCurve(self.unit_cost, self.saturation, self.restr_popsize, self.unrestr_popsize)
        self.func, self.inv_func = costcurve.set_cost_curve()

    def get_cov(self, spend):
        """
        Calculate the coverage for given expenditure
        :param spend: a 1d numpy array
        :return: a 1d numpy array
        """
        return self.func(spend)

    def get_spending(self, covs):
        """
        Calculate the spending for given coverage
        :param covs: 1d numpy array
        :return: 1d numpy array
        """
        return self.inv_func(covs)

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
        linearCurve = partial(self._lin_func, m, c, maxCoverage)
        return linearCurve

    def _get_inv_lin(self):
        m = 1. / self.unit_cost
        x0, y0 = [0., 0.]  # extra point
        if x0 == 0.:
            c = y0
        else:
            c = y0 / (m * x0)
        curve = partial(self._inv_lin_func, m, c)
        return curve

    def _get_log_curve(self):
        """ Returns an increasing marginal costs logistic curve"""
        B = self.saturation * self.restrictedPop
        A = -B
        C = 0.
        D = self.unit_cost*B/2.
        curve = partial(self._log_func, A, B, C, D)
        return curve

    def _get_inv_log(self):
        """ Inverse of the increasing marginal costs logistic curve
        WARNING: if coverage exceed saturation, will return infinity"""
        B = self.saturation * self.restrictedPop
        A = -B
        C = 0.
        D = self.unit_cost*B/2.
        curve = partial(self._inv_log, A, B, C, D)
        return curve

    def _lin_func(self, m, c, max_cov, x):
        """ Expects x to be a 1D numpy array.
         Return: a numpy array of the same length as x """
        unres_maxcov = np.full(len(x), max_cov / self.unrestrictedPop)
        return np.minimum((m * x[:] + c)/self.unrestrictedPop, unres_maxcov)

    def _log_func(self, A, B, C, D, x):
        return (A + (B - A) / (1 + np.exp(-(x[:] - C) / D))) / self.unrestrictedPop

    def _inv_lin_func(self, m, c, y):
        """
        :param m:
        :param c:
        :param y: a 1d numpy array of unrestricted coverage fractions
        :return: a 1d numpy array with same length as y
        """
        return (y[:]*self.unrestrictedPop - c)/m

    def _inv_log(self, A, B, C, D, y):
        if D == 0:
            return 0
        else:
            return -D * np.log((B - y[:]) / (y[:] - A)) + C


def set_programs(prog_set, prog_data, all_years):
    programs = [Program(prog_name, prog_data, all_years) for prog_name in prog_set] # list of all program objects
    return programs
    



class ProgramInfo: # todo: would like to incorporate spending info in here, even for scenarios... so user can get this info
    def __init__(self, prog_data):
        self.prog_data = prog_data
        self.programs = None
        self.prog_areas = None

        self.refs = None
        self.curr = None
        self.fixed = None
        self.free = None

    def get_allocs(self, add_funds, fix_curr, rem_curr):
        self.refs = self.get_refs()
        self.curr = self.get_curr()
        self.fixed = self.get_fixed(fix_curr)
        self.free = self.get_free(add_funds, fix_curr, rem_curr)

    def get_refs(self):
        ref_allocs = np.zeros(len(self.programs))
        for i, prog in enumerate(self.programs):
            if prog.reference:
                ref_allocs[i] = prog.get_spending(prog.annual_cov)[0]
            else:
                ref_allocs[i] = 0
        return ref_allocs

    def get_curr(self):
        allocs = np.zeros(len(self.programs))
        for i, prog in enumerate(self.programs):
            allocs[i] = prog.get_spending(prog.annual_cov)[0]
        return allocs

    def get_fixed(self, fix_curr):
        """
        Fixed allocations will contain reference allocations as well, for easy use in the objective function.
        Reference progs stored separately for ease of model output.
        :param fix_curr:
        :return:
        """
        if fix_curr:
            fixed = sc.dcp(self.curr)
        else:
            fixed = sc.dcp(self.refs)
        return fixed

    def get_free(self, add_funds, fix_curr, rem_curr):
        """
        freeFunds = currentExpenditure + add_funds - fixedFunds (if not remove current funds)
        freeFunds = additional (if want to remove current funds)

        fixedFunds includes both reference programs as well as currentExpenditure, if the latter is to be fixed.
        I.e. if all of the currentExpenditure is fixed, freeFunds = add_funds.
        :return:
        """
        if rem_curr and fix_curr:
            raise Exception("::Error: Cannot remove current funds and fix current funds simultaneously::")
        elif rem_curr and (not fix_curr):  # this is additional to reference spending
            freeFunds = add_funds
        elif not rem_curr:
            freeFunds = sum(self.curr) - sum(self.fixed) + add_funds
        return freeFunds

    def make_progs(self, prog_set, all_years):
        self.programs = set_programs(prog_set, self.prog_data, all_years)
        self.prog_areas = self._clean_prog_areas(self.prog_data.prog_areas, prog_set)
        self._set_ref_progs()
        self._sort_progs()

    def set_years(self, all_years):
        for prog in self.programs:
            prog.year = all_years[0]
            prog.sim_years = all_years[1:]

    def _set_ref_progs(self):
        for program in self.programs:
            if program.name in self.prog_data.ref_progs:
                program.reference = True
            else:
                program.reference = False

    def _sort_progs(self):
        """
        Sorts the program list by dependency such that the resulting order will be most independent to least independent.
        Uses a variant of a breadth-first search,
        whereby the order of the sorted list is a flattened tree structure
        (root, first level, second level etc..)
        :return:
        """
        self._rem_missing_progs()
        self._thresh_sort()
        self._excl_sort()

    def _rem_missing_progs(self):
        """ Removes programs from dependencies lists which are not included in analysis """
        allNames = set([prog.name for prog in self.programs])
        for prog in self.programs:
            prog.thresholdDependencies = [name for name in prog.thresholdDependencies if name in allNames]
            prog.exclusionDependencies = [name for name in prog.exclusionDependencies if name in allNames]

    def _clean_prog_areas(self, prog_areas, progset):
        """ Removed programs from program area list if not included in analysis """
        retain = {}
        for risk, names in prog_areas.iteritems():
            retain[risk] = [prog for prog in names if prog in progset]
        return retain

    def _get_thresh_roots(self):
        openSet = self.programs[:]
        closedSet = [program for program in openSet if not program.thresholdDependencies] # independence
        openSet = [program for program in openSet if program not in closedSet]
        return openSet, closedSet

    def _get_excl_roots(self):
        openSet = self.programs[:]
        closedSet = [program for program in openSet if not program.exclusionDependencies] # independence
        openSet = [program for program in openSet if program not in closedSet]
        return openSet, closedSet

    def _excl_sort(self):
        openSet, closedSet = self._get_excl_roots()
        for program in openSet:
            dependentNames = set(program.exclusionDependencies)
            closedSetNames = set([prog.name for prog in closedSet])
            if dependentNames.issubset(closedSetNames):  # all parent programs in closed set
                closedSet += [program]
        self.exclusionOrder = closedSet[:]

    def _thresh_sort(self):
        openSet, closedSet = self._get_thresh_roots()
        for program in openSet:
            dependentNames = set(program.thresholdDependencies)
            closedSetNames = set([prog.name for prog in closedSet])
            if dependentNames.issubset(closedSetNames):  # all parent programs in closed set
                closedSet += [program]
        self.thresholdOrder = closedSet[:]

    def set_init_covs(self, pops):
        for prog in self.programs:
            prog.set_pop_sizes(pops)
            prog.set_init_unrestr()

    def set_init_pops(self, pops):
        np.array()
        for prog in self.programs:
            prog.set_pop_sizes(pops)

    def set_costcovs(self):
        for prog in self.programs:
            prog.set_costcov()

    def get_cov_scen(self, covs, scentype, years):
        """ If scen is a budget scenario, convert it to unrestricted coverage.
        If scen is a coverage object, assumed to be restricted cov and coverted
        Return: list of lists"""
        unrestr_cov = np.zeros(shape=(len(self.programs), len(years)))
        spend = np.zeros(shape=(len(self.programs), len(years)))
        covs = self.check_cov(covs, years)
        if 'ov' in scentype:
            for i, prog in enumerate(self.programs):
                unrestr_cov[i] = prog.interp_cov(covs[i], restr_cov=True)
                spend[i] = prog.inv_func(unrestr_cov[i])
        elif 'ud' in scentype:
            for i, prog in enumerate(self.programs):
                unrestr_cov[i] = prog.interp_cov(prog.func(covs[i]), restr_cov=False)
                spend[i] = prog.inv_func(unrestr_cov[i])
        else:
            raise Exception("Error: scenario type '{}' is not valid".format(scentype))
        return unrestr_cov, spend

    def check_cov(self, covs, years):
        numyears = len(years)
        newcovs = np.zeros((len(self.programs), numyears))
        for i, prog in enumerate(self.programs):
            try:
                cov = covs[i]
                if isinstance(cov, float):
                    newcovs[i] = np.full(numyears, cov)
                elif len(covs) == numyears:
                    newcovs[i] = np.array(cov)
                elif len(cov) < numyears:
                    newcovs[i] = np.concatenate((cov, np.full(numyears - len(cov), cov[-1])), axis=0)
            except IndexError: # coverage scenario not specified, assume constant
                newcovs[i] = np.full(numyears, prog.annual_cov[0])
        #
        # for i, cov in enumerate(covs):
        #     if isinstance(cov, float):
        #         newcovs[i] = np.full(numyears, cov)
        #     elif not cov:
        #         newcovs[i] = np.full(numyears, np.nan)
        #     elif len(covs) == numyears:
        #         newcovs[i] = np.array(cov)
        #     elif len(cov) < numyears:
        #         newcovs[i] = np.concatenate((cov, np.full(numyears-len(cov), cov[-1])), axis=0)
        #     else:
        #         raise Exception(":: Error :: scenario is not valid")
        return newcovs

    def update_covs(self, pops, covs, spends):
        for i, prog in enumerate(self.programs):
            cov = covs[i]
            spend = spends[i]
            prog.update_cov(cov, spend)
        # restrict covs
        self.restrict_covs(pops)

    def determine_cov_change(self):
        for prog in self.programs:
            if abs(prog.annual_cov[prog.year-1] - prog.annual_cov[prog.year]) > 1e-3:
                return True
            else:
                pass
        return False

    def adjust_covs(self, pops, year):
        for program in self.programs:
            program.adjust_cov(pops, year)

    def update_prog_year(self, year):
        for prog in self.programs:
            prog.year = year

    def get_ann_covs(self, year):
        covs = {}
        for prog in self.programs:
            covs[prog.name] = prog.annual_cov[year]
        return covs

    def restrict_covs(self, pops):
        """
        Uses the ordering of both dependency lists to restrict the coverage of programs.
        Assumes that the coverage is given as peopleCovered/unrestr_popsize.
        Since the order of dependencies matters, was decided to apply threshold first then exclusion dependencies
        Method:
        GET OVERLAPPING AGE GROUPS BETWEEN PARENT AND CHILD NODES
        SUM OVERLAPPING POP SIZES FOR PARENT NODE
        MULTIPLY BY COVERAGE % TO GET NUMBER OF PEOPLE IN OVERLAPPING POP WHO ARE ALREADY COVERED BY PARENT
        DIVIDE THIS BY RESTRICTED POP SIZE FOR CHILD NODE
        BEHAVIOUR DEPENDENT UPON RESTRICTION TYPE & SIZE OF RATIO.
        """

        # Need to get the overlapping pop because the numCovered generated by cost curves
        # potentially includes populations which are not common to both
        # threshold
        for child in self.thresholdOrder:
            for parentName in child.thresholdDependencies:
                # get overlapping age groups (intersection)
                parent = next((prog for prog in self.programs if prog.name == parentName))
                commonAges = list(set(child.agesTargeted).intersection(parent.agesTargeted))
                parentPopSize = 0.
                for pop in pops:
                    parentPopSize += sum(age.pop_size for age in pop.age_groups if age.age in commonAges)
                numCoveredInOverlap = parent.annual_cov[parent.year] * parentPopSize
                percentCoveredByParent = numCoveredInOverlap / child.restr_popsize
                if percentCoveredByParent < 1:
                    childMaxCov = numCoveredInOverlap / child.restr_popsize
                else:
                    childMaxCov = child.restr_popsize / child.unrestr_popsize
                if child.annual_cov[child.year] > childMaxCov:
                    child.annual_cov[child.year] = childMaxCov
        #exclusion
        for child in self.exclusionOrder:
            if child.exclusionDependencies:
                # get population covered by all parent nodes
                numCoveredInOverlap = 0
                for parentName in child.exclusionDependencies:
                    parentPopSize = 0
                    # get overlapping age groups (intersection)
                    parent = next((prog for prog in self.programs if prog.name == parentName))
                    commonAges = list(set(child.agesTargeted).intersection(parent.agesTargeted))
                    for pop in pops:
                        parentPopSize += sum(age.pop_size for age in pop.age_groups if age.age in commonAges)
                    numCoveredInOverlap += parent.annual_cov[parent.year] * parentPopSize
                percentCoveredByParent = numCoveredInOverlap / child.restr_popsize
                if percentCoveredByParent < 1:
                    childMaxCov = (child.restr_popsize - numCoveredInOverlap) / child.unrestr_popsize
                else:
                    childMaxCov = 0
                if child.annual_cov[child.year] > childMaxCov:
                    child.annual_cov[child.year] = childMaxCov