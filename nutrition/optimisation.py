import nutrition as on, pso, asd, time, cPickle, copy, multiprocessing, numpy, scipy.interpolate, scipy.optimize, itertools

class Optim(object):
    def __init__(self, prog_info, pops, name, t, objs, mults, prog_set, active=True, parallel=True, num_runs=1,
                 add_funds=0, fix_curr=False, rem_curr=False, curve_type='linear', filter_progs=True,
                 maxiter=10, swarmsize=10, num_procs=None):
        self.name = name
        self.objs = objs
        self.mults = mults
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

        self.prog_info = copy.deepcopy(prog_info)
        self.pops = copy.deepcopy(pops)
        self.model = on.model.Model(name, self.pops, self.prog_info, self.all_years)
        self.programs = self.model.prog_info.programs
        self.active = active

        self.optim_alloc = None
        self.BOCs = {}
        self.refs = None
        self.curr = None
        self.fixed = None
        self.free = None
        self.get_alloc(fix_curr)

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
        kwargs = {'model': copy.deepcopy(self.model),
                  'free': copy.deepcopy(self.free) * mult,
                  'fixed': self.fixed[:],
                  'obj': obj,
                  'sign': on.utils.get_obj_sign(obj),
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
            fixed = copy.deepcopy(self.curr)
        else:
            fixed = copy.deepcopy(self.refs)
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
        print 'Optimising for {}'.format(self.name)
        buds = self.check_budget()
        self.optim_alloc = on.utils.run_parallel(self.one_optim, itertools.product(self.objs, buds), self.num_cpus)

    def check_budget(self):
        """For 0 free funds, spending is equal to the fixed costs"""
        if 0 in self.mults:
            newBudgets = filter(lambda x: x > 0, self.mults)
            # output fixed spending
            for objective in self.objs:
                allocationDict = self.createDictionary(self.fixed)
                self.writeToPickle(allocationDict, 0, objective)
        else:
            newBudgets = self.mults
        return newBudgets

    @on.utils.trace_exception
    def one_optim(self, params):
        obj = params[0]
        mult = params[1]
        kwargs = self.get_kwargs(obj, mult)
        if kwargs['free'] != 0:
            num_progs = len(kwargs['keep_inds'])
            xmin = [0.] * num_progs
            xmax = [kwargs['free']] * num_progs # TODO: could make this cost of saturation.
            runOutputs = []
            for run in range(self.num_runs):
                now = time.time()
                x0, fopt = pso.pso(obj_func, xmin, xmax, kwargs=kwargs, maxiter=self.maxiter, swarmsize=self.swarmsize)
                x, fval, flag = asd.asd(obj_func, x0, args=kwargs, xmin=xmin, xmax=xmax, verbose=0)
                runOutputs.append((x, fval[-1]))
                self.printMessages(obj, mult, flag, now)
            bestAllocation = self.findBestAllocation(runOutputs)
            scaledAllocation = on.utils.scale_alloc(kwargs['free'], bestAllocation)
            totalAllocation = on.utils.add_fixed_alloc(self.fixed, scaledAllocation, kwargs['keep_inds'])
            bestAllocationDict = self.createDictionary(totalAllocation)
        else:
            # if no money to distribute, return the fixed costs
            bestAllocationDict = self.createDictionary(self.fixed)
        return bestAllocationDict

    def printMessages(self, objective, multiple, flag, now):
        print 'Finished optimisation for {} for objective {} and multiple {}'.format(self.name, objective, multiple)
        print 'The reason is {} and it took {} minutes \n'.format(flag['exitreason'], round((time.time() - now) / 60., 2))

    def findBestAllocation(self, outputs):
        bestSample = min(outputs, key=lambda item: item[-1])
        return bestSample[0]

    def createDictionary(self, allocations):
        """Ensure keys and values have matching orders"""
        keys = [program.name for program in self.programs]
        returnDict = {key: value for key, value in zip(keys, allocations)}
        return returnDict

    def _filter_progs(self, obj):
        if self.filter_progs:
            threshold = 0.5
            newcov = 1.
            keep_inds = []
            # compare with 0 case
            zero_cov = [0 for prog in self.programs]
            zero_model = copy.deepcopy(self.model)
            zero_model.run_sim(zero_cov, restr_cov=True)
            zero_out = zero_model.get_outcome(obj)
            for i, prog in enumerate(self.programs):
                thismodel = copy.deepcopy(self.model)
                thiscov = copy.deepcopy(zero_cov)
                thiscov[i] = newcov
                # scale up twin concurrently
                if prog.twin_ind:
                    thiscov[prog.twin_ind] = newcov
                thismodel.run_sim(thiscov)
                out = thismodel.get_outcome(obj)
                if abs((out - zero_out) / zero_out) * 100. > threshold:  # no impact
                    keep_inds.append(i)
                    if prog.twin_ind:
                        keep_inds.append(prog.twin_ind)
            return keep_inds
        else:
            return [i for i in range(len(self.programs))]

    def interpolateBOC(self, objective, spending, outcome):
        # need BOC for each objective in region
        # spending, outcome = self.getBOCvectors(objective)
        self.BOCs[objective] = scipy.interpolate.pchip(spending, outcome, extrapolate=False)

    def getBOCvectors(self, objective, budgetMultiples):
        spending = numpy.array([])
        outcome = numpy.array([])
        for multiple in budgetMultiples:
            spending = numpy.append(spending, multiple * self.free)
            filePath = '{}/{}_{}_{}.pkl'.format(self.resultsDir, self.name, objective, multiple)
            f = open(filePath, 'rb')
            thisAllocation = cPickle.load(f)
            f.close()
            output = self.oneModelRunWithOutput(thisAllocation).getOutcome(objective)
            outcome = numpy.append(outcome, output)
        return spending, outcome

    # ########### FILE HANDLING ############
    # # TODO: remove this, new results handling
    #
    # def writeToPickle(self, allocation, multiple, objective):
    #     fileName = '{}/{}_{}_{}.pkl'.format(self.resultsDir, self.name, objective, multiple)
    #     outfile = open(fileName, 'wb')
    #     cPickle.dump(allocation, outfile)
    #     return
    #
    # def readPickles(self):
    #     allocations = {}
    #     for objective in self.objectives:
    #         allocations[objective] = {}
    #         for multiple in self.budgetMultiples:
    #             filename = '{}/{}_{}_{}.pkl'.format(self.resultsDir, self.name, objective, multiple)
    #             f = open(filename, 'rb')
    #             allocations[objective][multiple] = cPickle.load(f)
    #             f.close()
    #     return allocations
    #
    # def getOutcome(self, allocation, objective):
    #     model = self.oneModelRunWithOutput(allocation)
    #     outcome = model.getOutcome(objective)
    #     return outcome
    #
    # def oneModelRunWithOutput(self, allocationDictionary):
    #     model = copy.deepcopy(self.model)
    #     newCoverages = self.getCoverages(allocationDictionary)
    #     model.simulateScalar(newCoverages, restrictedCov=False)
    #     return model
    #
    # def getOptimisedOutcomes(self, allocations):
    #     outcomes = {}
    #     for objective in self.objectives:
    #         outcomes[objective] = {}
    #         for multiple in self.budgetMultiples:
    #             thisAllocation = allocations[objective][multiple]
    #             outcomes[objective][multiple] = self.getOutcome(thisAllocation, objective)
    #     return outcomes
    #
    # def getCurrentOutcome(self, currentSpending):
    #     currentOutcome = {}
    #     for objective in self.objectives:
    #         currentOutcome[objective] = {}
    #         currentOutcome[objective]['current spending'] = self.getOutcome(currentSpending, objective)
    #     return currentOutcome
    #
    # def getZeroSpendingOutcome(self):
    #     zeroSpending = {program.name: 0 for program in self.programs}
    #     baseline = {}
    #     for objective in self.objectives:
    #         baseline[objective] = {}
    #         baseline[objective]['zero spending'] = self.getOutcome(zeroSpending, objective)
    #     return baseline
    #
    # def getReferenceOutcome(self, refSpending):
    #     reference = {}
    #     for objective in self.objectives:
    #         reference[objective] = {}
    #         reference[objective]['reference spending'] = self.getOutcome(refSpending, objective)
    #     return reference
    #
    # def getCoverages(self, allocations):
    #     newCoverages = {}
    #     for program in self.programs:
    #         newCoverages[program.name] = program.costcov_func(allocations[program.name]) / program.unrestrictedPopSize
    #     return newCoverages
    #
    # def writeAllResults(self):
    #     currentSpending = self.createDictionary(self.curr)
    #     currentOutcome = self.getCurrentOutcome(currentSpending)
    #     referenceSpending = self.createDictionary(self.refs)
    #     referenceOutcome = self.getReferenceOutcome(referenceSpending)
    #     optimisedAllocations = self.readPickles()
    #     optimisedOutcomes = self.getOptimisedOutcomes(optimisedAllocations)
    #     currentAdditionalList = [a - b for a, b in zip(self.curr, self.refs)]
    #     currentAdditional = self.createDictionary(currentAdditionalList)
    #     optimisedAdditional = self.getOptimisedAdditional(optimisedAllocations)
    #     coverages = self.getOptimalCoverages(optimisedAllocations)
    #     self.writeOutcomesToCSV(referenceOutcome, currentOutcome, optimisedOutcomes)
    #     self.writeAllocationsToCSV(referenceSpending, currentAdditional, optimisedAdditional)
    #     self.writeCoveragesToCSV(coverages)
    #
    # def getOptimisedAdditional(self, optimised):
    #     fixedCostsDict = self.createDictionary(self.fixed)
    #     optimisedAdditional = {}
    #     for objective in self.objectives:
    #         optimisedAdditional[objective] = {}
    #         for multiple in self.budgetMultiples:
    #             add_funds = optimised[objective][multiple]
    #             optimisedAdditional[objective][multiple] = {}
    #             for programName in add_funds.iterkeys():
    #                 optimisedAdditional[objective][multiple][programName] = add_funds[programName] - \
    #                                                                         fixedCostsDict[programName]
    #     return optimisedAdditional
    #
    # def getOptimalCoverages(self, optimisedAllocations):
    #     coverages = {}
    #     for objective in self.objectives:
    #         coverages[objective] = {}
    #         for multiple in self.budgetMultiples:
    #             coverages[objective][multiple] = {}
    #             allocations = optimisedAllocations[objective][multiple]
    #             for program in self.programs:
    #                 # this gives the restricted coverage
    #                 coverages[objective][multiple][program.name] = "{0:.2f}".format(
    #                     (program.costcov_func(allocations[program.name]) / program.restrictedPopSize) * 100.)
    #     return coverages
    #
    # def writeCoveragesToCSV(self, coverages):
    #     filename = '{}/{}_coverages.csv'.format(self.resultsDir, self.name)
    #     with open(filename, 'wb') as f:
    #         w = writer(f)
    #         for objective in self.objectives:
    #             w.writerow([''])
    #             w.writerow([objective] + sorted(coverages[objective][self.budgetMultiples[0]].keys()))
    #             for multiple in self.budgetMultiples:
    #                 coverage = OrderedDict(sorted(coverages[objective][multiple].items()))
    #                 w.writerow([multiple] + coverage.values())
    #
    # def writeOutcomesToCSV(self, reference, current, optimised):
    #     allOutcomes = {}
    #     for objective in self.objectives:
    #         allOutcomes[objective] = {}
    #         allOutcomes[objective].update(reference[objective])
    #         allOutcomes[objective].update(current[objective])
    #         allOutcomes[objective].update(optimised[objective])
    #     filename = '{}/{}_outcomes.csv'.format(self.resultsDir, self.name)
    #     budgets = ['reference spending', 'current spending'] + self.budgetMultiples
    #     with open(filename, 'wb') as f:
    #         w = writer(f)
    #         for objective in self.objectives:
    #             w.writerow([objective])
    #             for multiple in budgets:
    #                 outcome = allOutcomes[objective][multiple]
    #                 w.writerow(['', multiple, outcome])
    #
    # def writeAllocationsToCSV(self, reference, current, optimised):
    #     allSpending = {}
    #     for objective in self.objectives:  # do i use this loop?
    #         allSpending[objective] = {}
    #         allSpending[objective].update(current)
    #         allSpending[objective].update(reference)
    #         allSpending[objective].update(optimised[objective])
    #     filename = '{}/{}_allocations.csv'.format(self.resultsDir, self.name)
    #     with open(filename, 'wb') as f:
    #         w = writer(f)
    #         sortedRef = OrderedDict(sorted(reference.items()))
    #         w.writerow(['reference'] + sortedRef.keys())
    #         w.writerow([''] + sortedRef.values())
    #         w.writerow([''])
    #         sortedCurrent = OrderedDict(sorted(current.items()))
    #         w.writerow(['current'] + sortedCurrent.keys())
    #         w.writerow([''] + sortedCurrent.values())
    #         for objective in self.objectives:
    #             w.writerow([''])
    #             w.writerow([objective] + sorted(optimised[objective][self.budgetMultiples[0]].keys()))
    #             for multiple in self.budgetMultiples:
    #                 allocation = OrderedDict(sorted(optimised[objective][multiple].items()))
    #                 w.writerow([multiple] + allocation.values())

def obj_func(allocation, obj, model, free, fixed, keep_inds, sign):
    thisModel = copy.deepcopy(model)
    totalAllocations = fixed[:]
    # scale the allocation appropriately
    scaledAllocation = on.utils.scale_alloc(free, allocation)
    programs = thisModel.prog_info.programs
    totalAllocations = on.utils.add_fixed_alloc(totalAllocations, scaledAllocation, keep_inds)
    new_covs = []
    for i, program in enumerate(programs):
        new_covs.append( program.func(totalAllocations[i]) )
    thisModel.run_sim(new_covs, restr_cov=False)
    outcome = thisModel.get_outcome(obj) * sign
    return outcome

def make_optims(country, region, user_opts):
    demo_data, prog_data, default_params = on.data.get_data(country, region)
    optim_list = []
    # create all of the requested optimizations
    for opt in user_opts:
        # initialise pops and progs
        prog_info = on.program_info.ProgramInfo(opt.prog_set, prog_data, default_params)
        pops = on.populations.set_pops(demo_data, default_params)
        # set up optims
        optim = Optim(prog_info, pops, **opt.get_attr())
        optim_list.append(optim)
    return optim_list

def default_optims(project, key='default', dorun=False):
    country = 'master'
    region = 'master'

    defaults = on.data.OptimOptsTest(key)
    opts = [on.utils.OptimOpts(**defaults.get_attr())]
    optim_list = make_optims(country, region, opts)
    project.add_optims(optim_list)
    if dorun:
        project.run_optims()