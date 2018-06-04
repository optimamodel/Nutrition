import programs as progs

class ProgramInfo:
    """
    This class is a convenient container for all program objects and their applicable areas.
    Allows centralised access to all program objects to be used in the Model class.

    Attributes:
        programs: list of all program objects
        programAreas: Risks are keys with lists containing applicable program names (dict of lists)
    """
    def __init__(self, prog_data, default_params):
        self.prog_set = prog_data.prog_set
        self.prog_areas = self._clean_prog_areas(default_params.prog_areas)
        self.ref_progs = prog_data.ref_progs
        self.programs = progs.set_programs(self.prog_set, prog_data, default_params)
        self._set_ref_progs()
        self._sort_progs()
        self._getTwins()

    def set_years(self, all_years):
        for prog in self.programs:
            prog.year = all_years[0]
            prog.all_years = all_years

    def _set_ref_progs(self):
        for program in self.programs:
            if program.name in self.ref_progs:
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
        allNames = set([prog.name for prog in self.programs])
        for prog in self.programs:
            prog.thresholdDependencies = [name for name in prog.thresholdDependencies if name in allNames]
            prog.exclusionDependencies = [name for name in prog.exclusionDependencies if name in allNames]

    def _clean_prog_areas(self, prog_areas):
        """ Removed programs from program area list if not included in analysis """
        retain = {}
        for risk, names in prog_areas.iteritems():
            retain[risk] = [prog for prog in names if prog in self.prog_set]
        return retain


    def _get_thresh_roots(self):
        openSet = self.programs[:]
        closedSet = [program for program in openSet if not program.thresholdDependencies] # independence
        openSet = [program for program in openSet if program not in closedSet]
        return openSet, closedSet

    def _get_excl_roots(self):
        openSet = self.programs[:]
        closedSet = [program for program in openSet if not program.exclusionDependencies] # independence
        openSet = [program for program in openSet if program not in closedSet]
        return openSet, closedSet

    def _excl_sort(self):
        openSet, closedSet = self._get_excl_roots()
        for program in openSet:
            dependentNames = set(program.exclusionDependencies)
            closedSetNames = set([prog.name for prog in closedSet])
            if dependentNames.issubset(closedSetNames):  # all parent programs in closed set
                closedSet += [program]
        self.exclusionOrder = closedSet[:]

    def _thresh_sort(self):
        openSet, closedSet = self._get_thresh_roots()
        for program in openSet:
            dependentNames = set(program.thresholdDependencies)
            closedSetNames = set([prog.name for prog in closedSet])
            if dependentNames.issubset(closedSetNames):  # all parent programs in closed set
                closedSet += [program]
        self.thresholdOrder = closedSet[:]

    def set_init_covs(self, pops, all_years):
        for program in self.programs:
            program.set_annual_cov(pops, all_years)
        self.restrict_covs(pops)

    def set_init_pops(self, pops):
        for prog in self.programs:
            prog.set_pop_sizes(pops)

    def set_costcovs(self):
        for prog in self.programs:
            prog.set_costcov()

    def get_cov_scen(self, scen_type, scen):
        """ If scen is a budget scenario, convert it to unrestricted coverage.
        If scen is a coverage object, assumed to be restricted cov and coverted
        Return: assigns attribute to each program, which are lists of unrestricted covs each year"""
        for prog in self.programs:
            if 'ov' in scen_type: # coverage scen
                # convert restricted to unrestricted coverage
                cov_scen = scen.cov_scen[prog.name]
                unrestr_cov = prog.interp_cov(cov_scen, restr_cov=True)
            elif 'ud' in scen_type: # budget scen
                # convert budget into unrestricted coverage
                budget_scen = scen.budget_scen[prog.name]
                unrestr_cov = []
                for budget in budget_scen: # each year
                    unrestr_cov.append(prog.costCurveFunc(budget))
                unrestr_cov = prog.interp_cov(unrestr_cov, restr_cov=False)
            else:
                raise Exception("Error: scenario type '{}' is not valid".format(scen_type))
            prog.annual_cov = unrestr_cov

    def collect_covs(self):
        covs = {}
        for prog in self.programs:
            covs[prog.name] = prog.annual_cov
        return covs

    def update_prog_covs(self, pops, covs, restr_cov=True):
        for prog in self.programs:
            cov = covs[prog.name]
            prog.update_cov(cov, restr_cov=restr_cov)
        # restrict covs
        self.restrict_covs(pops)

    def determine_cov_change(self):
        for prog in self.programs:
            if abs(prog.annual_cov[prog.year-1] - prog.annual_cov[prog.year]) > 1e-3:
                return True
            else:
                pass
        return False

    def adjust_covs(self, pops, year):
        for program in self.programs:
            program.adjust_cov(pops, year)

    def _getTwins(self):
        # TODO: long term, exchange this for the option where we don't have these twin interventions
        for program in self.programs:
            malariaTwin = program.name + ' (malaria area)'
            program.malariaTwin = True if malariaTwin in self.prog_set else False

    def update_prog_year(self, year):
        for prog in self.programs:
            prog.year = year

    def get_ann_covs(self, year):
        covs = {}
        for prog in self.programs:
            covs[prog.name] = prog.annual_cov[year]
        return covs

    def restrict_covs(self, pops):
        """
        Uses the ordering of both dependency lists to restrict the coverage of programs.
        Assumes that the coverage is given as peopleCovered/unrestrictedPopSize.
        Since the order of dependencies matters, was decided to apply threshold first then exclusion dependencies
        Method:
        GET OVERLAPPING AGE GROUPS BETWEEN PARENT AND CHILD NODES
        SUM OVERLAPPING POP SIZES FOR PARENT NODE
        MULTIPLY BY COVERAGE % TO GET NUMBER OF PEOPLE IN OVERLAPPING POP WHO ARE ALREADY COVERED BY PARENT
        DIVIDE THIS BY RESTRICTED POP SIZE FOR CHILD NODE
        BEHAVIOUR DEPENDENT UPON RESTRICTION TYPE & SIZE OF RATIO.
        """

        # Need to get the overlapping pop because the numCovered generated by cost curves
        # potentially includes populations which are not common to both
        # threshold
        for child in self.thresholdOrder:
            for parentName in child.thresholdDependencies:
                # get overlapping age groups (intersection)
                parent = next((prog for prog in self.programs if prog.name == parentName))
                commonAges = list(set(child.agesTargeted).intersection(parent.agesTargeted))
                parentPopSize = 0.
                for pop in pops:
                    parentPopSize += sum(age.getAgeGroupPopulation() for age in pop.age_groups if age.age in commonAges)
                numCoveredInOverlap = parent.annual_cov[parent.year] * parentPopSize
                percentCoveredByParent = numCoveredInOverlap / child.restrictedPopSize
                if percentCoveredByParent < 1:
                    childMaxCov = numCoveredInOverlap / child.restrictedPopSize
                else:
                    childMaxCov = child.restrictedPopSize / child.unrestrictedPopSize
                if child.annual_cov[child.year] > childMaxCov:
                    child.annual_cov[child.year] = childMaxCov
        #exclusion
        for child in self.exclusionOrder:
            if child.exclusionDependencies:
                # get population covered by all parent nodes
                numCoveredInOverlap = 0
                for parentName in child.exclusionDependencies:
                    parentPopSize = 0
                    # get overlapping age groups (intersection)
                    parent = next((prog for prog in self.programs if prog.name == parentName))
                    commonAges = list(set(child.agesTargeted).intersection(parent.agesTargeted))
                    for pop in pops:
                        parentPopSize += sum(age.getAgeGroupPopulation() for age in pop.age_groups if age.age in commonAges)
                    numCoveredInOverlap += parent.annual_cov[parent.year] * parentPopSize
                percentCoveredByParent = numCoveredInOverlap / child.restrictedPopSize
                if percentCoveredByParent < 1:
                    childMaxCov = (child.restrictedPopSize - numCoveredInOverlap) / child.unrestrictedPopSize
                else:
                    childMaxCov = 0
                if child.annual_cov[child.year] > childMaxCov:
                    child.annual_cov[child.year] = childMaxCov