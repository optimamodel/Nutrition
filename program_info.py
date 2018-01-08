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
        self.programs = progs.setUpPrograms(constants) # TODO: could sort programs by dependency in here.
        self.programAreas = constants.programAreas