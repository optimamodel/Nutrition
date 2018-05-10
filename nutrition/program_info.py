import programs as progs
from copy import deepcopy as dcp

class ProgramInfo:
    """
    This class is a convenient container for all program objects and their applicable areas.
    Allows centralised access to all program objects to be used in the Model class.

    Attributes:
        programs: list of all program objects
        programAreas: Risks are keys with lists containing applicable program names (dict of lists)
    """
    def __init__(self, constants, prog_set):
        self.programs = progs.setPrograms(constants, prog_set)
        self.programAreas = constants.programAreas
        self.const = constants
        self.currentExpenditure = constants.currentExpenditure
        self.availableBudget = constants.availableBudget
        self._setReferencePrograms()
        self._sortPrograms()
        self._getTwins()

    def set_years(self, all_years):
        for prog in self.programs:
            prog.year = all_years[0]
            prog.all_years = all_years

    def _setReferencePrograms(self):
        for program in self.programs:
            if program.name in self.const.referencePrograms:
                program.reference = True
            else:
                program.reference = False

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

    def set_init_covs(self, pops, all_years):
        for program in self.programs:
            program.set_init_cov(pops, all_years)
        # self.restrictCovs(self.pops) ? # TODO

    def update_prog_covs(self, pops, covs, restr_cov=True):
        # TODO: two different types of input: dict of (prog, cov), where cov could be a scalar or a list of values (array?)
        for prog in self.programs:
            cov = covs[prog.name]
            prog.update_cov(cov, restr_cov=restr_cov)
        # restrict covs,
        self.restrictCovs(pops) # TODO: check that restricting here is correct

    def determine_cov_change(self):
        for prog in self.programs:
            if abs(prog.annual_cov[prog.year-1] - prog.annual_cov[prog.year]) > 1e-3:
                return True
            else:
                return False


    def _setCovsScalar(self, coverages, restrictedCov):
        for program in self.programs:
            if coverages.get(program.name) is None: # remains constant
                cov = program.annualCoverage[program.year]
                program._setCovScalar(cov, restrictedCov=False)
            else:
                cov = coverages[program.name]
                program._setCovScalar(cov, restrictedCov)

    def _setCovsWorkbook(self):
        for program in self.programs:
            program._setCovWorkbook()

    def _callProgramMethod(self, method, *args):
        """Calls method for all programs in self.programs"""
        progMethod = lambda prog: getattr(prog, method)(args) if args else lambda prog: getattr(prog, method)()
        map(lambda prog: progMethod, self.programs)

    def _adjustCovsPops(self, populations, year):
        for program in self.programs:
            program._adjustCoverage(populations, year)

    def _getTwins(self):
        # TODO: long term, exchange this for the option where we don't have these twin interventions
        for program in self.programs:
            malariaTwin = program.name + ' (malaria area)'
            program.malariaTwin = True if malariaTwin in self.const.programList else False

    def update_prog_year(self, year):
        for prog in self.programs:
            prog.year = year

    def get_ann_covs(self, year):
        covs = {}
        for prog in self.programs:
            covs[prog.name] = prog.annual_cov[year]
        return covs

    def restrictCovs(self, populations):
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