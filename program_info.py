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
        self._thresholdSort()
        self._exclusionSort()

    def _getThresholdRoots(self):
        openSet = self.programs[:]
        closedSet = [program for program in openSet if not program.thresholdDependencies] # independence
        openSet = [program for program in openSet if program not in closedSet]
        return openSet, closedSet

    def _getExclusionRoots(self):
        openSet = self.programs[:]
        closedSet = [program for program in openSet if not program.exclusionDepedencies] # independence
        openSet = [program for program in openSet if program not in closedSet]
        return openSet, closedSet

    def _exclusionSort(self):
        openSet, closedSet = self._getExclusionRoots()
        for program in openSet:
            dependentNames = set(program.exclusionDepedencies)
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
