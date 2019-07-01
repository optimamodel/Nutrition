import numpy as np
import multiprocessing
import sciris as sc
from . import pso, utils
from .scenarios import Scen, run_scen


class Optim(sc.prettyobj):
    """ Stores settings for running an optimization for a single objective. """

    def __init__(self, name=None, model_name=None, weights=None, mults=None, prog_set=None, active=True,
                 add_funds=0, fix_curr=False, rem_curr=False, filter_progs=True, relative_reduction=False,
                 outcome_reductions=None):
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
        :param filter_progs: filter out programs which don't impact the objective (can improve optimization results)
        :param relative_reduction: use relative reduction based objective function?
        :param outcome_reductions: an odict of (outcome, relative reduction) pairs with optional inputs for the target
        year and weighting associated with each outcome
        """

        self.name = name
        self.model_name = model_name
        self.weights = utils.process_weights(weights)
        self.mults = mults
        self.prog_set = prog_set
        self.add_funds = add_funds
        self.fix_curr = fix_curr
        self.rem_curr = rem_curr if not fix_curr else False # can't remove if fixed
        self.filter_progs = filter_progs
        self.relative_reduction = relative_reduction
        self.outcome_reductions = outcome_reductions
        self.num_cpus = multiprocessing.cpu_count()

        self.active = active

        self.num_procs = None
        self.optim_allocs = sc.odict()


    ######### SETUP ############

    def get_kwargs(self, model, weights, mult, keep_inds, relative_reduction, outcome_reductions):
        model = sc.dcp(model)
        free = model.prog_info.free
        fixed = model.prog_info.fixed
        kwargs = {'model':     model,
                  'free':      free * mult,
                  'fixed':     fixed,
                  'weights':   weights,
                  'keep_inds': keep_inds,
                  'relative_reduction': relative_reduction,
                  'outcome_reductions': outcome_reductions}
        if free == 0:
            raise Exception('There are no funds available to optimize.')
        return kwargs

    ######### OPTIMIZATION ##########

    def run_optim(self, model, maxiter=20, swarmsize=25, maxtime=160, parallel=True, num_procs=None):
        if parallel:
            how = 'parallel'
            num_procs = num_procs if num_procs else self.num_cpus
        else:
            how = 'series'
            num_procs = 1
        print('Optimizing for %s in %s' % (self.name, how))
        # get impactful programs
        keep_inds = self._filter_progs(model)
        # get the kwargs
        optim = (maxiter, swarmsize, maxtime)
        args = [(self.get_kwargs(model, self.weights, mult, keep_inds, self.relative_reduction, self.outcome_reductions)
                 , mult)+optim for mult in self.mults]
        if parallel:
            res = utils.run_parallel(self.one_optim_parallel, args, num_procs)
        else:
            res = []
            for arg in args:
                this_res = self.one_optim(arg)
                res.append(this_res)
        return res

    def _filter_progs(self, model):
        if self.filter_progs:
            threshold = 0.1
            newcov = 1.
            restrictcovs=False
            keep_inds = []
            years = len(model.sim_years)
            # compare with 0 case
            progvals = {prog:[0] for prog in self.prog_set}
            kwargs = {'scen_type': 'coverage',
                      'progvals': progvals}
            zeroscen = Scen(**kwargs)
            zeromodel = sc.dcp(model)
            zerores = run_scen(zeroscen, zeromodel, restrictcovs)
            zeroouts = zerores.get_outputs()
            zeroval = np.inner(zeroouts, self.weights)
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
                    # override dependencies to allow scale-up
                    thiscov = sc.dcp(progvals)
                    thiscov[prog] = [newcov]*years
                    thesekwargs = sc.dcp(kwargs)
                    thesekwargs['progvals'] = thiscov
                    scen = Scen(**thesekwargs)
                    res = run_scen(scen, thismodel, restrictcovs=restrictcovs)
                    outs = res.get_outputs()
                    val = np.inner(outs, self.weights)
                    hasimpact = abs((val - zeroval) / zeroval) * 100. > threshold
                    keep_inds.append(hasimpact)
        else:
            keep_inds = [True for i, _ in enumerate(self.prog_set)]
        if not keep_inds:
            raise Exception('No programs impact the chosen objective or none were selected.')
        return np.array(keep_inds)

    def one_optim(self, args):
        """ Runs optimization for an objective and budget multiple.
        Return: a list of allocations, with order corresponding to the programs list """
        kwargs = args[0]
        mult = args[1]
        maxiter, swarmsize, maxtime = args[2:]
        free = kwargs['free']
        inds = kwargs['keep_inds']
        fixed = kwargs['fixed']
        model = kwargs['model']
        numprogs = np.sum(inds)
        if free > 0 and np.any(inds): # need both funds and programs
            xmin = np.zeros(numprogs)
            xmax = np.full(numprogs, free)
            now = sc.tic()
            x0, fopt = pso.pso(obj_func, xmin, xmax, kwargs=kwargs, maxiter=maxiter, swarmsize=swarmsize)
            x, fval, flag = sc.asd(obj_func, x0, args=kwargs, xmin=xmin, xmax=xmax, verbose=2, maxtime=maxtime)
            self.print_status(self.name, mult, flag, now)
            scaled = utils.scale_alloc(free, x)
            best_alloc = utils.add_fixed_alloc(fixed, scaled, inds)
        else:
            # if one of the multiples is 0, return fixed costs
            best_alloc = fixed
        # generate results
        name = '%s (x%s)' % (self.name, mult)
        progvals = {prog:spend for prog, spend in zip(self.prog_set, best_alloc)}
        scen = Scen(name=name, model_name=self.model_name, scen_type='budget', progvals=progvals)
        res = run_scen(scen, model, obj=self.name, mult=mult)
        return res
    
    @utils.trace_exception
    def one_optim_parallel(self, args):
        res = self.one_optim(args)
        return res

    def print_status(self, objective, multiple, flag, now):
        print('Finished optimization for %s for objective %s and multiple %s' % (self.name, objective, multiple))
        print('The reason is %s and it took %0.1f s \n' % (flag['exitreason'], sc.toc(now, output=True)))


def obj_func(allocation, model, free, fixed, keep_inds, weights, relative_reduction, outcome_reductions):
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
    thisModel.update_covs(totalAllocations, 'budget')
    thisModel.run_sim()
    # check which objective function to use
    if relative_reduction:
        goals = outcome_reductions.keys() # retrieve desired outcomes
        if len(goals) > 1:
            try: # use non-standard weights if input
                index_weighting = [outcome_reductions[goal]['index_weighting'] for goal in goals]
            except KeyError:
                index_weighting = [2 for goal in goals]
            base = np.array(thisModel.get_output(outcomes=goals, years=[thisModel.t[0] for goal in goals])) # retrieve year 1 outcomes
            reductions = [outcome_reductions[goal]['max_reduction'] for goal in goals] # retrieve desired relative reductions
            try:
                years = [outcome_reductions[goal]['year'] for goal in goals] # check if non-final year input as a goal
                outs = np.array(thisModel.get_output(outcomes=goals, years=years)) # retrieve desired year outcomes
                rel_red = 100 * (1. - (outs / base)) # retrieve relative reductions achieved
            except KeyError:
                outs = np.array(thisModel.get_output(outcomes=goals)) # retrieve final year outcomes
                rel_red = 100 * (1. - (outs / base)) # retrieve relative reductions achieved
            # sum over achieved progress toward (weighted) desired relative reduction in each outcomes
            try:
                outcome_weighting = [outcome_reductions[goal]['target_reduction'] for goal in goals] # check if specific target included for weighting
                value = sum((outcome_weighting[ind] / reductions[ind]) * max(0, (1 - rr / reductions[ind]))
                            ** index_weighting[ind] for ind, rr in enumerate(rel_red))
            except KeyError:
                value = sum(max(0, (1 - rr / reductions[ind])) ** index_weighting[ind] for ind, rr in enumerate(rel_red))
            if len(goals) == 2: # add equality weighting measure between two outcomes
                value += abs(rel_red[1] / reductions[1] - rel_red[0] / reductions[0])
            elif len(goals) > 2: # add equality weighting measure for more than two outcomes
                value += sum(abs(rel_red[ind + 1] / reductions[ind + 1] - rel_red[ind] / reductions[ind]) for ind in list(range(len(goals) - 1)))
                value += abs(rel_red[0] / reductions[0] - rel_red[-1] / reductions[-1])
        else: # check progress toward desired relative reduction for only one outcome
            goal = goals[0]
            index_weighting = 1
            base = thisModel.get_output(outcomes=goals, years=thisModel.t[0]) # retrieve year 1 outcome
            reductions = outcome_reductions[goal]['max_reduction'] # retrieve desired relative reduction
            try:
                years = outcome_reductions[goal]['year'] # check if non-final year input as a goal
                outs = thisModel.get_output(outcomes=goals, years=years) # retrieve desired year outcome
                rel_red = 100 * (1 - (outs / base)) # retrieve relative reduction achieved
            except KeyError:
                outs = np.array(thisModel.get_output(outcomes=goals)) # retrieve final year outcome
                rel_red = 100 * (1 - (outs / base)) # retrieve relative reduction achieved
            value = (1 - rel_red / reductions) ** index_weighting # calculate progress toward desired relative reduction
    else: # standard objective function via inner product
        outs = thisModel.get_output()
        value = np.inner(outs, weights)
    return value

def make_default_optim(modelname=None, basename='Maximize thrive'):
    """
    Creates and returns a prototype / default optimization for a particular Model.
    """

    kwargs1 = {'name': basename,
               'model_name': modelname,
               'mults': [1],
               'weights': sc.odict({'thrive': 1}),
               'prog_set': ['Vitamin A supplementation', 'IYCF 1', 'IFA fortification of maize',
                            'Balanced energy-protein supplementation',
                            'Public provision of complementary foods',
                            'Iron and iodine fortification of salt'],
               'fix_curr': False,
               'add_funds': 0,
               'filter_progs': True}

    default = Optim(**kwargs1)
    return default
