import numpy as np
import multiprocessing
import sciris as sc
from . import pso, utils
from .scenarios import Scen, run_scen


class Optim(object):
    """ Stores settings for running an optimization for a single objective. """

    def __init__(self, name=None, model_name=None, obj=None, weights=None, mults=None, prog_set=None, active=True,
                 add_funds=0, fix_curr=False, rem_curr=False, curve_type='linear',
                 filter_progs=True):
        """
        :param name: the name of the optimization (string)
        :param model_name: the name of the model corresponding to optimizations (string)
        :param obj: the name of the objective to optimize. This can be an outcome stored in utils.default_trackers() or custom.
        If custom, a vector of weights with the same order will need to be specified.
        :param weights: the weights to be applied to the model outcomes, order as in utils.default_trackers(). If 'obj' is pre-defined, don't need to specify this.
        :param mults: multiples of free funds
        :param prog_set: the programs to include in optimization (list of strings)
        :param active: whether to run in project class (boolean)
        :param add_funds: additional funds
        :param fix_curr: fix the current allocations?
        :param rem_curr: remove the current allocations?
        :param curve_type: the type for cost-coverage curve
        :param filter_progs: filter out programs which don't impact the objective (can improve optimization results)
        """

        self.name = name
        self.model_name = model_name
        self.obj = obj
        self.weights = weights if weights is not None else utils.get_weights(obj)
        self.mults = mults
        self.prog_set = prog_set
        self.add_funds = add_funds
        self.fix_curr = fix_curr
        self.rem_curr = rem_curr if not fix_curr else False # can't remove if fixed
        self.curve_type = curve_type
        self.filter_progs = filter_progs
        self.num_cpus = multiprocessing.cpu_count()

        self.active = active

        self.num_procs = None
        self.optim_allocs = sc.odict()
        self.BOCs = {}

    def __repr__(self):
        output  = sc.prepr(self)
        return output

    ######### SETUP ############

    def get_kwargs(self, model, weights, mult, keep_inds):
        model = sc.dcp(model)
        free = model.prog_info.free
        fixed = model.prog_info.fixed
        kwargs = { 'model':     model,
                   'free':      free * mult,
                   'fixed':     fixed,
                   'weights':   weights,
                   'keep_inds': keep_inds}
        return kwargs

    ######### OPTIMIZATION ##########

    def run_optim(self, model, maxiter=5, swarmsize=10, maxtime=10, parallel=True, num_procs=None):
        if parallel:
            how = 'parallel'
            num_procs = num_procs if num_procs else self.num_cpus
        else:
            how = 'serial'
            num_procs = 1
        print('Optimizing for %s in %s' % (self.name, how))
        # list of kwargs
        keep_inds = self._filter_progs(model, self.obj) # not dependent upon spending
        optim = (maxiter, swarmsize, maxtime)
        args = [(self.get_kwargs(model, self.weights, mult, keep_inds), mult)+optim for mult in self.mults]
        if parallel:
            res = utils.run_parallel(self.one_optim, args, num_procs)
        else:
            res = []
            for arg in args:
                this_res = self.one_optim(arg)
                res.append(this_res)
        return res

    def _filter_progs(self, model, obj): # todo: need to update this. Could use objective function
        if self.filter_progs:
            threshold = 0.1
            newcov = 1.
            keep_inds = []
            years = len(model.sim_years)
            # compare with 0 case
            progvals = {prog:[0] for prog in self.prog_set}
            kwargs = {'scen_type': 'cov',
                      'progvals': progvals}
            scen = Scen(**kwargs)
            zeromodel = sc.dcp(model)
            zerores = run_scen(scen, zeromodel)
            zeroout = zerores.get_outputs(obj)[0][0]
            for i, prog in enumerate(self.prog_set):
                thismodel = sc.dcp(model)
                thiscov = sc.dcp(progvals)
                thiscov[prog] = [newcov]*years
                thesekwargs = sc.dcp(kwargs)
                thesekwargs['progvals'] = thiscov
                scen = Scen(**thesekwargs)
                res = run_scen(scen, thismodel)
                out = res.get_outputs(obj)[0][0] # todo: will need to update this for weighting
                hasimpact = abs((out - zeroout) / zeroout) * 100. > threshold
                keep_inds.append(hasimpact)
            if not any(keep_inds): # no programs had impact
                print('Warning: selected programs do not impact objective "%s"' % obj)
        else:
            keep_inds = [True for i, _ in enumerate(self.prog_set)]
        return np.array(keep_inds)

    @utils.trace_exception
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
            self.print_status(self.obj, mult, flag, now)
            scaled = utils.scale_alloc(free, x)
            best_alloc = utils.add_fixed_alloc(fixed, scaled, inds)
        else:
            # if no money to distribute, return the fixed costs
            if self.name != 'Baseline':
                print('Warning: degenerate optimization, returning fixed allocations \n objective: %s '
                  '\n flexible funds: %s \n impactful progs: %s' % (self.obj, free, numprogs))
            best_alloc = fixed
        # generate results
        name = '%s (x%s)' % (self.name, mult)
        progvals = {prog:spend for prog, spend in zip(self.prog_set, best_alloc)}
        scen = Scen(name=name, model_name=self.model_name, scen_type='budget', progvals=progvals)
        res = run_scen(scen, model, obj=self.obj, mult=mult)
        return res

    def print_status(self, objective, multiple, flag, now):
        print('Finished optimization for %s for objective %s and multiple %s' % (self.name, objective, multiple))
        print('The reason is %s and it took %0.1f s \n' % (flag['exitreason'], sc.toc(now, output=True)))


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
    thisModel.update_covs(totalAllocations, 'budget')
    thisModel.run_sim()
    # get weighted objective value
    outs = thisModel.get_output()
    value = np.inner(outs, weights)
    return value