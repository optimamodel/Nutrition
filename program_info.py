class ProgramInfo:
    """
    This class is a convenient container for all program objects and their applicable areas.
    Allows centralised access to all program objects to be used in the Model class.

    Attributes:
        programs: list of all program objects
        programAreas: Risks are keys with lists containing applicable program names (dict of lists)
    """
    def __init__(self, constants):
        """
        :param project: container for all data read in from workbook
        :type project: instance of Project class
        """
        import programs as progs
        self.programs = progs.setUpPrograms(constants)
        self.programAreas = constants.programAreas
        self.referencePrograms = constants.referencePrograms
        self.const = constants
        self._sortPrograms()
        self._getTwins()

    def _sortPrograms(self):
        """
        Sorts the program list by dependency such that the resulting order will be most independent to least independent.
        Uses a variant of a breadth-first search,
        whereby the order of the sorted list is a flattened tree structure
        (root, first level, second level etc..)
        :return:
        """
        self._removeMissingPrograms()
        self._thresholdSort() # TODO: would like to have only one function to do both sortings
        self._exclusionSort()

    def _removeMissingPrograms(self):
        """Removes programs from dependencies lists which are not included in analysis"""
        allNames = set([prog.name for prog in self.programs])
        for prog in self.programs:
            prog.thresholdDependencies = [name for name in prog.thresholdDependencies if name in allNames]
            prog.exclusionDependencies = [name for name in prog.exclusionDependencies if name in allNames]

    def _getThresholdRoots(self):
        openSet = self.programs[:]
        closedSet = [program for program in openSet if not program.thresholdDependencies] # independence
        openSet = [program for program in openSet if program not in closedSet]
        return openSet, closedSet

    def _getExclusionRoots(self):
        openSet = self.programs[:]
        closedSet = [program for program in openSet if not program.exclusionDependencies] # independence
        openSet = [program for program in openSet if program not in closedSet]
        return openSet, closedSet

    def _exclusionSort(self):
        openSet, closedSet = self._getExclusionRoots()
        for program in openSet:
            dependentNames = set(program.exclusionDependencies)
            closedSetNames = set([prog.name for prog in closedSet])
            if dependentNames.issubset(closedSetNames):  # all parent programs in closed set
                closedSet += [program]
        self.exclusionOrder = closedSet[:]

    def _thresholdSort(self):
        openSet, closedSet = self._getThresholdRoots()
        for program in openSet:
            dependentNames = set(program.thresholdDependencies)
            closedSetNames = set([prog.name for prog in closedSet])
            if dependentNames.issubset(closedSetNames):  # all parent programs in closed set
                closedSet += [program]
        self.thresholdOrder = closedSet[:]

    def _setBaselineCov(self, populations):
        """
        Adjusts the baseline coverages to be unrestricted baseline coverage.
        :param populations:
        :return:
        """
        self.baselineCovs = {}
        for program in self.programs:
            program._setBaselineCoverage(populations)
            self.baselineCovs[program.name] = program.unrestrictedBaselineCov

    def _setSimulationCoverageFromScalar(self, coverages, restrictedCov):
        for program in self.programs:
            cov = coverages[program.name]
            program._setSimulationCoverageFromScalar(cov, restrictedCov)

    def _setSimulationCoverageFromWorkbook(self):
        for program in self.programs:
            program._setSimulationCoverageFromWorkbook()

    def _callProgramMethod(self, method):
        """Calls method for all programs in self.programs"""
        map(lambda prog: getattr(prog, method)(), self.programs)

    def _setAnnualCoverages(self, populations, years, optimise):
        for program in self.programs:
            program._setAnnualCoverage(populations, years, optimise)

    def _adjustCoveragesForPopGrowth(self, populations, year):
        for program in self.programs:
            program._adjustCoverage(populations, year)

    def _getTwins(self):
        # TODO: long term, exchange this for the option where we don't have these twin interventions
        for program in self.programs:
            malariaTwin = program.name + ' (malaria area)'
            program.malariaTwin = True if malariaTwin in self.const.programList else False

    def _updateYearForPrograms(self, year):
        for prog in self.programs:
            prog.year = year

    def _getAnnualCoverage(self, year):
        coverages = {}
        for prog in self.programs:
            coverages[prog.name] = prog.annualCoverage[year]
        return coverages

    def _restrictCoverages(self, populations):
        """
        Uses the ordering of both dependency lists to restrict the coverage of programs.
        Assumes that the coverage is given as peopleCovered/unrestrictedPopSize.
        Since the order of dependencies matters, was decided to apply threshold first then exclusion dependencies
        :param newCoverages:
        :return:
        """
        # GET OVERLAPPING AGE GROUPS BETWEEN PARENT AND CHILD NODES
        # SUM OVERLAPPING POP SIZES FOR PARENT NODE
        # MULTIPLY BY COVERAGE % TO GET NUMBER OF PEOPLE IN OVERLAPPING POP WHO ARE ALREADY COVERED BY PARENT
        # DIVIDE THIS BY RESTRICTED POP SIZE FOR CHILD NODE
        # BEHAVIOUR DEPENDENT UPON RESTRICTION TYPE & SIZE OF RATIO.

        # TODO: need to think carefully about using coverage dictionary or not
        # Need to get the overlapping pop because the numCovered generated by cost curves
        # potentially includes populations which are not common to both
        # TODO: the following could use a clean-up
        # threshold
        for child in self.thresholdOrder:
            for parentName in child.thresholdDependencies:
                # get overlapping age groups (intersection)
                parent = next((prog for prog in self.programs if prog.name == parentName))
                commonAges = list(set(child.agesTargeted).intersection(parent.agesTargeted))
                parentPopSize = 0.
                for pop in populations:
                    parentPopSize += sum(age.getAgeGroupPopulation() for age in pop.ageGroups if age.age in commonAges)
                numCoveredInOverlap = parent.annualCoverage[parent.year] * parentPopSize
                percentCoveredByParent = numCoveredInOverlap / child.restrictedPopSize
                if percentCoveredByParent < 1:
                    childMaxCov = numCoveredInOverlap / child.restrictedPopSize
                else:
                    childMaxCov = child.restrictedPopSize / child.unrestrictedPopSize
                if child.annualCoverage[child.year] > childMaxCov:
                    child.annualCoverage[child.year] = childMaxCov
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
                    for pop in populations:
                        parentPopSize += sum(age.getAgeGroupPopulation() for age in pop.ageGroups if age.age in commonAges)
                    numCoveredInOverlap += parent.annualCoverage[parent.year] * parentPopSize
                percentCoveredByParent = numCoveredInOverlap / child.restrictedPopSize
                if percentCoveredByParent < 1:
                    childMaxCov = (child.restrictedPopSize - numCoveredInOverlap) / child.unrestrictedPopSize
                else:
                    childMaxCov = 0
                if child.annualCoverage[child.year] > childMaxCov:
                    child.annualCoverage[child.year] = childMaxCov