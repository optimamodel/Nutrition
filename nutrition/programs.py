import traceback
from functools import partial
from math import ceil
import numpy as np
import sciris as sc
from .settings import Settings
from .utils import get_new_prob
from . import utils




class Program(sc.prettyobj):
    """Each instance of this class is an intervention,
    and all necessary data will be stored as attributes. Will store name, targetpop, popsize, coverage, edges etc
    Restricted coverage: the coverage amongst the target population (assumed given by user)
    Unrestricted coverage: the coverage amongst the entire population """
    def __init__(self, name, all_years, progdata):
        self.name = name
        self.year = all_years[0]
        self.years = all_years
        self.target_pops = progdata.prog_target[name]
        self.unit_cost = progdata.costs[name]
        self.costtype = progdata.costtype[name]
        self.sat = progdata.sat[name]
        self.max_inc = progdata.max_inc[name]
        self.max_dec = progdata.max_dec[name]
        self.base_cov = progdata.base_cov[name]
      
        self.annual_cov = np.zeros(len(all_years)) #this is the unrestr_cov
        self.annual_restr_cov = np.ones(len(all_years)) * self.base_cov #only calculated in adjust_cov
        self.annual_spend = np.zeros(len(all_years))
        self.excl_deps = progdata.prog_deps[name]['Exclusion dependency']
        self.thresh_deps = progdata.prog_deps[name]['Threshold dependency']
        self.popn = np.zeros(len(all_years))
        
        
        # attributes to be calculated later
        self.ref_spend = None
        self.func = None
        self.inv_func = None
        self.sat_unrestr = None
        self.base_spend = None
        self.famplan_methods = None
        self.pregav_sum = None
        

        self.ss = Settings()
        

        if 'amil' in self.name: # family planning program only
            self.famplan_methods = progdata.famplan_methods
            self.set_pregav_sum()
        self._set_target_ages()
        self._set_impacted_ages(progdata.impacted_pop[name])

    def __repr__(self):
        output = sc.prepr(self)
        return output

    def get_cov(self, unrestr=True):
        """ Extracts either the restricted or unrestricted coverage array """
        if unrestr:
            return self.annual_cov
                     
        else:
            return self.annual_restr_cov

    def initialize_cov(self, cov, restr_cov, spend):
        self.annual_cov = cov
        self.annual_restr_cov = restr_cov
        self.annual_spend = spend

    def interp_scen(self, cov, years, scentype, progname):
        """ cov: a list of coverages/spending with one-to-one correspondence with sim_years
        restr_cov: boolean indicating if the coverages are restricted or unrestricted """
        if 'coverage' in scentype:
            # Raise exception is invalid coverage value. Done here before converting to unrestricted coverages
            if (sc.sanitize(cov) < 0).any() or (sc.sanitize(cov) > 1).any():
                raise Exception("Coverage for '%s' outside range 0-1: %s" % (progname, cov))
            # assume restricted cov
            # cov = self.get_unrestr_cov(cov)
            cov[0] = self.annual_cov[0]
            not_nan = ~np.isnan(cov)
            interp_restr_cov = np.interp(years, years[not_nan], cov[not_nan])
            interp_cov  = self.get_unrestr_cov(interp_restr_cov)
            interp_spend = self.inv_func(interp_cov) #will not be exactly matching if there is population growth, but will get fixed by adjust_cov later
        elif 'budget' in scentype: # budget
            # can't have negative spending
            if (sc.sanitize(cov) < 0).any():
                raise Exception("Spending for '%s' below 0: %s" % (progname, cov))
            cov[0] = self.annual_spend[0]
            not_nan = ~np.isnan(cov)
            interp_spend = np.interp(years, years[not_nan], cov[not_nan])
            interp_cov = self.func(interp_spend)
            interp_restr_cov = interp_cov * self.unrestr_popsize / self.restr_popsize
        else:
            raise Exception("Scenario type '%s' is not valid, must be 'coverage' or 'budget'" %scentype)
        return interp_cov, interp_restr_cov, interp_spend

    def get_unrestr_cov(self, restr_cov):
        """ Expects an array of restricted coverages """
        return restr_cov[:] * self.restr_popsize / self.unrestr_popsize

    def set_pop_sizes(self, pops):
        self._set_restrpop(pops)
        self._set_unrestrpop(pops)
        # this accounts for different fractions within age bands
        self.sat_unrestr = self.restr_popsize / self.unrestr_popsize

    def set_init_unrestr(self):
        unrestr_cov = (self.base_cov * self.restr_popsize) / self.unrestr_popsize
        self.annual_cov[0] = unrestr_cov

    def adjust_cov(self, pops, year, growth=False):
        """" This functions adjust coverage and spending to the annual population growth in each time step
            - First it ensures both restricted and unrestircted population sizes are updated
            - Then, cost coverage curves are also updaed as per the population size
            - "fixed budget" ensures the budget is constant over the period, however, the coverage is slightly decreasing
            - "fixed coverage"" ensures covergae is constant, however, the budget is adjusted to the population so it is slowly increasing"""
        # set unrestricted pop size so coverages account for growing population size
        if growth:
            self._set_unrestrpop(pops) # ensure population sizes are updated to the current timestep
            self._set_restrpop(pops)
            self.set_costcov() #ensure cost curve is updated to new population size, TODO check: code may be (much?) faster to just update pop size and curve if nonlinear?
            # old_cov = sc.dcp(self.annual_cov)[year]
            old_restr_cov = sc.dcp(self.annual_restr_cov[year])
            old_spend = sc.dcp(self.annual_spend[year])
        
        #work out what we want the coverage to be
        if growth == "fixed budget":
            self.annual_spend[year] = old_spend
            self.annual_cov[year] = self.func(self.annual_spend)[year]
            self.annual_restr_cov[year] = self.annual_cov[year] * self.unrestr_popsize / self.restr_popsize
        elif growth == "fixed coverage":
            self.annual_restr_cov[year] = old_restr_cov #note: maintaining fixed restricted coverage rather than overall coverage
            self.annual_cov[year] = old_restr_cov * self.restr_popsize / self.unrestr_popsize 
            self.annual_spend[year] = self.get_spending(self.annual_cov)[year] #note that we have updated the cost curve so this should be correct for all scenarios
        elif not growth: #no changes will be necessary
            pass
        else:
            raise Exception("Growth type '%s' is not valid, must be False, 'fixed budget' or 'fixed coverage'" %growth)      
        
                
    def _set_target_ages(self):
        """
        The ages at whom programs are targeted
        :return:
        """
        self.agesTargeted = []
        for age in self.ss.all_ages:
            fracTargeted = self.target_pops[age]
            if fracTargeted > 0.001: # floating point tolerance
                self.agesTargeted.append(age)

    def _set_impacted_ages(self, impacted_pop):
        """
        The ages who are impacted by this program
        :return:
        """
        self.agesImpacted = []
        for age in self.ss.all_ages:
            impacted = impacted_pop[age]
            if impacted > 0.001: # floating point tolerance
                self.agesImpacted.append(age)

    def _set_unrestrpop(self, populations):
        """
        sum of the total pop for each targeted age group
        """
        # TMP SOLUTION: THE DENOMINATOR FOR CALCULATING PROGRAM COVERAGE WILL USE sum(CEILING(FRAC TARGETED) * POP SIZE) over all pops targeted. I.E. FOR IYCF WITH FRAC >1, we get normalised sum
        self.unrestr_popsize = 0.
        for pop in populations:
                self.unrestr_popsize += sum(ceil(self.target_pops[age.age]) * age.pop_size for age in pop.age_groups
                                            if age.age in self.agesTargeted)

    def _set_restrpop(self, populations):
        self.restr_popsize = 0.
        for pop in populations:
                self.restr_popsize += sum(age.pop_size * self.target_pops[age.age] for age in pop.age_groups
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
        change =  self.annual_cov[self.year] - self.annual_cov[self.year-1]
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
        probnew = get_new_prob(self.annual_cov[self.year], probcov, probnot)
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
        newProb = get_new_prob(self.annual_cov[self.year], probIfCovered, probIfNotCovered)
        reduction = sc.safedivide(oldProb - newProb, oldProb, default=0.0)  # If the denominator is 0.0 or close, set reduction to zero (no change)
        update = 1.-reduction
        return update

    def _wasting_prev_update(self, age_group):
        # overall update to prevalence of MAM and SAM
        update = {}
        for wastingCat in self.ss.wasted_list:
            oldProb = age_group.frac_wasted(wastingCat)
            probWastedIfCovered = age_group.probConditionalCoverage[wastingCat][self.name]['covered']
            probWastedIfNotCovered = age_group.probConditionalCoverage[wastingCat][self.name]['not covered']
            newProb = get_new_prob(self.annual_cov[self.year], probWastedIfCovered, probWastedIfNotCovered)
            reduction = sc.safedivide(oldProb - newProb, oldProb, default=0.0)  # If the denominator is 0.0 or close, set reduction to zero (no change)
            update[wastingCat] = 1-reduction
        return update

    def _wasting_incid_update(self, age_group):
        update = {}
        oldCov = self.annual_cov[self.year-1]
        for condition in self.ss.wasted_list:
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
        BOupdate = {BO: 1. for BO in self.ss.birth_outcomes}
        oldCov = self.annual_cov[self.year-1]
        for outcome in self.ss.birth_outcomes:
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
        probNew = get_new_prob(self.annual_cov[self.year], probCorrectCovered, probCorrectNotCovered)
        fracChange = probNew - correctFracOld
        return fracChange

    def set_costcov(self):
        costcurve = CostCovCurve(self.unit_cost, self.sat, self.restr_popsize, self.unrestr_popsize, self.costtype)
        self.func, self.inv_func = costcurve.set_cost_curve()

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

class CostCovCurve(sc.prettyobj):
    def __init__(self, unit_cost, sat, restrictedPop, unrestrictedPop, costtype):
        self.costtype = costtype.lower()
        self.unit_cost = unit_cost
        self.sat = sat
        self.restrictedPop = restrictedPop
        self.unrestrictedPop = unrestrictedPop
        try:
            self.maxcov = sat * restrictedPop / unrestrictedPop
        except ZeroDivisionError:
            self.maxcov = 0
        self.approx = 0.95
        self.ss = Settings()

    def set_cost_curve(self):
        if 'lin' in self.costtype:
            curve, invcurve = self._get_lin_curve()
        else:
            curve, invcurve = self._get_log_curve()
        return curve, invcurve

    def _get_lin_curve(self):
        m = 1. / self.unit_cost
        x0, y0 = [0., 0.]  # extra point
        if x0 == 0.:
            c = y0
        else:
            c = y0 / (m * x0)
        linearCurve = partial(self._lin_func, m, c)
        invcurve = partial(self._inv_lin_func, m, c)
        return linearCurve, invcurve

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
        """ Returns a logisitic function with the desired marginal cost behaviour.
         The parameters for the 'increasing' marginal cost curve were solved for analytically,
         while other variants are created by shifting these """
        # 'increasing' is the default case
        b = self.sat * self.restrictedPop
        a = -b
        c = 0.
        d = self.unit_cost * b / 2.
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
        cov = np.divide(numcov, self.unrestrictedPop, out=np.zeros(len(x)), where=self.unrestrictedPop!=0)
        return np.minimum(cov, self.maxcov)

    def _log_func(self, a, b, c, d, yshift, xscale, yscale, x, offset=0):
        """ The generalized logistic function, with extra params for scaling and shifting so that all desired curves can be produced.
        Offset is a way to account for the error around (0,0) produced by approximating the 'end' value of the logisitic curve.
         This function is truncated for the decreasing marginal costs curve, which can exceed maxcov. """
        numcov = ((a + yshift) + (b - a) / (1 + np.exp(-(x*xscale - c) / d))) / yscale
        cov = np.divide(numcov, self.unrestrictedPop, out=np.zeros(len(x)), where=self.unrestrictedPop!=0) - offset
        return np.minimum(cov, self.maxcov)

    def _inv_lin_func(self, m, c, y):
        """
        :param m:
        :param c:
        :param y: a 1d numpy array of unrestricted coverage fractions
        :return: a 1d numpy array with same length as y
        """
        y[y>self.maxcov] = self.maxcov
        return (y*self.unrestrictedPop - c)/m

    def _inv_log(self, a, b, c, d, yshift, xscale, yscale, y, offset=0):
        """ Inverse of the logistic curve with given parameters.
         If coverage >= the asymptote, takes an approx of this. """
        y[y>=self.maxcov] = self.approx*self.maxcov # prevent inf
        numcovered = y * self.unrestrictedPop
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
        endnum = endcov * self.unrestrictedPop
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
        self.covs = None
        #self.max_inc = 0
        #self.max_dec = 0

    def get_allocs(self, add_funds, fix_curr, rem_curr):
        self.refs = self.get_refs()
        self.curr = self.get_curr()
        self.fixed = self.get_fixed(fix_curr)
        self.free = self.get_free(add_funds, fix_curr, rem_curr)

    def get_refs(self):
        ref_allocs = np.zeros(len(self.programs))
        for i, prog in self.programs.enumvals():
            if prog.reference:
                ref_allocs[i] = prog.get_spending(prog.annual_cov)[0]
            else:
                ref_allocs[i] = 0
        return ref_allocs

    def get_curr(self):
        allocs = np.zeros(len(self.programs))
        for i, prog in self.programs.enumvals():
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
        self.all_years = all_years
        self.sim_years = all_years[1:]
        self.programs = set_programs(prog_set, self.prog_data, all_years)
        self.prog_areas = self._clean_prog_areas(self.prog_data.prog_areas, prog_set)
        self._set_ref_progs()
        self._sort_progs()

    def get_base_spend(self):
        for prog in self.programs.values():
            spend = prog.inv_func(prog.annual_cov[:1])[0]
            prog.base_spend = spend
            prog.annual_spend[0] = spend

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

    def set_init_covs(self, pops):
        for prog in self.programs.values():
            prog.set_pop_sizes(pops)
            prog.set_init_unrestr()

    def set_costcovs(self):
        for prog in self.programs.values():
            prog.set_costcov()

    def get_cov_scen(self, covs, scentype, years):
        """ If scen is a budget scenario, convert it to unrestricted coverage.
        If scen is a coverage object, assumed to be restricted cov and converted
        Return: list of lists"""
        unrestr_covs = np.zeros(shape=(len(self.programs), len(years)))
        spends = np.zeros(shape=(len(self.programs), len(years)))
        covs = self.check_cov(covs, years)
        restr_covs = self.check_cov(covs, years)
        for i,prog in self.programs.enumvals():
            unrestr_covs[i], restr_covs[i], spends[i] = prog.interp_scen(covs[i], years, scentype, prog.name)
        return unrestr_covs, restr_covs, spends

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

    def initialize_covs(self, covs, restr_covs, spends, restrictcovs):
        """
        Called once at the beginning of a model run to set the initial intended coverages/spendings for each program
        Note: Annual updates to program coverages/spendings are set in the same program.annual_cov location, and set by adjust_covs
        """
        for i,prog in self.programs.enumvals():
            cov = covs[i]
            restr_cov = restr_covs[i]
            spend = spends[i]
            prog.initialize_cov(cov, restr_cov, spend)
        # restrict covs
        if restrictcovs:
            self.restrict_covs()
            

    def determine_cov_change(self):
        for prog in self.programs.values():
            if abs(prog.annual_cov[prog.year-1] - prog.annual_cov[prog.year]) > 1e-3:
                return True
            else:
                pass
        return False
    
    def rebalance_ramped_coverage(self, year):
        """ This function supports smooth ramping of functions.
        This ensures that ramping changes preserve budget between years
        
        1. Enforce ramping on each program coverage, work out (a) the change in spending for each program from the previous year, and (b) the difference in spending as a result of ramping on each program
        2. If the total difference DUE TO RAMPING is positive (too much money spent in year compared to year-1), proportionally reduce spending on programs from the previous year for programs given extra spend
        3. If the total difference DUE TO RAMPING is negative (too little money spent in year compared to year-1), proportionally increase spending on programs from the previous year for programs with reduced spend
        4. Recalculate coverage and restricted coverage        
        """

        yearly_spend_changes   = np.zeros(len(self.programs)) #relative to previous year
        ramping_changes = np.zeros(len(self.programs)) #relative to the current year if ramping was not in place
        
        orig_year_spend = np.zeros(len(self.programs))
        
        # ramped_year_spend = np.zeros(len(self.programs))

        for i, prog in self.programs.enumvals():
            orig_year_spend[i]    = sc.dcp(prog.annual_spend[year])
            yearly_spend_changes[i] = (prog.annual_spend[year] - prog.annual_spend[year-1])
            
            prog_change = False
            #actually enforce ramping
            if   prog.annual_restr_cov[year] - prog.annual_restr_cov[year-1] > prog.max_inc: #enforce not increasing coverage faster than max increment relative to previous year
                # print (f'Enforcing upper ramping limit for {self.name} in {year}, target={target_cov_year}, prev={self.annual_cov[year-1]}')
                prog.annual_restr_cov[year] = prog.annual_restr_cov[year-1] + prog.max_inc
                prog_change = True
            elif prog.annual_restr_cov[year-1] - prog.annual_restr_cov[year] > prog.max_dec: #enforce not decreasing coverage faster than max decrement relative to previous year
                # print (f'Enforcing lower ramping limit for {self.name} in {year}, target={target_cov_year}, prev={self.annual_cov[year-1]}')    
                prog.annual_restr_cov[year] = prog.annual_restr_cov[year-1] - prog.max_dec
                prog_change = True
            
            if prog_change:
                prog.annual_cov[year]       = prog.get_unrestr_cov(prog.annual_restr_cov)[year]
                prog.annual_spend[year]     = prog.get_spending(prog.annual_cov)[year]
            
                ramping_changes[i] = prog.annual_spend[year] - orig_year_spend[i]
            
            # ramped_year_spend[i] = sc.dcp(prog.annual_spend[year])
        
        total_ramping_spend_change = sum(ramping_changes)
        # print (f'Ramped spending changed {sum(orig_year_spend)} => {sum(ramped_year_spend)}, total change {total_ramping_spend_change}')
        
        if abs(total_ramping_spend_change) <1e-2: #within 1 cent
            return True #no further corrections needed
        
        if total_ramping_spend_change > 0: #too much money has been added due to ramping constraints - need to take some money from programs that increased spend relative to the previous year
            ramping_correction = np.array([max(ys, 0.) for ys in yearly_spend_changes])
        elif total_ramping_spend_change < 0: #too much money has been taken away due to ramping constraints - need to add some money to programs that decreased spend relative to the previous year
            ramping_correction = np.array([min(ys, 0.) for ys in yearly_spend_changes])

        #proportionally correct total spending based on how much spend was changed from the previous year
        ramping_correction = ramping_correction * total_ramping_spend_change / sum(ramping_correction)
        
        # new_year_spend = np.zeros(len(self.programs))
        #now change the spending, coverage, and restricted coverage based on this...
        for i, prog in self.programs.enumvals():
            if ramping_correction[i] != 0:
                prog.annual_spend[year]     = prog.annual_spend[year] - ramping_correction[i]
                prog.annual_cov[year]       = prog.func(prog.annual_spend)[year]
                prog.annual_restr_cov[year] = prog.annual_cov[year] * prog.unrestr_popsize / prog.restr_popsize
                
            # new_year_spend[i] = sc.dcp(prog.annual_spend[year])
        
        # print (f'Rebalanced spending changed {sum(orig_year_spend)} => {sum(new_year_spend)} after making a correction of {sum(ramping_correction)}')
        # assert abs(sum(orig_year_spend) - sum(new_year_spend)) <= 1e-2, f'Oh no, {orig_year_spend} -> {new_year_spend}'
        
        
        return True

    # def rebalance_fixed_spending(self, year, fixed_spending = None):
    #     """
    #     To be called if growth is fixed spending to ensure that spending remains exactly constant each year
        
    #     1. Check what the difference is between this year spending and the previous year spending
    #     2. check what programs are not constrained relative to the necessary increase/decrease
    #     3. get total spending on non-constrained progs
    #     4. scale as necessary to spend/cut extra difference
    #     5. adjust prog spending in this year directly
        
    #     :param year: year for comparison to be made
    #     :param fixed_spending: optional parameter to enforce a specific spending total, alternatively defaults to using the previous year's spend
    #     :return True if changes were made, False if changes were not.
    #     """
    #     spending_validated = True if year == 0 else False
        
    #     while not spending_validated:            
    #         prev_year_spend = np.zeros(len(self.programs))
    #         this_year_spend = np.zeros(len(self.programs))
    #         unconstrained_increase_progs = np.ones(len(self.programs))
    #         unconstrained_decrease_progs = np.ones(len(self.programs))
            
    #         for i, prog in self.programs.enumvals():
    #             prev_year_spend[i] += prog.annual_spend[year-1]
    #             this_year_spend[i] += prog.annual_spend[year]
                
    #             if prog.annual_cov[year] - prog.annual_cov[year-1] >= prog.max_inc:
    #                 unconstrained_increase_progs[i] = 0. #constrained above - can't have any extra budget assigned to it
    #             if prog.annual_cov[year-1] - prog.annual_cov[year] >= prog.max_dec:
    #                 unconstrained_decrease_progs[i] = 0. #constrained below - can't have any extra budget removed from it
            
    #         comparison_spend = fixed_spending if fixed_spending else sum(prev_year_spend)
    #         difference = sum(this_year_spend) - comparison_spend
    #         # print (f'Diff is {difference}')
            
    #         if abs(difference) < 0.01: #less than 1 cent difference we can accept
    #             spending_validated = True
    #         else:
    #             assert not np.isnan(difference).any(), 'Error: nan in spending.'
    #             if difference > 0: #we have too much spending, need to remove spending from existing programs
    #                 adjustable_budgets = this_year_spend * unconstrained_decrease_progs
    #             elif difference < 0: #we have too little spending, need to add spending to existing programs
    #                 adjustable_budgets = this_year_spend * unconstrained_increase_progs                   
                    
    #             if sum(adjustable_budgets) == 0:
    #                 adjustable_budgets = this_year_spend
    #                 print (f'Warning: Necessary to violate ramping constraints in year {year} in order to preserve fixed budget constraint.')
    #                 spending_validated = True #stop trying to improve on this
    #                 if sum(adjustable_budgets) == 0: #there's zero spending on anything - just divide any changes evenly
    #                     adjustable_budgets = np.ones(len(adjustable_budgets))
                    
                    
    #             adjustable_budgets = difference * adjustable_budgets / sum(adjustable_budgets) #difference applied as a proportion of unconstrained budget
                
    #             for i, prog in self.programs.enumvals():
    #                 if adjustable_budgets[i]:
    #                     prog.annual_spend[year] -= adjustable_budgets[i]
    #                     prog.annual_cov[year] = prog.func(prog.annual_spend)[year] #recalculate coverage also
    #                     prog.annual_restr_cov[year] = prog.annual_cov[year] * prog.unrestr_popsize / prog.restr_popsize
            
    #     return spending_validated
                    

    def adjust_covs(self, pops, year, growth, enforce_constraints_year=0):
        """
        Called every year to adjust the intended coverages/spendings based on population growth and ramping constraints
        Note: Initial intended coverages/spendings are set in the same program.annual_cov location, and set by initialize_covs
        
        :param growth: False, 'fixed budget', or 'fixed coverage' (either of the latter assume population growth generally occurs)
        :param enforce_constraints_year: may be turned on or off selectively by year for the model (e.g. to implement a coverage scenario outside of the ramping it would be turned off earlier)
            - enforces for a fixed budget scenario that the budget this year matches exactly the previous year
            - enforces ramping constraints that coverage can't have changed more than the limit from the previous year
        """
        for program in self.programs.values():
            program.adjust_cov(pops, year, growth)
        
        if year > enforce_constraints_year: 
            self.rebalance_ramped_coverage(year)
            
        #NOTE: possibly should have a call to restrict_covs here?  Might slow the model down a lot for very limited gain though.  
        
        #NOTE: commented this out, as it shouldn't be necessary after improving rebalance_ramped_coverage
        # if growth == 'fixed budget' and year > enforce_constraints_year: #need to make sure annual budget is exactly the same every year while respecting ramping constraints
        #     print ("rebalancing fixed budget...")
        #     self.rebalance_fixed_spending(year)
            
                    
    def update_prog_year(self, year):
        for prog in self.programs.values():
            prog.year = year
            
    def get_ann_covs(self, year):
        """ This function considers ramping constraints for the annual coverage
            This is called in model.py to compute population coverage probabilities"""
        #covs = {}
        covs = sc.odict()
        for prog in self.programs.values():
            if prog.annual_cov[prog.year] - prog.annual_cov[prog.year-1] > prog.max_inc:
                covs[prog.name] = prog.annual_cov[prog.year-1] + prog.max_inc
            elif prog.annual_cov[prog.year] - prog.annual_cov[prog.year-1] < (-1) * prog.max_dec:
                covs[prog.name] = prog.annual_cov[prog.year-1] - prog.max_dec
            else:
               covs[prog.name] = prog.annual_cov[prog.year]
        return covs   


    def restrict_covs(self):
        """
        Uses the ordering of both dependency lists to restrict the coverage of programs.
        Assumes that the coverage is given as peopleCovered/unrestr_popsize.
        Since the order of dependencies matters, was decided to apply threshold first then exclusion dependencies.
        Coverage will be restricted even in baseline year.
        """
        # threshold
        for child in self.thresholdOrder:
            for parname in child.thresh_deps:
                for year in self.all_years:
                    par = next(prog for prog in self.programs.values() if prog.name == parname)
                    # assuming uniform coverage across age bands, we can use the unrestricted coverage (NOT restricted)
                    maxcov_child = max(child.sat_unrestr - (par.sat_unrestr - par.annual_cov[year]), 0)
                    if child.annual_cov[year] > maxcov_child:
                        child.annual_cov[year] = maxcov_child
        # exclusion
        for child in self.exclusionOrder:
            for parname in child.excl_deps:
                for year in self.all_years:
                    par = next((prog for prog in self.programs.values() if prog.name == parname))
                    # assuming uniform coverage across age bands, we can use the unrestricted coverage (NOT restricted)
                    maxcov_child = max(child.sat_unrestr - par.annual_cov[year], 0) # if coverage of parent exceeds child sat
                    if child.annual_cov[year] > maxcov_child:
                        child.annual_cov[year] = maxcov_child

    def add_prog(self, prog, pops):
        '''
        Add a Program to ProgramInfo with a dict containing necessary information.
        :param prog: dict containing program name, scenario years and ProgData for the program to be added
        :param pops: model population info used to calculate coverages
        :return:
        '''
        new_prog = Program(prog['name'], prog['all_years'], prog['prog_data'])
        new_prog.set_pop_sizes(pops)
        new_prog.set_costcov()
        self.programs[prog['name']] = new_prog
        np.append(self.refs, 0.0)
        np.append(self.curr, 0.0)
        return
