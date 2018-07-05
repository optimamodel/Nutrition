import multiprocessing
import sciris.core as sc
import numpy as np
from . import pso
from . import asd
from . import utils
from .scenarios import Scen, run_scen


class Optim(object):
    """ Stores settings for running an optimization for a single objective. """

    def __init__(self, name=None, model_name=None, obj=None, mults=None, prog_set=None, active=True,
                 num_runs=1, add_funds=0, fix_curr=False, rem_curr=False, curve_type='linear',
                 filter_progs=True):
        
        self.name = name
        self.model_name = model_name
        self.obj = obj
        self.mults = mults
        self.prog_set = prog_set
        self.num_runs = num_runs
        self.add_funds = add_funds
        self.fix_curr = fix_curr
        self.rem_curr = rem_curr if not fix_curr else False # can't remove if fixed
        self.curve_type = curve_type
        self.filter_progs = filter_progs
        self.num_cpus = multiprocessing.cpu_count()

        self.active = active

        self.num_procs = None
        self.optim_allocs = sc.odict
        self.BOCs = {}

    def __repr__(self):
        output  = sc.desc(self)
        return output

    ######### SETUP ############

    def get_kwargs(self, model, obj, mult):
        model = sc.dcp(model)
        free = model.prog_info.free
        fixed = model.prog_info.fixed
        num_progs = len(model.prog_info.programs)
        kwargs = { 'model': model,
                  'free': free * mult,
                  'fixed': fixed,
                  'obj': obj,
                  'sign': utils.get_obj_sign(obj),
                   'keep_inds': [i for i in range(num_progs)]}
                   # 'keep_inds': self._filter_progs(obj) }
        return kwargs, mult

    ######### OPTIMIZATION ##########

    def run_optim(self, model, parallel=True, num_procs=None):
        if parallel:
            how = 'parallel'
            num_procs = num_procs if num_procs else self.num_cpus
        else:
            how = 'serial'
            num_procs = 1
        print('Optimizing for %s in %s' % (self.name, how))
        # list of kwargs
        args = [self.get_kwargs(model, self.obj, mult) for mult in self.mults]
        res = utils.run_parallel(self.one_optim, args, num_procs)
        return res

    @utils.trace_exception
    def one_optim(self, args, maxiter=5, swarmsize=10, maxtime=None):
        """ Runs optimization for an objective and budget multiple.
        Return: a list of allocations, with order corresponding to the programs list """
        kwargs = args[0]
        mult = args[1]
        if kwargs['free'] != 0:
            num_progs = len(kwargs['keep_inds'])
            xmin = np.zeros(num_progs)
            xmax = np.full(num_progs, kwargs['free'])
            runOutputs = []
            for run in range(self.num_runs):
                now = sc.tic()
                x0, fopt = pso.pso(obj_func, xmin, xmax, kwargs=kwargs, maxiter=maxiter, swarmsize=swarmsize)
                x, fval, flag = asd.asd(obj_func, x0, args=kwargs, xmin=xmin, xmax=xmax, verbose=2, maxtime=maxtime)
                runOutputs.append((x, fval[-1]))
                self.print_status(kwargs['obj'], mult, flag, now)
            best_alloc = self.get_best(runOutputs)
            scaled = utils.scale_alloc(kwargs['free'], best_alloc)
            best_alloc = utils.add_fixed_alloc(kwargs['fixed'], scaled, kwargs['keep_inds'])
        else:
            # if no money to distribute, return the fixed costs
            best_alloc = kwargs['fixed']
        # generate results
        name = '{}_{}'.format(self.name, mult)
        model = kwargs['model']
        prog_set = [prog.name for prog in model.prog_info.programs]
        scen = Scen(name=name, model_name=self.model_name, scen_type='budget', covs=best_alloc, prog_set=prog_set)
        res = run_scen(scen, model, obj=kwargs['obj'], mult=mult)
        return res

    def print_status(self, objective, multiple, flag, now):
        print('Finished optimization for %s for objective %s and multiple %s' % (self.name, objective, multiple))
        print('The reason is %s and it took %0.1f s \n' % (flag['exitreason'], sc.toc(now, output=True)))
   
    def get_best(self, outputs):
        bestSample = min(outputs, key=lambda item: item[-1])
        return bestSample[0]

    def _filter_progs(self, obj): # todo: put this in proginfo
        if self.filter_progs:
            threshold = 0.5
            newcov = 1.
            keep_inds = []
            # compare with 0 case
            zero_cov = [0 for prog in self.programs]
            zero_model = sc.dcp(self.model)
            zero_model.run_sim(zero_cov, restr_cov=True)
            zero_out = zero_model.get_output(obj)
            for i, prog in enumerate(self.programs):
                thismodel = sc.dcp(self.model)
                thiscov = sc.dcp(zero_cov)
                thiscov[i] = newcov
                # scale up twin concurrently
                if prog.twin_ind:
                    thiscov[prog.twin_ind] = newcov
                thismodel.run_sim(thiscov)
                out = thismodel.get_output(obj)
                if abs((out - zero_out) / zero_out) * 100. > threshold:  # no impact
                    keep_inds.append(i)
                    if prog.twin_ind:
                        keep_inds.append(prog.twin_ind)
            return keep_inds
        else:
            return [i for i in range(len(self.programs))]

def obj_func(allocation, obj, model, free, fixed, keep_inds, sign):
    thisModel = sc.dcp(model)
    totalAllocations = fixed[:]
    # scale the allocation appropriately
    scaledAllocation = utils.scale_alloc(free, allocation)
    totalAllocations = utils.add_fixed_alloc(totalAllocations, scaledAllocation, keep_inds)
    thisModel.update_covs(totalAllocations, 'budget')
    thisModel.run_sim()
    outcome = thisModel.get_output(obj) * sign
    return outcome