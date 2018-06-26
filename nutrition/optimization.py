import multiprocessing
import itertools
import sciris.core as sc
from . import pso
from . import asd
from . import utils
from . import data
from . import programs
from . import model


class Optim(object):
    def __init__(self, prog_info=None, pops=None, name=None, t=None, objs=None, mults=None, prog_set=None, active=True, 
                 parallel=True, num_runs=1, add_funds=0, fix_curr=False, rem_curr=False, curve_type='linear', 
                 filter_progs=True, maxiter=5, swarmsize=10, num_procs=None):
        self.name = name
        self.objs = objs
        self.mults = mults
        self.combs = list(itertools.product(self.objs, self.mults))
        self.t = t
        self.prog_set = prog_set
        self.parallel = parallel
        self.num_cpus = multiprocessing.cpu_count() if parallel else 1
        self.year_names = range(self.t[0], self.t[1] + 1)
        self.all_years = range(len(self.year_names))  # used to index lists
        self.num_runs = num_runs
        self.add_funds = add_funds
        self.fix_curr = fix_curr
        self.rem_curr = rem_curr if not fix_curr else False # can't remove if fixed
        self.curve_type = curve_type
        self.filter_progs = filter_progs
        self.maxiter = maxiter
        self.swarmsize = swarmsize

        self.prog_info = sc.dcp(prog_info)
        self.pops = sc.dcp(pops)
        self.model = model.Model(name, self.pops, self.prog_info, self.all_years)
        self.programs = self.model.prog_info.programs
        self.active = active

        self.optim_allocs = None
        self.BOCs = {}
        self.refs = None
        self.curr = None
        self.fixed = None
        self.free = None
        self.get_alloc(fix_curr)
    
    def __repr__(self):
        output  = sc.desc(self)
        return output

    ######### SETUP ############

    def get_alloc(self, fix_curr):
        """
        Designed so that currentAllocations >= fixedAllocations >= referenceAllocations.
        referenceAllocations: these allocations cannot be reduced because it is impractical to do so.
        fixedAllocations: this is funding which cannot be reduced because of the user's wishes.
        currentAllocations: this is the total current funding (incl. reference & fixed allocations) determined by program initial coverage.
        :param fix_curr:
        :return:
        """
        self.refs = self.get_refs()
        self.curr = self.get_curr()
        self.fixed = self.get_fixed(fix_curr)
        self.free = self.get_free(fix_curr)

    def get_kwargs(self, obj, mult):
        kwargs = {'model': sc.dcp(self.model),
                  'free': sc.dcp(self.free) * mult,
                  'fixed': self.fixed[:],
                  'obj': obj,
                  'sign': utils.get_obj_sign(obj),
                  'keep_inds': self._filter_progs(obj)}
        return kwargs

    def get_refs(self):
        """
        Reference programs are not included in nutrition budgets, therefore these must be removed before future calculations.
        :return: 
        """
        referenceAllocations = []
        for program in self.programs:
            if program.reference:
                referenceAllocations.append(program.get_spending())
            else:
                referenceAllocations.append(0)
        return referenceAllocations

    def get_curr(self):
        allocations = []
        for program in self.programs:
            allocations.append(program.get_spending())
        return allocations

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

    def get_free(self, fix_curr):
        """
        freeFunds = currentExpenditure + add_funds - fixedFunds (if not remove current funds)
        freeFunds = additional (if want to remove current funds)

        fixedFunds includes both reference programs as well as currentExpenditure, if the latter is to be fixed.
        I.e. if all of the currentExpenditure is fixed, freeFunds = add_funds.
        :return:
        """
        if self.rem_curr and fix_curr:
            raise Exception("::Error: Cannot remove current funds and fix current funds simultaneously::")
        elif self.rem_curr and (not fix_curr):  # this is additional to reference spending
            freeFunds = self.add_funds
        elif not self.rem_curr:
            freeFunds = sum(self.curr) - sum(self.fixed) + self.add_funds
        return freeFunds

    ######### OPTIMISATION ##########

    def run_optim(self):
        print('Optimizing for %s' % self.name)
        if self.num_cpus>1:
            self.optim_allocs = utils.run_parallel(self.one_optim, self.combs, self.num_cpus)
        else:
            self.optim_allocs = []
            for comb in self.combs:
                res = self.one_optim(comb)
                self.optim_allocs.append(res)
        return None

    @utils.trace_exception
    def one_optim(self, params):
        """ Runs optimization for an objective and budget multiple.
        Return: a list of allocations, with order corresponding to the programs list """
        obj = params[0]
        mult = params[1]
        kwargs = self.get_kwargs(obj, mult)
        if kwargs['free'] != 0:
            num_progs = len(kwargs['keep_inds'])
            xmin = [0.] * num_progs
            xmax = [kwargs['free']] * num_progs
            runOutputs = []
            for run in range(self.num_runs):
                now = sc.tic()
                x0, fopt = pso.pso(obj_func, xmin, xmax, kwargs=kwargs, maxiter=self.maxiter, swarmsize=self.swarmsize)
                x, fval, flag = asd.asd(obj_func, x0, args=kwargs, xmin=xmin, xmax=xmax, verbose=0, maxtime=30)
                runOutputs.append((x, fval[-1]))
                self.print_status(obj, mult, flag, now)
            bestAllocation = self.get_best(runOutputs)
            scaledAllocation = utils.scale_alloc(kwargs['free'], bestAllocation)
            totalAllocation = utils.add_fixed_alloc(self.fixed, scaledAllocation, kwargs['keep_inds'])
            bestAllocationDict = totalAllocation
        else:
            # if no money to distribute, return the fixed costs
            bestAllocationDict = self.fixed
        return bestAllocationDict

    def print_status(self, objective, multiple, flag, now):
        print('Finished optimization for %s for objective %s and multiple %s' % (self.name, objective, multiple))
        print('The reason is %s and it took %0.1f s \n' % (flag['exitreason'], sc.toc(now, output=True)))
   
    def get_best(self, outputs):
        bestSample = min(outputs, key=lambda item: item[-1])
        return bestSample[0]

    def _filter_progs(self, obj):
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
    programs = thisModel.prog_info.programs
    totalAllocations = utils.add_fixed_alloc(totalAllocations, scaledAllocation, keep_inds)
    new_covs = []
    for i, program in enumerate(programs):
        new_covs.append( program.func(totalAllocations[i]) )
    thisModel.run_sim(new_covs, restr_cov=False)
    outcome = thisModel.get_output(obj) * sign
    return outcome

def make_optims(country=None, region=None, user_opts=None, json=None, project=None, dataset=None):
    # WARNING, consolidate boilerplate with make_scens
    demo_data, prog_data, default_params, pops = data.get_data(country=country, region=region, project=project, dataset=dataset, withpops=True)
    optim_list = []
    if user_opts is not None:
        for opt in user_opts: # create all of the requested optimizations
            prog_info = programs.ProgramInfo(opt.prog_set, prog_data, default_params) # initialise pops and progs
            optim = Optim(prog_info, pops, **opt.get_attr()) # set up optims
            optim_list.append(optim)
    if json is not None:
        json = sc.dcp(json) # Just to be sure, probably unnecessary
        prog_info = programs.ProgramInfo(json['prog_set'], prog_data, default_params)
        optim = Optim(prog_info=prog_info, pops=pops, name=json['name'], t=json['t'], objs=json['objs'], mults=json['mults'], prog_set=json['prog_set'], active=True, add_funds=json['add_funds'], fix_curr=json['fix_curr'])
        optim_list.append(optim)
    return optim_list