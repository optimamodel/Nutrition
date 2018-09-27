import sciris as sc
from optimization import Optim
import numpy as np
from scipy.interpolate import pchip
import utils

class Geospatial:
    def __init__(self, name=None, model_names=None, region_names=None, weights=None, mults=None, prog_set=None,
                 add_funds=0, fix_curr=False, fix_regionalspend=False, filter_progs=True, active=True):
        """
        :param name: name of the optimization (string)
        :param region_names: names of the regions to be included (list of strings)
        :param model_names: names of the models (datasets) that each region corresponds to (list of strings). Order must match that of region_names.
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
        self.model_names = model_names
        self.regionnames = region_names
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

    def make_regions(self, add_funds=None, mults=None):
        """ Create all the Optim objects requested """
        if add_funds is None: add_funds = self.add_funds
        if mults is None: mults = self.mults
        if isinstance(add_funds, float) or isinstance(add_funds, int):
            add_funds = [add_funds] * len(self.regionnames)
        regions = []
        for i, name in enumerate(self.regionnames):
            model_name = self.model_names[i]
            regionalfunds = add_funds[i]
            region = Optim(name=name, model_name=model_name, weights=self.weights, mults=mults,
                           prog_set=self.prog_set, active=self.active, add_funds=regionalfunds,
                           filter_progs=self.filter_progs, fix_curr=self.fix_curr)
            regions.append(region)
        self.regions = regions
        return regions

    def get_bocs(self, optimized, optim_curr):
        """ Genereates the budget outcome curves for each region
         :param optimized: a list of Optim objects (list of lists) """
        national = self.get_totalfreefunds(optim_curr)
        for name, results in optimized.iteritems():
            spending = np.zeros(len(results))
            output = np.zeros(len(results))
            for i, res in enumerate(results):
                outs = res.model.get_output()
                val = np.inner(outs, self.weights)
                spending[i] = national * res.mult
                output[i] = val
            self.bocs[name] = pchip(spending, output, extrapolate=False)
        return

    def get_icer(self, regions):
        numpoints = 10000
        icervecs = []
        spendingvec = []
        nationalspend = self.get_totalfreefunds(regions)
        for name, region in zip(self.regionnames, regions):
            minspend = 0
            maxspend = nationalspend
            boc = self.bocs[name]
            spend = np.linspace(minspend, maxspend, numpoints)
            deriv = boc.derivative(nu=1)
            icer = deriv(spend) # reflect curve across x-axis
            spendingvec.append(spend)
            icervecs.append(icer)
        return spendingvec, icervecs

    def gridsearch(self, optimized):
        # extract each result that has multiple 1
        regions = [region for sublist in optimized.itervalues() for region in sublist if region.mult == 1]
        self.get_bocs(optimized, regions)
        spendvecs, icervecs = self.get_icer(regions)
        totalfunds = self.get_totalfreefunds(regions, restrict=self.fix_regionalspend)
        remainfunds = totalfunds
        regional_allocs = np.zeros(len(regions))
        percentspend = 0
        maxiters = int(1e6)

        for i in range(maxiters):
            besteff = np.inf
            bestregion = None
            for regionidx in range(len(regions)):
                # find most effective spending in each region
                icer = icervecs[regionidx]
                if len(icer):
                    maxidx = np.nanargmin(icer)
                    maxeff = icer[maxidx]
                    if maxeff < besteff:
                        besteff = maxeff
                        besteffidx = maxidx
                        bestregion = regionidx
            # once he most cost-effective spending is found, adjust all spending
            # and outcome vectors, available funds and regional allocation
            if bestregion is not None:
                fundsspent = spendvecs[bestregion][besteffidx]
                remainfunds -= fundsspent
                spendvecs[bestregion] -= fundsspent
                regional_allocs[bestregion] += fundsspent
                # remove funds & derivatives at or below zero
                spendvecs[bestregion] = spendvecs[bestregion][besteffidx + 1:]
                icervecs[bestregion] = icervecs[bestregion][besteffidx + 1:]
                # ensure regional spending doesn't exceed remaining funds
                for regionidx in range(len(regions)):
                    withinbudget = np.nonzero(spendvecs[regionidx] <= remainfunds)[0]
                    spendvecs[regionidx] = spendvecs[regionidx][withinbudget]
                    icervecs[regionidx] = icervecs[regionidx][withinbudget]
                newpercent = (totalfunds - remainfunds) / totalfunds * 100
                if not (i % 100) or (newpercent - percentspend) > 1:
                    percentspend = newpercent
            else:
                break # nothing more to allocate

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
