from copy import deepcopy as dcp
class Model:
    def __init__(self, filePath):
        import data2 as data
        import populations2 as pops
        # import programs as progs
        import program_info
        self.project = data.setUpProject(filePath)
        self.programInfo = program_info.ProgramInfo(self.project)
        self.populations = pops.setUpPopulations(self.project) # TODO: concerned about making dependence between populations and programs
        self.year = None # TODO: get this from spreadsheet
        self.newCoverages = None

    # TODO: goal is to be able to call 'for population in populations', then 'population.update()' and the magic happens in populations module
    # Pass in the program info as argument to the update method of populations
    # TODO: self.programInfo contains the program objects etc, so that we can pass to the populations for updating.


    def _updateCoverages(self):
        for program in self.programInfo.programs:
            program._updateCoverage(self.newCoverages[program.name])


    def applyUpdates(self, newCoverages):
        '''newCoverages is required to be the overall coverage % (i.e. people covered / entire target pop) '''
        self.newCoverages = dcp(newCoverages)
        self._updateCoverages()
        for pop in self.populations: # update all the populations
            pop._update(self.programInfo)


















        # TODO: these functions may now have been superseded.
        # stuntingUpdate = self._getStuntingUpdate()
        # anaemiaUpdate = self._getAnaemiaUpdate()
        # wastingUpdate = self._getWastingUpdate()




    # def _getStuntingUpdate(self):
    #     stuntingProgs = self.programs['Stunting']
    #     ageGroups = self.children.ageGroups
    #     update = [program._getStuntingUpdate(ageGroups, self.newCoverages) for program in stuntingProgs]
    #     combinedUpdate = self._multiplyProgramUpdates(update)
    #     return combinedUpdate
    #
    # def _getAnaemiaUpdate(self):
    #     anaemiaProgs = self.programs['Anaemia']
    #     ageGroups = [pop.ageGroups for pop in self.allPops]
    #     update = [program._getAnaemiaUpdate(ageGroups, self.newCoverages) for program in anaemiaProgs]
    #     combined = self._multiplyProgramUpdates(update)
    #     return combined
    #
    # def _getWastingUpdate(self):
    #     wastingProgs = self.programs['Wasting']
    #     ageGroups = self.children.ageGroups
    #     update = [program._getWastingPrevalenceUpdate(ageGroups, self.newCoverages) for program in wastingProgs]
    #     combined = self._multiplyWastingUpdate(update)
    #     return combined
    #
    # def _multiplyProgramUpdates(self, update):
    #     '''Update is a list of lists, with each sub-list being updates for eacg age from a given program'''
    #     # TODO: this & the wasting version below approach should be re-thought.
    #     ageUpdate = {}
    #     for progUpdate in update:
    #         for age, value in progUpdate.iteritems():
    #             if ageUpdate.get(age) is None:
    #                 ageUpdate[age] = 1.
    #             ageUpdate[age] *= value
    #     return ageUpdate
    #
    # def _multiplyWastingUpdate(self, update):
    #     ageUpdate = {}
    #     for progUpdate in update:
    #         for age, catValue in progUpdate.iteritems():
    #             ageUpdate[age] = {}
    #             for cat, value in catValue.iteritems():
    #                 if ageUpdate[age].get(cat) is None:
    #                     ageUpdate[age][cat] = 1.
    #                 ageUpdate[age][age] *= value
    #     return ageUpdate





