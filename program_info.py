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
        self._sortPrograms()

    def _sortPrograms(self):
        """
        Sorts the program list by dependency such that the resulting order will be most independent to least independent.
        Uses a variant of a breadth-first search,
        whereby the order of the sorted list is a flattened tree structure
        (root, first level, second level etc..)
        :return:
        """
        self._thresholdSort() # TODO: would like to have only one function to do both sortings
        self._exclusionSort()

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

    def _restrictCoverages(self, newCoverages):
        """
        Uses the ordering of both dependency lists to restrict the coverage of programs.
        Since the order of dependencies matters, was decided to apply threshold first then exclusion dependencies
        :param newCoverages:
        :return:
        """
        # TODO: currently assuming coverage is dictionary.

        # TODO: this structure is correct but need to calculate the proper coverage comparison
        #threshold
        for child in self.thresholdOrder:
            childName = child.name
            for parentName in child.thresholdDependencies:
                maxCov = newCoverages[parentName]
                if newCoverages[childName] > maxCov: # TODO: this does not account for the mis-match in coverages -- need to calculate this
                    newCoverages[childName] = maxCov
        #exclusion
        for child in self.exclusionOrder:
            childName = child.name
            for parentName in child.exclusionDependencies:
                maxCov = 1.-newCoverages[parentName]
                if newCoverages[childName] > maxCov:
                    newCoverages[childName] = maxCov
        return newCoverages

