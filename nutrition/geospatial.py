import numpy as np
import matplotlib.pyplot as plt
import sciris as sc
from functools import partial
from scipy.interpolate import pchip
from .optimization import Optim
from . import utils


class Geospatial:
    def __init__(self, name=None, modelnames=None, weights=None, mults=None, prog_set=None, add_funds=0, fix_curr=False, fix_regionalspend=False, filter_progs=True, active=True, growth="fixed budget", balanced_optimization=False, locale=None):
        """
        :param name: name of the optimization (string)
        :param modelnames: names of the models (datasets) that each region corresponds to (list of strings). Order must match that of region_names.
        :param weights: weights defining an objective function (odict). See documentation in optimization.Optim()
        :param mults: the multiples of flexible funding to be optimized. These are multiples within the interval (min_freefunds, max_freefunds).
         Default values recommended.
        :param prog_set: the progr
        :param add_funds: additional funds to be distributed across all regions (positive float/integer)
        :param fix_curr: fix the current regional program allocations (boolean), as in optimization.Optim(fix_curr).
        :param fix_regionalspend: fix the current total regional spending (boolean), but not at current allocations.
        :param locale: Locale to match the weights being passed in

        It follows that if fix_curr is True, fix_regionalspend must also be true.
        """
        self.name = name
        self.modelnames = modelnames
        self.regions = None
        self.input_weights = weights  # retain input weights to pass to Optim
        proc_weights = utils.process_weights(weights, locale=locale)
        self.weights = np.transpose(proc_weights)

        if mults is not None:
            print("Warning: changing budget multiples, not recommended")
            self.mults = mults
        else:
            self.mults = [0, 0.01, 0.025, 0.04, 0.05, 0.075, 0.1, 0.2, 0.3, 0.6, 1]
            # self.mults = [0, 0.01, 0.025, 0.04, 0.05, 0.075]
        self.prog_set = prog_set
        self.add_funds = add_funds
        self.fix_curr = fix_curr
        self.fix_regionalspend = fix_curr if fix_curr else fix_regionalspend
        self.filter_progs = filter_progs
        self.bocs = sc.odict()
        self.growth = growth
        self.balanced_optimization = balanced_optimization

    def run_geo(self, proj, maxiter, swarmsize, maxtime, parallel, runbalanced=False, n_samples=0):
        """Runs geospatial optimization for a given project via the following steps:
        - Calculates the total flexible spending available for distribution across regions.
        Total flexible spending is a function of additional funds, `fix_curr` and `fix_regionalspend`.
        - generate budget outcome curves and run gridsearch to distribute these flexible funds.
        - once funding is distributed between regions, optimize this within the regions"""
        _ = utils.get_translator(proj.locale)

        results = []
        for w, weight in enumerate(self.weights):
            # create regions in order to calculate total flexible funds
            regions = self.make_regions(add_funds=0, weight_ind=w)
            if len(regions) < 2:
                raise Exception(_("Less than 2 regions selected for geospatial analysis."))
            models = []
            for reg in regions:
                thismod = sc.dcp(proj.model(reg.model_name))
                thismod.setup(reg, setcovs=False)
                thismod.get_allocs(reg.add_funds, reg.fix_curr, reg.rem_curr)
                models.append(thismod)
            # current regional spending only included in flexible funding if regional spending not fixed
            regional_flexi = np.array([mod.prog_info.free for mod in models]) * int(not self.fix_regionalspend)
            totalfunds = sum(regional_flexi) + self.add_funds
            # adjust for region adding in current expenditure again
            total_flexi = [totalfunds - x for x in regional_flexi]
            if totalfunds > 0:
                # can distribute between regions
                # create regions with corrected additional funds
                regions = self.make_regions(add_funds=total_flexi, weight_ind=w)
                # NOTE: n_runs = 1 here always - we don't want sampling for determining the cost-curve
                run_optim = partial(proj.run_optim, key=-1, maxiter=maxiter, swarmsize=swarmsize, maxtime=maxtime, parallel=parallel, dosave=True, runbaseline=False, n_samples=0)
                # Generate the budget outcome curves optimization results.  This step takes a long while, generally.
                print("Creating BOCs afresh...")
                boc_optims = sc.odict([(region.name + "objective #" + str(w + 1), run_optim(optim=region)[0]) for region in regions])

                # Get the actual BOCs (storing them in the self.bocs odict of pchip-generated objects).
                self.get_bocs(boc_optims, totalfunds, weight)

                # Use a grid search to calculate the regional allocations from the BOCs.
                regional_allocs = self.gridsearch(boc_optims, totalfunds=totalfunds)

            # Else, if we have no funds to distribute between regions, but can redistribute within the regions...
            elif (totalfunds == 0) and (self.fix_curr is False):
                print("Warning: No funds to distribute between regions.")
                regional_allocs = [0] * len(self.modelnames)  # allocate 0 additional funds to each region for final optimization
            # Else, we shouldn't be trying to optimize anything because nothing can be distributed.
            else:
                raise Exception(_("No funds to distribute between or within regions."))

                # Optimize the new allocations within each region.
            regions = self.make_regions(add_funds=regional_allocs, rem_curr=not self.fix_regionalspend, mults=[1], weight_ind=w)
            run_optim = partial(proj.run_optim, key=-1, maxiter=1, swarmsize=swarmsize, maxtime=1, parallel=False, dosave=True, runbaseline=True, runbalanced=runbalanced, n_samples=n_samples)

            # Run results in parallel or series.
            # can run in parallel b/c child processes in series
            if parallel:
                results += utils.run_parallel(run_optim[0], regions, num_procs=len(regions))
            else:
                for region in regions:
                    results.append(run_optim(region)[0])

        # Flatten list.
        results = [item for sublist in results for item in sublist]
        # remove multiple to plot by name (total hack)
        excess_budget = 0
        track_names = []
        track_del_ind = []
        for r, res in enumerate(results):
            _ = utils.get_translator(res.locale)

            res.mult = None
            if res.name == _("Baseline"):
                if res.model_name + ": " + _("Baseline") in track_names:
                    track_del_ind.append(r)
                res.name = res.model_name + ": " + _("Baseline")
                track_names.append(res.name)
            else:
                res.name = res.model_name + ": " + res.name
            if _("Excess budget not allocated") in res.prog_info.programs and _("Baseline") not in res.name:
                excess_budget += res.prog_info.programs[_("Excess budget not allocated")].annual_spend[-1]
                res.prog_info.programs[_("Excess budget not allocated")].annual_spend = np.zeros(len(res.years))

        if track_del_ind:
            for index in sorted(track_del_ind, reverse=True):
                del results[index]

        if excess_budget > 0:
            excess_res = sc.dcp(results[0])
            excess_res.name = _("Excess budget")
            excess_prog = sc.dcp(excess_res.programs[_("Excess budget not allocated")])
            excess_prog.annual_spend[1:] += excess_budget
            excess_res.prog_info.programs = {_("Excess budget not allocated"): excess_prog}
            excess_res.programs = excess_res.prog_info.programs
            results.append(excess_res)
        return results

    def make_regions(self, add_funds=None, rem_curr=False, mults=None, weight_ind=None):
        """ Create all the Optim objects requested """
        if add_funds is None:
            add_funds = self.add_funds
        if mults is None:
            mults = self.mults
        if isinstance(add_funds, float) or isinstance(add_funds, int):
            add_funds = [add_funds] * len(self.modelnames)
        if weight_ind is not None:
            obj_weights = sc.odict((key, [val[weight_ind]]) for key, val in self.input_weights.items())
        else:
            obj_weights = self.input_weights
        regions = []
        for i, name in enumerate(self.modelnames):
            modelname = self.modelnames[i]
            regionalfunds = add_funds[i]
            region = Optim(name=name, model_name=modelname, weights=obj_weights, mults=mults, prog_set=self.prog_set, active=self.active, add_funds=regionalfunds, filter_progs=self.filter_progs, fix_curr=self.fix_curr, rem_curr=rem_curr, growth=self.growth, balanced_optimization=self.balanced_optimization)
            regions.append(region)
        self.regions = regions
        return regions

    def get_bocs(self, boc_optims, totalfunds, weight):
        """Genereates the budget outcome curves for each region
        :param optimized: a list of Optim objects (list of lists)"""
        for name, results in boc_optims.items():
            spending = np.zeros(len(results))
            output = np.zeros(len(results))
            for i, res in enumerate(results):
                outs = res.model.get_output()
                val = np.inner(outs, weight)
                spending[i] = totalfunds * res.mult
                output[i] = val
            self.bocs[name] = pchip(spending, output, extrapolate=False)
        return

    def gridsearch(self, boc_optims, totalfunds):
        import matplotlib.pyplot as plt

        # Initialize the region budget allocations to all zeros.
        numregions = len(boc_optims.keys())
        regional_allocs = np.zeros(numregions)
        total_budget_allocated = 0.0
        tol = 0.00001
        # Make budget increments to be tried at each iteration of the algorithm.
        numpoints = 1000
        # numpoints = 2000
        tmpx1 = np.linspace(1, np.log(totalfunds), numpoints)  # Logarithmically distributed
        tmpx2 = np.log(np.linspace(1, totalfunds, numpoints))  # Uniformly distributed
        tmpx3 = (tmpx1 + tmpx2) / 2.0  # Halfway in between, logarithmically speaking
        base_trial_budgets = np.exp(tmpx3)  # Convert from log-space to normal space
        # Initialise trial budgets for all regions
        trial_budgets = np.zeros((numregions, base_trial_budgets.size))
        for reg_ind in list(range(numregions)):
            trial_budgets[reg_ind] = base_trial_budgets
        """
        print('TRIAL BUDGETS:')
        for reg_ind in list(range(numregions)):
            print('Region %d' % reg_ind)
            print(trial_budgets[reg_ind])

        print('INITIAL BUDGET ALLOCATIONS:')
        print(regional_allocs)
        """
        # Loop over a number of budget increment tries...
        maxiters = int(1e6)
        for i in range(maxiters):
            # Only take a step if we still have budget increment steps to take.
            valid_increments_count = 0.0
            for reg_ind in list(range(numregions)):
                valid_increments_count += len(trial_budgets[reg_ind])
            if valid_increments_count > 0:
                # Initialize the marginal improvements arrays.
                budget_increments = []
                marginal_improvements = []
                for reg_ind in list(range(numregions)):
                    budget_increments.append(np.zeros(len(trial_budgets[reg_ind])))
                # Initialise budget increments
                # Loop over regions...
                shift_ind = np.zeros(numregions)
                for reg_ind in list(range(numregions)):
                    # Get the present outcome value from the BOC (given the current budget allocated to the region).
                    reg_key = boc_optims.keys()[reg_ind]
                    current_outcome = self.bocs[reg_key](regional_allocs[reg_ind])
                    # Calculate budget increments
                    budget_increments[reg_ind] = trial_budgets[reg_ind] - regional_allocs[reg_ind]
                    # Find number of budget increments <= 0
                    shift_ind[reg_ind] = budget_increments[reg_ind].size - len(budget_increments[reg_ind][budget_increments[reg_ind] >= tol])
                    if shift_ind[reg_ind] > 0:  # Remove any budget increments <= 0
                        budget_increments[reg_ind] = budget_increments[reg_ind][int(shift_ind[reg_ind]) :]
                    # Find number of budget increments greater than the remaining budget
                    shift_ind[reg_ind] = budget_increments[reg_ind].size - len(budget_increments[reg_ind][budget_increments[reg_ind] - totalfunds + total_budget_allocated <= tol])
                    if shift_ind[reg_ind] > 0:  # Remove budget increments which are too big
                        budget_increments[reg_ind] = budget_increments[reg_ind][0 : budget_increments[reg_ind].size - int(shift_ind[reg_ind])]
                    marginal_improvements.append(np.zeros(len(budget_increments[reg_ind])))
                    # Loop over the budget increments...
                    for budget_inc_ind in list(range(len(budget_increments[reg_ind]))):
                        # Get the new outcome from the BOC, assuming the particular budget increment is chosen.
                        new_outcome = self.bocs[reg_key](regional_allocs[reg_ind] + budget_increments[reg_ind][budget_inc_ind])

                        # Calculate the marginal improvement for this budget increment and region.
                        marginal_improvements[reg_ind][budget_inc_ind] = (current_outcome - new_outcome) / budget_increments[reg_ind][budget_inc_ind]
                # Check if there were any marginal improvements calculated
                if sum(np.count_nonzero(marginal_improvements[k]) for k in list(range(numregions))) == 0:
                    break
                else:
                    check = []
                    val = []
                    for reg_ind in list(range(numregions)):
                        # Check if marginal improvements were calculated in each region
                        if not marginal_improvements[reg_ind].any():
                            check.append(np.nan)
                            val.append(np.nan)
                        else:  # If yes then find the last occurrence of the maximum value
                            # check.append(np.argwhere(marginal_improvements[reg_ind] == marginal_improvements[reg_ind][np.nanargmax(marginal_improvements[reg_ind])]).flatten().tolist()[-1])
                            check.append(np.nanargmax(marginal_improvements[reg_ind]).flatten().tolist()[-1])
                            val.append(marginal_improvements[reg_ind][check[-1]])
                    # Find best region and funding amount
                    # best_reg_ind = np.argwhere(val == val[np.nanargmax(val)]).flatten().tolist() # Find all maximum value indices
                    best_reg_ind = np.nanargmax(val).flatten().tolist()
                    best_budget_inc_ind = []
                    for num_ind in best_reg_ind:
                        best_budget_inc_ind.append(check[num_ind])
                    # Check if there are multiple best regions
                    if len(best_reg_ind) == 1:
                        # Allocate the money to the chosen best region and add to the total budget allocated.
                        regional_allocs[best_reg_ind[0]] += budget_increments[best_reg_ind[0]][best_budget_inc_ind[0]]
                        total_budget_allocated += budget_increments[best_reg_ind[0]][best_budget_inc_ind[0]]
                    else:
                        options = []
                        for choice in list(range(len(best_reg_ind))):
                            options.append(regional_allocs[best_reg_ind[choice]])
                        choose = np.argwhere(options == options[np.nanargmin(options)]).flatten().tolist()
                        if len(choose) > 1:
                            import random

                            best_choice = random.choice(choose)
                        elif len(choose) == 1:
                            best_choice = choose[0]
                        else:
                            print("There are no regional allocations")
                        regional_allocs[best_reg_ind[best_choice]] += budget_increments[best_reg_ind[best_choice]][best_budget_inc_ind[best_choice]]
                        total_budget_allocated += budget_increments[best_reg_ind[best_choice]][best_budget_inc_ind[best_choice]]
            else:
                break

        print("FINAL BUDGET ALLOCATIONS:")
        print(regional_allocs)

        # scale to ensure correct budget
        scaledallocs = utils.scale_alloc(totalfunds, regional_allocs)
        return scaledallocs

    def get_totalfreefunds(self, regions, restrict=False):
        if restrict:
            return self.add_funds
        else:
            return sum([region.get_freefunds() - self.add_funds for region in regions]) + self.add_funds

    def get_nationalspend(self, regions):
        """ allocation return as time series, ensure only extract current spending"""
        return sum([sum(region.get_currspend()) for region in regions])


def make_default_geo(basename="Geospatial optimization", locale=None):
    """
    Creates and returns a prototype / default geospatial optimization.
    """

    _ = utils.get_translator(locale)

    kwargs1 = {
        "name": basename,
        "modelnames": [None],
        "weights": "thrive",
        "fix_curr": False,
        "fix_regionalspend": False,
        "add_funds": 0,
        "prog_set": [
            _("IFA fortification of maize"),
            _("IYCF 1"),
            _("Lipid-based nutrition supplements"),
            _("Multiple micronutrient supplementation"),
            _("Micronutrient powders"),
            _("Kangaroo mother care"),
            _("Public provision of complementary foods"),
            _("Treatment of SAM"),
            _("Vitamin A supplementation"),
            _("Mg for eclampsia"),
            _("Zinc for treatment + ORS"),
            _("Iron and iodine fortification of salt"),
        ],
    }

    default = Geospatial(**kwargs1, locale=locale)
    return default
