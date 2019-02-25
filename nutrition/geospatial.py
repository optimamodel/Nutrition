import numpy as np
import sciris as sc
from functools import partial
from scipy.interpolate import pchip
from .optimization import Optim
from . import utils


class Geospatial:
    def __init__(self, name=None, modelnames=None, weights=None, mults=None, prog_set=None,
                 add_funds=0, fix_curr=False, fix_regionalspend=False, filter_progs=True, active=True):
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
        It follows that if fix_curr is True, fix_regionalspend must also be true.
        """
        self.name = name
        self.modelnames = modelnames
        self.regions = None
        self.weights = utils.process_weights(weights)
        if mults is not None:
            print("Warning: changing budget multiples, not recommended")
            self.mults = mults
        else:
            self.mults = [0, 0.01, 0.025, 0.04, 0.05, 0.075, 0.1, 0.2, 0.3, 0.6, 1]
        self.prog_set = prog_set
        self.add_funds = add_funds
        self.fix_curr = fix_curr
        self.fix_regionalspend = fix_curr if fix_curr else fix_regionalspend
        self.filter_progs = filter_progs
        self.active = active
        self.bocs = sc.odict()

    def run_geo(self, proj, maxiter, swarmsize, maxtime, parallel):
        """ Runs geospatial optimization for a given project via the following steps:
            - Calculates the total flexible spending available for distribution across regions.
            Total flexible spending is a function of additional funds, `fix_curr` and `fix_regionalspend`.
            - generate budget outcome curves and run gridsearch to distribute these flexible funds.
            - once funding is distributed between regions, optimize this within the regions"""
        # Create regions in order to calculate total flexible funds.
        regions = self.make_regions(add_funds=0)

        # Barf if we have less than 2 regions to analyze.
        if len(regions) < 2:
            raise Exception('Less than 2 regions selected for geospatial analysis.')

        # Set up models for each of the regions.
        models = []
        for reg in regions:
            thismod = sc.dcp(proj.model(reg.model_name))
            thismod.setup(reg, setcovs=False)
            thismod.get_allocs(reg.add_funds, reg.fix_curr, reg.rem_curr)
            models.append(thismod)

        # Current regional spending only included in flexible funding if regional spending not fixed.
        regional_flexi = np.array([mod.prog_info.free for mod in models]) * int(not self.fix_regionalspend)

        # Total funds = sum of all free-to-change programs + additional funds to be added.
        totalfunds = sum(regional_flexi) + self.add_funds

        # Calculate the funds that could come into each region from all of the other regions and the additional funds.
        total_flexi = [totalfunds - x for x in regional_flexi]

        # If there are funds that need distribution between regions...
        if totalfunds > 0:
            # Create regions with corrected additional funds.
            regions = self.make_regions(add_funds=total_flexi)

            # Define the run_optim func.
            run_optim = partial(proj.run_optim, key=-1, maxiter=maxiter, swarmsize=swarmsize, maxtime=maxtime,
                                parallel=parallel, dosave=True, runbaseline=False)

            # Generate the budget outcome curves optimization results.  This step takes a long while, generally.
            import os.path
            if os.path.exists('bocs.obj'):
                print('Loading BOCS from bocs.obj...')
                boc_optims = sc.loadobj('bocs.obj')
            else:
                print('Creating BOCs afresh...')
                boc_optims = sc.odict([(region.name, run_optim(optim=region)) for region in regions])
                sc.saveobj('bocs.obj', boc_optims)

            # Get the actual BOCs (storing them in the self.bocs odict of pchip-generated objects).
            self.get_bocs(boc_optims, totalfunds)

            # Use a grid search to calculate the regional allocations from the BOCs.
            regional_allocs = self.gridsearch(boc_optims, totalfunds=totalfunds)

        # Else, if we have no funds to distribute between regions, but can redistribute within the regions...
        elif (totalfunds == 0) and (self.fix_curr is False):
            print('Warning: No funds to distribute between regions.')
            regional_allocs = [0] * len(self.modelnames)  # allocate 0 additional funds to each region for final optimization

        # Else, we shouldn't be trying to optimize anything because nothing can be distributed.
        else:
            raise Exception('No funds to distribute between or within regions.')

        # Optimize the new allocations within each region.
        regions = self.make_regions(add_funds=regional_allocs, rem_curr=not self.fix_regionalspend, mults=[1])
        run_optim = partial(proj.run_optim, key=-1, maxiter=maxiter, swarmsize=swarmsize, maxtime=maxtime,
                            parallel=False, dosave=True, runbaseline=False)

        # Run results in parallel or series.
        # can run in parallel b/c child processes in series
        if parallel:
            results = utils.run_parallel(run_optim, regions, num_procs=len(regions))
        else:
            results = [run_optim(region) for region in regions]

        # Flatten list.
        results = [item for sublist in results for item in sublist]

        # Remove multiple to plot by name (total hack)
        for res in results:
            res.mult = None
            res.name = res.name.replace('(x1)', '')
        return results

    def make_regions(self, add_funds=None, rem_curr=False, mults=None):
        """ Create all the Optim objects requested """
        if add_funds is None:
            add_funds = self.add_funds
        if mults is None:
            mults = self.mults
        if isinstance(add_funds, float) or isinstance(add_funds, int):
            add_funds = [add_funds] * len(self.modelnames)
        regions = []
        for i, name in enumerate(self.modelnames):
            modelname = self.modelnames[i]
            regionalfunds = add_funds[i]
            region = Optim(name=name, model_name=modelname, weights=self.weights, mults=mults,
                           prog_set=self.prog_set, active=self.active, add_funds=regionalfunds,
                           filter_progs=self.filter_progs, fix_curr=self.fix_curr, rem_curr=rem_curr)
            regions.append(region)
        self.regions = regions
        return regions

    def get_bocs(self, boc_optims, totalfunds):
        """ Genereates the budget outcome curves for each region
         :param optimized: a list of Optim objects (list of lists) """
        for name, results in boc_optims.items():
            spending = np.zeros(len(results))
            output = np.zeros(len(results))
            for i, res in enumerate(results):
                outs = res.model.get_output()
                val = np.inner(outs, self.weights)
                spending[i] = totalfunds * res.mult
                output[i] = val
            self.bocs[name] = pchip(spending, output, extrapolate=False)
        return

    # TODO: This can probably go bye-bye.
    def get_icer(self, regions, totalfunds):
        numpoints = 10000
        icervecs = []
        spendingvec = []
        for name, region in zip(self.modelnames, regions):
            minspend = 0
            maxspend = totalfunds
            boc = self.bocs[name]
            spend = np.linspace(minspend, maxspend, numpoints)
            deriv = boc.derivative(nu=1)
            icer = deriv(spend) # reflect curve across x-axis
            spendingvec.append(spend)
            icervecs.append(icer)
        return spendingvec, icervecs

    def gridsearch(self, boc_optims, totalfunds):
        # Make budget increments to be tried at each iteration of the algorithm.
        # numpoints = 10000
        numpoints = 2000
        # tmpx1 = np.linspace(1, np.log(totalfunds), numpoints)  # Logarithmically distributed
        # tmpx2 = np.log(np.linspace(1, totalfunds, numpoints))  # Uniformly distributed
        # tmpx3 = (tmpx1 + tmpx2) / 2.0  # Halfway in between, logarithmically speaking
        # budget_increments = np.exp(tmpx3)  # Convert from log-space to normal space
        budget_increments = np.linspace(0, totalfunds, numpoints)
        budget_increments = budget_increments[1:]

        print('BUDGET INCREMENTS:')
        print(budget_increments)

        # Initialize the region budget allocations to all zeros.
        numregions = len(boc_optims.keys())
        regional_allocs = np.zeros(numregions)
        total_budget_allocated = 0.0

        print('INITIAL BUDGET ALLOCATIONS:')
        print(regional_allocs)

        # Loop over a number of budget increment tries...
        maxiters = int(1e6)
        for i in range(maxiters):
            # Only take a step if we still have budget increment steps to take.
            if len(budget_increments) > 0:
                # Initialize the marginal improvements array.
                marginal_improvements = np.zeros((numregions, len(budget_increments)))

                # Loop over regions...
                for reg_ind in range(numregions):
                    # Get the present outcome value from the BOC (given the current budget allocated to the region).
                    current_outcome = self.bocs[reg_ind](regional_allocs[reg_ind])

                    # Loop over the budget increments...
                    for budget_inc_ind in range(len(budget_increments)):
                        # Get the new outcome from the BOC, assuming the particular budget increment is chosen.
                        new_outcome = self.bocs[reg_ind](regional_allocs[reg_ind] + budget_increments[budget_inc_ind])

                        # Calculate the marginal improvement for this budget increment and region.
                        marginal_improvements[reg_ind][budget_inc_ind] = (current_outcome - new_outcome) / budget_increments[budget_inc_ind]

                # Find the combination of region and budget increment.
                (best_reg_ind, best_budget_inc_ind) = np.unravel_index(np.argmax(marginal_improvements), marginal_improvements.shape)

                print('MARGINAL IMPROVEMENTS:')
                print(marginal_improvements)
                print('Best region %d' % best_reg_ind)
                print('Best budget inc %f' % budget_increments[best_budget_inc_ind])

                # Allocate the money to the chosen best region and add to the total budget allocated.
                regional_allocs[best_reg_ind] += budget_increments[best_budget_inc_ind]
                total_budget_allocated += budget_increments[best_budget_inc_ind]

                print('BUDGET ALLOCATIONS:')
                print(regional_allocs)

                # Chop out any budget increments that now run us over the budget total.
                budget_increments = budget_increments[(budget_increments + total_budget_allocated - totalfunds) <= 0]

                print('NEW BUDGET INCREMENTS:')
                print(budget_increments)

                print('Allocated so far: %f of %f' % (total_budget_allocated, totalfunds))

        print('FINAL BUDGET ALLOCATIONS:')
        print(regional_allocs)

        # Old shtuff.

        # # extract each result that has multiple 1
        # regions = [region for sublist in boc_optims.values() for region in sublist if region.mult == 1]
        # spendvecs, icervecs = self.get_icer(regions, totalfunds)
        # remainfunds = totalfunds
        # regional_allocs = np.zeros(len(regions))
        # percentspend = 0
        # maxiters = int(1e6)
        #
        # for i in range(maxiters):
        #     besteff = np.inf
        #     bestregion = None
        #     for regionidx in range(len(regions)):
        #         # find most effective spending in each region
        #         icer = icervecs[regionidx]
        #         if len(icer):
        #             maxidx = np.nanargmin(icer)
        #             maxeff = icer[maxidx]
        #             if maxeff < besteff:
        #                 besteff = maxeff
        #                 besteffidx = maxidx
        #                 bestregion = regionidx
        #     # once he most cost-effective spending is found, adjust all spending
        #     # and outcome vectors, available funds and regional allocation
        #     if bestregion is not None:
        #         fundsspent = spendvecs[bestregion][besteffidx]
        #         remainfunds -= fundsspent
        #         spendvecs[bestregion] -= fundsspent
        #         regional_allocs[bestregion] += fundsspent
        #         # remove funds & derivatives at or below zero
        #         spendvecs[bestregion] = spendvecs[bestregion][besteffidx + 1:]
        #         icervecs[bestregion] = icervecs[bestregion][besteffidx + 1:]
        #         # ensure regional spending doesn't exceed remaining funds
        #         for regionidx in range(len(regions)):
        #             withinbudget = np.nonzero(spendvecs[regionidx] <= remainfunds)[0]
        #             spendvecs[regionidx] = spendvecs[regionidx][withinbudget]
        #             icervecs[regionidx] = icervecs[regionidx][withinbudget]
        #         newpercent = (totalfunds - remainfunds) / totalfunds * 100
        #         if not (i % 100) or (newpercent - percentspend) > 1:
        #             percentspend = newpercent
        #     else:
        #         break # nothing more to allocate

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


def make_default_geo(basename='Geospatial optimization'):
    """
    Creates and returns a prototype / default geospatial optimization.
    """

    kwargs1 = {'name': basename,
               'modelnames': [None],
               'weights': 'thrive',
               'fix_curr': False,
               'fix_regionalspend': False,
               'add_funds': 0,
               'prog_set': ['IFA fortification of maize', 'IYCF 1', 'Lipid-based nutrition supplements',
                            'Multiple micronutrient supplementation', 'Micronutrient powders', 'Kangaroo mother care',
                            'Public provision of complementary foods', 'Treatment of SAM', 'Vitamin A supplementation',
                            'Mg for eclampsia', 'Zinc for treatment + ORS', 'Iron and iodine fortification of salt']}

    default = Geospatial(**kwargs1)
    return default
