from functools import partial
from math import ceil
import numpy as np
import sciris as sc
from .settings import Settings
from .utils import get_new_prob


class Program(sc.prettyobj):
    """
    The base class for a program.
    This stores the relevant data and functionality for individual programs.
    """
    def __init__(self, name, all_years, progdata):
        """

        :param name: The name of the program (type string)
        :param all_years: The years for the simulation period (type list)
        :param progdata: Contains the following program data (class ProgData)
            1. Target populations
            2. Unit cost
            3. Cost-coverage curve type
            4. Saturation
            5. Baseline coverage
            6. Exclusion dependencies
            7. Threshold dependencies
        """
        self.name = name
        self.year = all_years[0]
        self.targetpopfracs = progdata.prog_target[name]
        self.unit_cost = progdata.costs[name]
        self.costtype = progdata.costtype[name]
        self.sat = progdata.sat[name]
        self.base_cov = progdata.base_cov[name]
        self.annualcov = np.zeros(len(all_years))
        self.annualspend = np.zeros(len(all_years))
        self.excl_deps = progdata.prog_deps[name]['Exclusion dependency']
        self.thresh_deps = progdata.prog_deps[name]['Threshold dependency']
        # attributes to be calculated later
        self.targetpopsize = 0
        self.totalpopsize = 0
        self.ref_spend = None
        self.costfunc = None
        self.covfunc = None
        self.totalpopsat = None
        self.base_spend = None
        self.famplan_methods = None
        self.pregav_sum = None

        self.ss = Settings()

        if 'amil' in self.name: # family planning program only
            self.famplan_methods = progdata.famplan_methods
            self.set_pregav_sum()
        self._settargetages()
        self._setimpactages(progdata.impacted_pop[name])

    def __repr__(self):
        output = sc.prepr(self)
        return output

    def getcov(self, popcov=True):
        """
        Retrieves the desired coverage vector
        :param popcov: population or target coverage (boolean)
        :return: A 1d numpy array, containing either population or target coverages
        """
        if popcov:
            return self.annualcov
        else:
            return self.annualcov * self.totalpopsize / self.targetpopsize

    def update_cov(self, cov, spend):
        """
        Sets the coverage and spending vectors for a program.
        :param cov: A 1d numpy array of population coverages.
        :param spend: A 1d numpy array of budgets
        :return: None
        """
        self.annualcov = cov
        self.annualspend = spend
        return

    def _interpscen(self, cov, years, scentype):
        """
        Interpolates the coverage and spending vectors for a program.
        Performs some basic validation on the vectors.
        :param cov: A 1d array of coverages or spending. Must be the same length as years.
        :param years: The years of the simulation
        :param scentype: The type of scenario, containing the substring 'ov' (coverage) or 'ud' (budget)
        :return: the interpolated coverage and spending vectors (1d numpy array)
        """
        if 'ov' in scentype:
            # Raise exception is invalid coverage value. Done here before converting to population coverages
            if (cov < 0).any() or (cov > 1).any():
                raise Exception("Coverage for '%s' outside range 0-1: %s" % (self.name, cov))
            # assume target coverage
            cov = self.getpopcov(cov)
            cov[0] = self.annualcov[0]
            not_nan = ~np.isnan(cov)
            interp_cov = np.interp(years, years[not_nan], cov[not_nan])
            interp_spend = self.covfunc(interp_cov)
        elif 'ud' in scentype: # budget
            # can't have negative spending
            if (cov < 0).any():
                raise Exception("Spending for '%s' below 0: %s" % (self.name, cov))
            cov[0] = self.annualspend[0]
            not_nan = ~np.isnan(cov)
            interp_spend = np.interp(years, years[not_nan], cov[not_nan])
            interp_cov = self.costfunc(interp_spend)
        else:
            raise Exception("Scenario type '%s' is not valid, must be 'coverage' or 'budget'" %scentype)
        return interp_cov, interp_spend

    def getpopcov(self, popcov):
        """ Expects an array of target population coverages """
        return popcov[:] * self.targetpopsize / self.totalpopsize

    def setpopsize(self, pops):
        self._settargetpop(pops)
        self._settotalpop(pops)
        # this accounts for different fractions within age bands
        self.totalpopsat = self.targetpopsize / self.totalpopsize
        return

    def setbasecov(self):
        popcov = (self.base_cov * self.targetpopsize) / self.totalpopsize
        self.annualcov[0] = popcov
        spend = self.covfunc(self.annualcov[:1])[0]
        self.base_spend = spend
        self.annualspend[0] = spend
        return

    def adjust_cov(self, pops, year): # todo: needs fixing for annualcov being an array now
        """ Defunct, requires updating"""
        # set unrestricted pop size so coverages account for growing population size
        oldURP = self.totalpopsize
        self.setpopsize(pops)# TODO: is this the optimal place to do this?
        oldCov = self.annualcov[year]
        newCov = oldURP * oldCov / self.totalpopsize
        self.annualcov.append(newCov)

    def _settargetages(self):
        """
        The ages at whom programs are targeted
        :return:
        """
        self.agesTargeted = []
        for age in self.ss.all_ages:
            fracTargeted = self.targetpopfracs[age]
            if fracTargeted > 0.001: # floating point tolerance
                self.agesTargeted.append(age)

    def _setimpactages(self, impacted_pop):
        """
        The ages who are impacted by this program
        :return:
        """
        self.agesImpacted = []
        for age in self.ss.all_ages:
            impacted = impacted_pop[age]
            if impacted > 0.001: # floating point tolerance
                self.agesImpacted.append(age)

    def _settotalpop(self, populations): # todo: revisit this
        """
        sum of the total pop for each targeted age group
        """
        # TMP SOLUTION: THE DENOMINATOR FOR CALCULATING PROGRAM COVERAGE WILL USE sum(CEILING(FRAC TARGETED) * POP SIZE) over all pops targeted. I.E. FOR IYCF WITH FRAC >1, we get normalised sum
        for pop in populations:
            self.totalpopsize += sum(ceil(self.targetpopfracs[age.age]) * age.pop_size for age in pop.age_groups
                                        if age.age in self.agesTargeted)

    def _settargetpop(self, populations):
        for pop in populations:
            self.targetpopsize += sum(age.pop_size * self.targetpopfracs[age.age] for age in pop.age_groups
                                         if age.age in self.agesTargeted)

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

    def set_pregav_sum(self):
        self.pregav_sum = sum(self.famplan_methods[prog]['Effectiveness'] * self.famplan_methods[prog]['Distribution']
                      for prog in self.famplan_methods.keys())

    def get_pregav_update(self, age_group):
        """ Even though this isn't technically an age group-specific update,
        for consistencies sake, this distributes the pregnancies averted uniformly across the age bands,
        but should really only need the sum of all averted births.
        (cov(t) - cov(t-1)) yields a symmetric update around the baseline coverage"""
        change =  self.annualcov[self.year] - self.annualcov[self.year-1]
        age_group.preg_av = self.pregav_sum * change / len(self.ss.wra_ages)

    def get_birthspace_update(self, age_group):
        """ Birth spacing in non-pregnant women impacts birth outcomes for newborns """
        age_group.birthspace_update += self._space_update(age_group)

    def _space_update(self, age_group):
        """ Update the proportion of pregnancies in the correct spacing category.
          This will only work on WRA: 15-19 years by design, since it isn't actually age-specific """
        correctold = age_group.birth_space[self.ss.optimal_space]
        probcov = age_group.probConditionalCoverage['Birth spacing'][self.name]['covered']
        probnot = age_group.probConditionalCoverage['Birth spacing'][self.name]['not covered']
        probnew = get_new_prob(self.annualcov[self.year], probcov, probnot)
        fracChange = probnew - correctold
        return fracChange

    def wasting_prevent_update(self, age_group):
        """ The update we calculate here is used as a % reduction in prevalence.
        Assumes that reduction in prevalence is same % as incidence"""
        update = self._wasting_incid_update(age_group)
        for wastingCat in self.ss.wasted_list:
            age_group.wastingPreventionUpdate[wastingCat] *= update[wastingCat]

    def wasting_treat_update(self, age_group):
        update = self._wasting_prev_update(age_group)
        for wastingCat in self.ss.wasted_list:
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
        for BO in self.ss.birth_outcomes:
            age_group.birthUpdate[BO] *= update[BO]

    def _get_cond_prob_update(self, age_group, risk):
        """This uses law of total probability to update a given age groups for risk types
        Possible risk types are 'Stunting' & 'Anaemia' """
        oldProb = age_group.frac_risk(risk)
        probIfCovered = age_group.probConditionalCoverage[risk][self.name]['covered']
        probIfNotCovered = age_group.probConditionalCoverage[risk][self.name]['not covered']
        newProb = get_new_prob(self.annualcov[self.year], probIfCovered, probIfNotCovered)
        reduction = (oldProb - newProb) / oldProb
        update = 1.-reduction
        return update

    def _wasting_prev_update(self, age_group):
        # overall update to prevalence of MAM and SAM
        update = {}
        for wastingCat in self.ss.wasted_list:
            oldProb = age_group.frac_wasted(wastingCat)
            probWastedIfCovered = age_group.probConditionalCoverage[wastingCat][self.name]['covered']
            probWastedIfNotCovered = age_group.probConditionalCoverage[wastingCat][self.name]['not covered']
            newProb = get_new_prob(self.annualcov[self.year], probWastedIfCovered, probWastedIfNotCovered)
            reduction = (oldProb - newProb) / oldProb
            update[wastingCat] = 1-reduction
        return update

    def _wasting_incid_update(self, age_group):
        update = {}
        oldCov = self.annualcov[self.year-1]
        for condition in self.ss.wasted_list:
            affFrac = age_group.prog_eff[(self.name, condition, 'Affected fraction')]
            effectiveness = age_group.prog_eff[(self.name, condition,'Effectiveness incidence')]
            reduction = affFrac * effectiveness * (self.annualcov[self.year] - oldCov) / (1. - effectiveness*oldCov)
            update[condition] = 1.-reduction
        return update

    def _effectiveness_update(self, age_group, effType):
        """This covers mortality and incidence updates (except wasting)"""
        if 'incidence' in effType:
            toIterate = ['Diarrhoea'] # only model diarrhoea incidence
        else: # mortality
            toIterate = age_group.causes_death
        update = {cause: 1. for cause in toIterate}
        oldCov = self.annualcov[self.year-1]
        for cause in toIterate:
            affFrac = age_group.prog_eff.get((self.name,cause,'Affected fraction'),0)
            effectiveness = age_group.prog_eff.get((self.name,cause,effType),0)
            reduction = affFrac * effectiveness * (self.annualcov[self.year] - oldCov) / (1. - effectiveness*oldCov)
            update[cause] *= 1. - reduction
        return update

    def _bo_update(self, age_group):
        BOupdate = {BO: 1. for BO in self.ss.birth_outcomes}
        oldCov = self.annualcov[self.year-1]
        for outcome in self.ss.birth_outcomes:
            affFrac = age_group.bo_eff[self.name]['affected fraction'][outcome]
            eff = age_group.bo_eff[self.name]['effectiveness'][outcome]
            reduction = affFrac * eff * (self.annualcov[self.year] - oldCov) / (1. - eff*oldCov)
            BOupdate[outcome] = 1. - reduction
        return BOupdate

    def _bf_practice_update(self, age_group):
        correctPrac = age_group.correct_bf
        correctFracOld = age_group.bf_dist[correctPrac]
        probCorrectCovered = age_group.probConditionalCoverage['Breastfeeding'][self.name]['covered']
        probCorrectNotCovered = age_group.probConditionalCoverage['Breastfeeding'][self.name]['not covered']
        probNew = get_new_prob(self.annualcov[self.year], probCorrectCovered, probCorrectNotCovered)
        fracChange = probNew - correctFracOld
        return fracChange

    def setcostfuncs(self):
        """ Set the cost-coverage function and corresponding inverse function """
        costcurve = CostCovCurve(self.unit_cost, self.sat, self.targetpopsize, self.totalpopsize, self.costtype)
        self.costfunc, self.covfunc = costcurve.setfuncs()

    def get_spending(self, covs):
        """
        Calculate the spending for given coverage
        :param covs: 1d numpy array
        :return: 1d numpy array
        """
        return self.covfunc(covs)


class CostCovCurve(sc.prettyobj):
    def __init__(self, unitcost, sat, targetpop, totalpop, costtype):
        self.costtype = costtype.lower()
        self.unitcost = unitcost
        self.sat = sat
        self.targetpop = targetpop
        self.totalpop = totalpop
        try:
            self.maxcov = sat * targetpop / totalpop
        except ZeroDivisionError:
            self.maxcov = 0
        self.approx = 0.95
        self.ss = Settings()

    def setfuncs(self):
        """
        Sets the cost-coverage function and its corresponding inverse.
        The functional form is determined by self.costtype
        :return: a cost coverage function and its inverse
        """
        if 'lin' in self.costtype:
            curve, invcurve = self._get_lin_curve()
        else:
            curve, invcurve = self._get_log_curve()
        return curve, invcurve

    def _get_lin_curve(self):
        m = 1. / self.unitcost
        x0, y0 = [0., 0.]  # extra point
        if x0 == 0.:
            c = y0
        else:
            c = y0 / (m * x0)
        linearCurve = partial(self._lin_func, m, c)
        invcurve = partial(self._inv_lin_func, m, c)
        return linearCurve, invcurve

    def _get_inv_lin(self):
        m = 1. / self.unitcost
        x0, y0 = [0., 0.]  # extra point
        if x0 == 0.:
            c = y0
        else:
            c = y0 / (m * x0)
        curve = partial(self._inv_lin_func, m, c)
        return curve

    def _get_log_curve(self):
        """ Returns a logisitic function with the desired marginal cost behaviour.
         The parameters for the 'increasing' marginal cost curve were solved for analytically,
         while other variants are created by shifting these """
        # 'increasing' is the default case
        b = self.sat * self.targetpop
        a = -b
        c = 0.
        d = self.unitcost * b / 2.
        yshift = 0
        xscale = 1
        yscale = 1
        if 'decre' in self.costtype:
            endx, endy = self.get_endpoints(a, b, c, d)
            yshift = endy # shift up
            c += endx # shift right
        elif 'shaped' in self.costtype:
            endx, endy = self.get_endpoints(a, b, c, d)
            yshift = endy # shift up
            c += endx # shift right
            xscale = 2 # shrink x
            yscale = 2 # shrink y
        # account for the error around (0,0)
        zero = np.array([0])
        curve = partial(self._log_func, a, b, c, d, yshift, xscale, yscale)
        inv = partial(self._inv_log, a, b, c, d, yshift, xscale, yscale)
        yerr = curve(zero)
        xerr = inv(zero)
        curve = partial(self._log_func, a, b, c, d, yshift, xscale, yscale, offset=yerr)
        inv = partial(self._inv_log, a, b, c, d, yshift, xscale, yscale, offset=xerr)
        return curve, inv

    def _lin_func(self, m, c, x):
        """ Expects x to be a 1D numpy array.
         Return: a numpy array of the same length as x """
        numcov = m * x[:] + c
        cov = np.divide(numcov, self.totalpop, out=np.zeros(len(x)), where=self.totalpop!=0)
        return np.minimum(cov, self.maxcov)

    def _log_func(self, a, b, c, d, yshift, xscale, yscale, x, offset=0):
        """ The generalized logistic function, with extra params for scaling and shifting so that all desired curves can be produced.
        Offset is a way to account for the error around (0,0) produced by approximating the 'end' value of the logisitic curve.
         This function is truncated for the decreasing marginal costs curve, which can exceed maxcov. """
        numcov = ((a + yshift) + (b - a) / (1 + np.exp(-(x*xscale - c) / d))) / yscale
        cov = np.divide(numcov, self.totalpop, out=np.zeros(len(x)), where=self.totalpop!=0) - offset
        return np.minimum(cov, self.maxcov)

    def _inv_lin_func(self, m, c, y):
        """
        :param m:
        :param c:
        :param y: a 1d numpy array of unrestricted coverage fractions
        :return: a 1d numpy array with same length as y
        """
        y[y>self.maxcov] = self.maxcov
        return (y*self.totalpop - c)/m

    def _inv_log(self, a, b, c, d, yshift, xscale, yscale, y, offset=0):
        """ Inverse of the logistic curve with given parameters.
         If coverage >= the asymptote, takes an approx of this. """
        y[y>=self.maxcov] = self.approx*self.maxcov # prevent inf
        numcovered = y * self.totalpop
        cost = xscale*(-d * np.log((b - yscale * numcovered + yshift) / (yscale * numcovered - a - yshift)) + c) - offset
        return cost

    def get_endpoints(self, a, b, c, d):
        """Estimates the average change of the increasing marginal costs curve,
        so that the decreasing and mixed marginal cost curves can be fit.
        The average change dictates the gradient of a linear curve to base logistic curves upon.
        Calculates between points (0,0) and (cost, 95% of saturation) """
        # estimate cost at 95% of saturation
        endcov = np.array([self.approx*self.maxcov])
        endcost = self._inv_log(a, b, c, d, 0, 1, 1, endcov)
        endnum = endcov * self.totalpop
        return endcost[0], endnum[0]


def set_programs(progset, progdata, all_years):
    """ Do the error handling here because we have the progset param at this point. """
    programs = sc.odict()
    for name in progset:
        programs[name] = Program(name, all_years, progdata)
    return programs


class ProgramInfo(sc.prettyobj):
    def __init__(self, prog_data):
        self.prog_data = prog_data
        self.programs = None
        self.prog_areas = None
        self.all_years = None
        self.sim_years = None

        self.refs = None
        self.curr = None
        self.fixed = None
        self.free = None

    def setupprogs(self, pops):
        for prog in self.programs.values():
            prog.setpopsize(pops)
            prog.setcostfuncs()
            prog.setbasecov()

    def setallocs(self, add_funds, fix_curr, rem_curr):
        self.refs = self.get_refs()
        self.curr = self.get_curr()
        self.fixed = self.get_fixed(fix_curr)
        self.free = self.get_free(add_funds, fix_curr, rem_curr)

    def get_refs(self):
        ref_allocs = np.zeros(len(self.programs))
        for i, prog in self.programs.enumvals():
            if prog.reference:
                ref_allocs[i] = prog.get_spending(prog.annualcov)[0]
            else:
                ref_allocs[i] = 0
        return ref_allocs

    def get_curr(self):
        allocs = np.zeros(len(self.programs))
        for i, prog in self.programs.enumvals():
            allocs[i] = prog.get_spending(prog.annualcov)[0]
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

    def makeprogs(self, prog_set, all_years):
        self.all_years = all_years
        self.sim_years = all_years[1:]
        self.programs = set_programs(prog_set, self.prog_data, all_years)
        self.prog_areas = self._clean_prog_areas(self.prog_data.prog_areas, prog_set)
        self._set_ref_progs()
        self._sort_progs()

    def base_progset(self):
        return self.prog_data.base_prog_set

    def _set_ref_progs(self):
        for program in self.programs.values():
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
        allNames = self.programs.keys()
        for prog in self.programs.values():
            prog.thresh_deps = [name for name in prog.thresh_deps if name in allNames]
            prog.excl_deps = [name for name in prog.excl_deps if name in allNames]

    def _clean_prog_areas(self, prog_areas, progset):
        """ Removed programs from program area list if not included in analysis """
        retain = {}
        for risk, names in prog_areas.items():
            retain[risk] = [prog for prog in names if prog in progset]
        return retain

    def _get_thresh_roots(self):
        """ Makes a list of all programs with dependencies """
        openSet = [program for program in self.programs.values() if program.thresh_deps]
        closedSet = [program for program in self.programs.values() if program not in openSet] # independence
        idx = len(closedSet)
        return openSet, closedSet, idx

    def _get_excl_roots(self):
        openSet = [program for program in self.programs.values() if program.excl_deps]
        closedSet = [program for program in self.programs.values() if program not in openSet] # independence
        idx = len(closedSet)
        return openSet, closedSet, idx

    def _excl_sort(self):
        openSet, closedSet, idx = self._get_excl_roots()
        for program in openSet:
            dependentNames = set(program.excl_deps)
            closedSetNames = set([prog.name for prog in closedSet])
            if dependentNames.issubset(closedSetNames):  # all parent programs in closed set
                closedSet += [program]
        self.exclusionOrder = closedSet[idx:]

    def _thresh_sort(self):
        open_set, closed_set, idx = self._get_thresh_roots()
        for program in open_set:
            dependentNames = set(program.thresh_deps)
            closedSetNames = set([prog.name for prog in closed_set])
            if dependentNames.issubset(closedSetNames):  # all parent programs in closed set
                closed_set += [program]
        self.thresholdOrder = closed_set[idx:]

    def getscen(self, covs, scentype, years):
        """
        Checks and fully defines the coverage and budget vectors used in the scenario.
        :param covs: the coverages or budgets for each program (list of lists)
        :param scentype:
        :param years:
        :return:
        """
        popcov = np.zeros(shape=(len(self.programs), len(years)))
        spend = np.zeros(shape=(len(self.programs), len(years)))
        covs = self.check_cov(covs, years)
        for i,prog in self.programs.enumvals():
            popcov[i], spend[i] = prog._interpscen(covs[i], years, scentype)
        return popcov, spend

    def check_cov(self, covs, years):
        numyears = len(years)-1 # not including baseline
        newcovs = np.zeros((len(self.programs), numyears+1))
        for i,prog in self.programs.enumvals():
            try:
                cov = covs[i]
                if isinstance(cov, float):
                    newcov = np.full(numyears, cov)
                elif len(cov) == numyears:
                    newcov = np.array(cov)
                elif len(cov) < numyears:
                    newcov = np.concatenate((cov, np.full(numyears - len(cov), cov[-1])), axis=0)
                elif len(cov) > numyears:
                    newcov = cov[1:] # this is hack fix for when baseline spending included
            except IndexError: # coverage scenario not specified, assume constant
                newcov = np.full(numyears, prog.base_cov)
            newcovs[i][1:] = newcov
        newcovs = newcovs.astype(float) # force conversion to treat None as nan and convert integers
        return newcovs

    def setcovs(self, covs, spends, restrictcovs):
        for i,prog in self.programs.enumvals():
            cov = covs[i]
            spend = spends[i]
            prog.update_cov(cov, spend)
        # restrict covs
        if restrictcovs:
            self.restrict_covs()

    def determine_cov_change(self):
        for prog in self.programs.values():
            if abs(prog.annualcov[prog.year-1] - prog.annualcov[prog.year]) > 1e-3:
                return True
            else:
                pass
        return False

    def adjust_covs(self, pops, year):
        for program in self.programs.values():
            program.adjust_cov(pops, year)

    def update_prog_year(self, year):
        for prog in self.programs.values():
            prog.year = year

    def get_ann_covs(self, year):
        covs = {}
        for prog in self.programs.values():
            covs[prog.name] = prog.annualcov[year]
        return covs

    def restrict_covs(self):
        """
        Uses the ordering of both dependency lists to restrict the coverage of programs.
        Assumes that the coverage is given as peopleCovered/totalpopsize.
        Since the order of dependencies matters, was decided to apply threshold first then exclusion dependencies.
        Coverage will be restricted even in baseline year.
        """
        # threshold
        for child in self.thresholdOrder:
            for parname in child.thresh_deps:
                for year in self.all_years:
                    par = next(prog for prog in self.programs.values() if prog.name == parname)
                    # assuming uniform coverage across age bands, we can use the unrestricted coverage (NOT restricted)
                    maxcov_child = max(child.totalpopsat - (par.totalpopsat - par.annualcov[year]), 0)
                    if child.annualcov[year] > maxcov_child:
                        child.annualcov[year] = maxcov_child
        # exclusion
        for child in self.exclusionOrder:
            for parname in child.excl_deps:
                for year in self.all_years:
                    par = next((prog for prog in self.programs.values() if prog.name == parname))
                    # assuming uniform coverage across age bands, we can use the unrestricted coverage (NOT restricted)
                    maxcov_child = max(child.totalpopsat - par.annualcov[year], 0) # if coverage of parent exceeds child sat
                    if child.annualcov[year] > maxcov_child:
                        child.annualcov[year] = maxcov_child