import numpy as np
import multiprocessing
import sciris as sc
from . import pso, utils
from .scenarios import Scen, run_scen
from .migration import migrate
from .utils import get_translator, translate


class Optim(sc.prettyobj):
    """ Stores settings for running an optimization for a single objective. """

    def __init__(self, name=None, model_name=None, weights=None, mults=None, prog_set=None, active=True, add_funds=0, fix_curr=False, rem_curr=False, growth="fixed budget", filter_progs=True, balanced_optimization=False, locale=None, uid=None):
        """
        :param name: the name of the optimization (string)
        :param model_name: the name of the model corresponding to optimizations (string)
        :param weights: an odict of (outcome, weight) pairs
        :param mults: multiples of free funds
        :param prog_set: the programs to include in optimization (list of strings)
        :param active: whether to run in project class (boolean)
        :param add_funds: additional funds
        :param fix_curr: fix the current allocations?
        :param rem_curr: remove the current allocations?
        :param locale: Locale to match the weights being passed in
        :param filter_progs: filter out programs which don't impact the objective (can improve optimization results)
        :param growth: consider it is fixed budget ot fixed coverage (boolean)
        :param balanced_optimization: optionally run an additional set of optimizations for each budget multiplier that balances progress toward each objective
        """

        self.name = name
        self.uid = uid or sc.uuid()
        self.model_name = model_name
        proc_weights = utils.process_weights(weights, locale=locale)
        self.weights = np.transpose(proc_weights)
        self.mults = mults
        self.prog_set = prog_set
        self.add_funds = add_funds
        self.fix_curr = fix_curr
        self.rem_curr = rem_curr if not fix_curr else False  # can't remove if fixed
        self.filter_progs = filter_progs
        self.num_cpus = multiprocessing.cpu_count()
        self.num_procs = None
        self.optim_allocs = sc.odict()
        self.growth = growth
        self.balanced_optimization = balanced_optimization

    ######### SETUP ############

    def get_kwargs(self, model, weights, mult, keep_inds):
        model = sc.dcp(model)
        model.growth = self.growth
        free = model.prog_info.free
        fixed = model.prog_info.fixed
        kwargs = {"model": model, "free": free * mult, "fixed": fixed, "weights": weights, "keep_inds": keep_inds}
        if free == 0:
            raise Exception("There are no funds available to optimize.")
        return kwargs

    ######### OPTIMIZATION ##########
    @translate
    def run_optim(self, model, maxiter=1, swarmsize=None, maxtime=200, parallel=True, num_procs=None, runbalanced=False, base=None):
        if parallel:
            how = "parallel"
            num_procs = num_procs if num_procs else self.num_cpus
        else:
            how = "series"
            num_procs = 1
        print("Optimizing for %s in %s" % (self.name, how))
        # get impactful programs
        keep_inds = self._filter_progs(model)
        # get the kwargs
        optim = (maxiter, swarmsize, maxtime)
        args = [(self.get_kwargs(model, weight, mult, keep_inds), mult) + optim for mult in self.mults for weight in list(self.weights)]
        if parallel:
            res, scen = utils.run_parallel(self.one_optim_parallel, args, num_procs, return_two=True)
        else:
            res, scen = [], []
            for arg in args:
                this_res, this_scen = self.one_optim(arg)
                res.append(this_res)
                scen.append(this_scen)

        """The goal of this is to balance progress toward multiple competing objectives, e.g.
        weight[0] = 100% Maximize thrive,  the objective progress (baseline evaluation - optimized evaluation) of the optimized result is 100
        weight[1] = 100% Minimize prevalence of MAM,  the objective progress (baseline evaluation - optimized evaluation) of the optimized result is 0.2
        Rebalancing these would give an objective function of:
            [1/100 maximize thrive, 1/0.2 minimize prevalence of MAM] = [0.01, 5] and final results would approximately balance the most effective interventions for each objective
        If multiple weightings include the same objective the results would be slightly leaning toward that objective, but this seems reasonably as intended    
        """
        if runbalanced and len(self.weights) > 1:
            balanced_args = []
            res_labels = [result.name for result in res]

            balanced_args = []
            for mult in self.mults:
                relative_progress = dict()
                balanced_weight = np.zeros(len(self.weights[0]))

                for weight in list(self.weights):
                    weight_label = "%s (x%s) (w%s)" % (self.name, mult, weight)
                    weight_ind = res_labels.index(weight_label)

                    # all objectives are reframed so that minimizing is good: baseline - optimized = a positive number where higher is better.
                    relative_progress = sum((base.get_outputs()[:] - res[weight_ind].get_outputs()[:]) * weight)

                    if relative_progress > 0.0:
                        balanced_weight += weight * 1.0 / relative_progress

                balanced_weight *= 1.0 / max(abs(balanced_weight))  # normalize a bit so the highest absolute weight is 1.

                balanced_args.append((self.get_kwargs(model, balanced_weight, mult, keep_inds), mult) + optim)

            if parallel:
                res_balanced, scen_balanced = utils.run_parallel(self.one_optim_parallel, balanced_args, num_procs, return_two=True)
            else:
                res_balanced, scen_balanced = [], []
                for arg in balanced_args:
                    this_res, this_scen = self.one_optim(arg)
                    res_balanced.append(this_res)
                    scen_balanced.append(this_scen)
            # Prettier names
            for i, mult in enumerate(self.mults):
                mult_str = f"(mult={res_balanced[i].mult}) " if len(self.mults) > 1 or res_balanced[i].mult != 1 else ""
                res_balanced[i].name = res_balanced[i].obj + f" {mult_str}{_('Balanced objectives')}"
                scen_balanced[i].name = res_balanced[i].obj + f" {mult_str}{_('Balanced objectives')}"

        for r, result in enumerate(res):
            if len(self.mults) > 1 or result.mult != 1:  # add clarity on multiplier only if necessary
                result.name = result.obj + f" ({_('budget')} x{result.mult})"
            else:
                result.name = result.obj
            scen[r].name = result.name

        if runbalanced and len(self.weights) > 1:
            res += res_balanced
            scen += scen_balanced

        return res, scen

    def objfun_val(self, outs, weights):
        """ "This is used to find the value of the objective functional for
        different weights."""
        num_weights = np.shape(self.weights)[0]
        val = np.zeros(num_weights)
        for i in range(0, num_weights):
            val[i] = np.inner(outs, self.weights[i])
        return val

    def _filter_progs(self, model):
        if self.filter_progs:
            threshold = 0.1
            newcov = 1.0
            restrictcovs = False
            keep_inds = []
            years = len(model.sim_years)
            # compare with 0 case
            progvals = {prog: [0] for prog in self.prog_set}
            kwargs = {"scen_type": "coverage", "progvals": progvals, "growth": self.growth}
            zeroscen = Scen(**kwargs)
            zeromodel = sc.dcp(model)
            zeromodel.growth = self.growth
            zerores = run_scen(zeroscen, zeromodel, restrictcovs)
            zeroouts = zerores.get_outputs(asdict=False)
            zeroval = self.objfun_val(zeroouts, self.weights)
            # check for dependencies
            progs = list(zeromodel.prog_info.programs.values())
            alldeps = [prog.excl_deps for prog in progs] + [prog.thresh_deps for prog in progs]
            # flatten list of lists
            flatdeps = [progname for deps in alldeps for progname in deps]
            for i, prog in enumerate(self.prog_set):
                if prog in flatdeps:
                    # parent programs must be retained in the optimization
                    keep_inds.append(True)
                else:
                    thismodel = sc.dcp(model)
                    thismodel.growth = self.growth
                    # override dependencies to allow scale-up
                    thiscov = sc.dcp(progvals)
                    thiscov[prog] = [newcov] * years
                    thesekwargs = sc.dcp(kwargs)
                    thesekwargs["progvals"] = thiscov
                    thesekwargs["growth"] = self.growth
                    scen = Scen(**thesekwargs)
                    res = run_scen(scen, thismodel, restrictcovs=restrictcovs)
                    outs = res.get_outputs(asdict=False)
                    val = self.objfun_val(outs, self.weights)
                    hasimpact = abs((np.linalg.norm(val) - np.linalg.norm(zeroval)) / np.linalg.norm(zeroval)) * 100.0 > threshold
                    keep_inds.append(hasimpact)
        else:
            keep_inds = [True for i, _ in enumerate(self.prog_set)]
        if not keep_inds:
            raise Exception("No programs impact the chosen objective or none were selected.")
        return np.array(keep_inds)

    def one_optim(self, args):
        """Runs optimization for an objective and budget multiple.
        Return: a list of allocations, with order corresponding to the programs list"""
        kwargs = args[0]
        mult = args[1]
        maxiter, swarmsize, maxtime = args[2:]
        free = kwargs["free"]
        inds = kwargs["keep_inds"]
        fixed = kwargs["fixed"]
        model = kwargs["model"]
        weight = kwargs["weights"]

        _ = utils.get_translator(model.locale)

        numprogs = np.sum(inds)
        if free > 0 and np.any(inds):  # need both funds and programs
            xmin = np.zeros(numprogs)
            xmax = np.full(numprogs, free)
            now = sc.tic()
            if ((swarmsize is not None) and (swarmsize > 0)) and ((maxiter is not None) and (maxiter > 0)):
                x0, fopt = pso.pso(obj_func, xmin, xmax, kwargs=kwargs, maxiter=maxiter, swarmsize=swarmsize)
            else:
                x0 = kwargs["model"].prog_info.curr[inds]
            opt_result = sc.asd(obj_func, x0, args=kwargs, xmin=xmin, xmax=xmax, verbose=2, maxtime=maxtime, randseed=5)
            x = opt_result.x
            self.print_status(x, mult, opt_result.exitreason, now)
            scaled = utils.scale_end_alloc(free, x, model.prog_info, inds, fixed)  # scales spending to fit budget, limited by saturation and any program coverage dependencies
            inds = np.append(inds, True)
            fixed = np.append(fixed, 0.0)
            excess_spend = {"name": _("Excess budget not allocated"), "all_years": model.prog_info.all_years, "prog_data": utils.add_dummy_prog_data(model.prog_info, _("Excess budget not allocated"), model.locale)}
            model.prog_info.add_prog(excess_spend, model.pops)
            model.prog_info.prog_data = excess_spend["prog_data"]
            self.prog_set.append(_("Excess budget not allocated"))
            best_alloc = utils.add_fixed_alloc(fixed, scaled, inds)
        else:
            # if one of the multiples is 0, return fixed costs
            best_alloc = fixed
        # generate results
        name = "%s (x%s) (w%s)" % (self.name, mult, weight)
        progvals = {prog: spend for prog, spend in zip(self.prog_set, best_alloc)}
        scen = Scen(name=name, model_name=self.model_name, scen_type="budget", progvals=progvals, enforce_constraints_year=0, growth=self.growth, _optim_uid=self.uid)
        res = run_scen(scen, model, obj=self.name, mult=mult, weight=weight, restrictcovs=False)
        if _("Excess budget not allocated") in self.prog_set:
            self.prog_set.remove(_("Excess budget not allocated"))

        return res, scen

    @utils.trace_exception
    def one_optim_parallel(self, args):
        res, scen = self.one_optim(args)
        return res, scen

    def print_status(self, objective, multiple, exitreason, now):
        print("Finished optimization for %s for objective %s and multiple %s" % (self.name, objective, multiple))
        print("The reason is %s and it took %0.1f s \n" % (exitreason, sc.toc(now, output=True)))

    def __setstate__(self, d):
        self.__dict__ = d
        d = migrate(self)
        self.__dict__ = d.__dict__


def obj_func(allocation, model, free, fixed, keep_inds, weights):
    """
    Calculates the scalar value of a model run given some program allocation. Runs as a budget scenario.
    :param allocation:
    :param model: a newly instantiated model object to run the budget scenario.
    :param free: total money to be distributed across programs
    :param fixed: fixed costs for programs
    :param keep_inds: The indices of the programs to keep (those excluded are 'fixed programs')
    :param weights: an array of weights for each model outcome. Order corresponding to default_trackers()
    :return: scalar value of the model run
    """
    thisModel = sc.dcp(model)
    # scale the allocation appropriately
    scaledAllocation = utils.scale_alloc(free, allocation)
    totalAllocations = utils.add_fixed_alloc(fixed, scaledAllocation, keep_inds)
    thisModel.initialize_covs(totalAllocations, "budget")
    thisModel.run_sim()
    # get weighted objective value
    outs = thisModel.get_output()
    value = np.inner(outs, weights)
    return value


def make_default_optim(modelname=None, basename="Maximize thrive", locale=None):
    """
    Creates and returns a prototype / default optimization for a particular Model.
    """

    _ = utils.get_translator(locale)

    kwargs1 = {
        "name": basename,
        "model_name": modelname,
        "mults": [1],
        "weights": sc.odict({"thrive": [1]}),
        "prog_set": [
            _("Vitamin A supplementation"),
            _("IYCF 1"),
            _("IFA fortification of maize"),
            _("Balanced energy-protein supplementation"),
            _("Public provision of complementary foods"),
            _("Iron and iodine fortification of salt"),
        ],
        "fix_curr": False,
        "add_funds": 0,
        "filter_progs": True,
    }

    return Optim(**kwargs1, locale=locale)
