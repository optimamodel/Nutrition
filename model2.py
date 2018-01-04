from copy import deepcopy as dcp
class Model:
    def __init__(self, filePath):
        import data2 as data
        import populations2 as pops
        import program_info
        self.project = data.setUpProject(filePath) # one modification comes below for IYCF target pops
        self.populations = pops.setUpPopulations(self.project)
        #self._setIYCFtargetPop(self.populations) # TODO: This is not complete
        self.programInfo = program_info.ProgramInfo(self.project)

        self.year = int(self.project.year)
        self.newCoverages = self.project.costCurveInfo['baseline coverage']
        # initialise baseline coverages
        self._updateCoverages()

    def _updateCoverages(self):
        for program in self.programInfo.programs:
            program.updateCoverage(self.newCoverages[program.name], self.populations)

    # TODO: TBC
    def _setIYCFtargetPop(self, populations):
        """
        This method is placed here because population sizes are required for these calculations,
        but are unknown until the population classes are initialised.
        :return:
        """
        # get pop sizs for children & PW
        allPopSizes = {}
        for pop in populations[:2]: # TODO: make this a method in populations.py
            allPopSizes.update({age.name:age.populationSize for age in pop.ageGroups})
        targetPop = self.project.IYCFtargetPop
        # equation: maxCovIYCF = sum(popSize * fracExposed) / sum(popSize)
        # TODO: want this to be stratified by age (not mode)
        # TODO: this calculation would be sum(fracExposed)/numModes (trivial case of more general equation).
        maxCov = {}
        for name, package in targetPop.iteritems():
            maxCov[name] = 0.
            for pop, modeFrac in package.iteritems():
                for mode, frac in modeFrac.iteritems():
                    maxCov[name] += frac * allPopSizes[pop] # TODO: should probably convert this to fraction (?)
        # update in project
        self.project.programTargetPop.update(maxCov)



    def applyNewProgramCoverages(self, newCoverages):
        '''newCoverages is required to be the overall coverage % (i.e. people covered / entire target pop) '''
        self.newCoverages = dcp(newCoverages)
        self._updateCoverages()
        for pop in self.populations[:1]: # update all the populations # TODO: UNDO SPLICING
            self._updatePopulation(pop)

    def _getApplicablePrograms(self, risk):
        applicableProgNames = self.programInfo.programAreas[risk]
        programs = list(filter(lambda x: x.name in applicableProgNames, self.programInfo.programs))
        return programs

    def _combineUpdates(self, updates, risk):
        pass

    def _updateDistributions(self, totalUpdate, risk):
        pass

    def _updatePopulation(self, population):
        for risk in self.programInfo.programAreas.keys():
            # get relevant programs, determined by risk area
            applicableProgs = self._getApplicablePrograms(risk)
            for ageGroup in population.ageGroups:
                updates = []
                for program in applicableProgs:
                    if ageGroup.name in program.relevantAges:
                        if risk == 'Stunting':
                            program._getStuntingUpdate(ageGroup)
                        elif risk == 'Anaemia':
                            program._getAnaemiaUpdate(ageGroup)
                        elif risk == 'Wasting prevention':
                            program._getWastingUpdateFromWastingIncidence(ageGroup)
                        elif risk == 'Wasting treatment':
                            program._getWastingPrevalenceUpdate(ageGroup)
                        # elif risk == 'Breastfeeding':


                        # elif risk == 'Diarrhoea':
                        elif risk == 'Mortality':
                            program._getMortalityUpdate(ageGroup)
                        elif risk == 'Birth outcomes':
                            program._getBirthOutcomeUpdate(ageGroup)
                        # elif risk == 'Family planning':
                        elif risk == 'None':
                            continue
                        else:
                            print ":: Risk _{}_ not found. No update applied ::".format(risk)
                            continue
                    else:
                        continue

                # AT THIS POINT THIS AGE GROUP WILL HAVE THE TOTAL UPDATE FOR A PARTICULAR RISK
                # TODO: combine the updates above in a Model method which also updates distributions
                totalUpdate = self._combineUpdates(updates, risk) # TODO: here we can account for MAMtoSAM & SAMtoMAM updates for wasting
                self._updateDistributions(totalUpdate, risk)

                # TODO: need to update distributions etc here.
                # TODO: update mortality
                # UPDATE STUNTING DISTRIBUTION
                # oldProbStunting = ageGroup.getFracRisk(risk)
                # newProbStunting = oldProbStunting * update
                # ageGroup.restratify(newProbStunting) # write this
                # redistribute population based on new distribution
                # ageGroup.redistribute() # use distributions of ageGroups











