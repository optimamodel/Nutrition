from copy import deepcopy as dcp
class Model:
    def __init__(self, filePath):
        import data2 as data
        import populations2 as pops
        import program_info
        from constants import Constants
        self.project = data.setUpProject(filePath) # one modification comes below for IYCF target pops
        self.constants = Constants(self.project)
        self.populations = pops.setUpPopulations(self.project, self.constants)
        #self._setIYCFtargetPop(self.populations) # TODO: This is not complete
        self.programInfo = program_info.ProgramInfo(self.constants)

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
            # combine direct and indirect updates to each risk area that we model
            self._combineUpdates(pop) # This only needs to be called for children
            self._updateDistributions(pop) # TODO: remember to move the population around after updating distributions

    def _getApplicablePrograms(self, risk):
        applicableProgNames = self.programInfo.programAreas[risk]
        programs = list(filter(lambda x: x.name in applicableProgNames, self.programInfo.programs))
        return programs

    def _combineUpdates(self, population):
        """
        Each risk area modelled can be impacted from direct and indirect pathways, so we combine these here
        :param population:
        :return:
        """
        if population.name is 'Children':
            for ageGroup in population.ageGroups:
                # stunting: direct, diarrhoea, breatfeeding
                ageGroup.totalStuntingUpdate = ageGroup.stuntingUpdate * ageGroup.diarrhoeaUpdate['Stunting'] \
                                               * ageGroup.bfUpdate['Stunting']
                # anaemia: direct, diarrhoea, breastfeeding
                ageGroup.totalAnaemiaUpdate = ageGroup.anaemiaUpdate * ageGroup.diarrhoeaUpdate['Anaemia'] \
                                              * ageGroup.bfUpdate['Anaemia']
                # wasting: direct (prevalence, incidence), flow between MAM & SAM, diarrhoea, breastfeeding
                ageGroup.totalWastingUpdate = {}
                for wastingCat in self.constants.wastedList:
                    ageGroup.totalWastingUpdate[wastingCat] = ageGroup.wastingTreatmentUpdate[wastingCat] \
                                                  * ageGroup.wastingPreventionUpdate[wastingCat] \
                                                  * ageGroup.bfUpdate[wastingCat] \
                                                  * ageGroup.diarrhoeaUpdate[wastingCat] \
                                                  * ageGroup.fromMAMtoSAMupdate[wastingCat] \
                                                  * ageGroup.fromSAMtoMAMupdate[wastingCat]
        # elif population.name is 'Pregnant women': # only anaemia





    def _updateDistributions(self, population):
        """
        Uses assumption that each ageGroup in a population has a default update
        value which exists (not across populations though)
        :param ageGroup:
        :return:
        """
        if population.name is 'Children':
            for ageGroup in population.ageGroups:
                # mortality
                for cause in self.constants.causesOfDeath:
                    ageGroup.referenceMortality[cause] *= ageGroup.mortalityUpdate[cause]
                # stunting
                oldProbStunting = ageGroup.getFracRisk('Stunting')
                newProbStunting = oldProbStunting * ageGroup.totalStuntingUpdate
                ageGroup.stuntingDist = ageGroup.restratify(newProbStunting)
                # anaemia
                oldProbAnaemia = ageGroup.getFracRisk('Anaemia')
                newProbAnaemia = oldProbAnaemia * ageGroup.totalAnaemiaUpdate
                ageGroup.anaemiaDist['anaemic'] = newProbAnaemia
                ageGroup.anaemiaDist['not anaemic'] = 1.-newProbAnaemia
                # wasting
                newProbWasted = 0.
                for wastingCat in self.constants.wastedList: # TODO: does order of SAM/MAM matter? Check distribution update
                    oldProbThisCat = ageGroup.getFracWasted(wastingCat)
                    newProbThisCat = oldProbThisCat * ageGroup.totalWastingUpdate[wastingCat]
                    ageGroup.wastingDist[wastingCat] = newProbThisCat
                    newProbWasted += newProbThisCat
                # normality constraint on non-wasted proportions only
                nonWastedDist = ageGroup.restratify(newProbWasted)
                for nonWastedCat in self.constants.nonWastedList:
                    ageGroup.wastingDist[nonWastedCat] = nonWastedDist[nonWastedCat]
                ageGroup.redistributePopulation()
                # birth outcomes
                # each ageGroup needs access to the distribution for 'updateMortalityRate()', so need to update for each
                for BO in self.constants.birthOutcomes:
                    ageGroup.birthDist[BO] *= ageGroup.birthUpdate[BO]
                ageGroup.birthDist['Term AGA'] = 1. - sum(ageGroup.birthDist[BO]
                                                          for BO in self.constants.birthOutcomes if BO is not 'Term AGA')
        else: # PW or non-PW -- anaemia only
            for ageGroup in population.ageGroups:
                # TODO: this update is exactly the same as for children -- make function?
                oldProbAnaemia = ageGroup.getFracRisk('Anaemia')
                newProbAnaemia = oldProbAnaemia * ageGroup.totalAnaemiaUpdate
                ageGroup.anaemiaDist['anaemic'] = newProbAnaemia
                ageGroup.anaemiaDist['not anaemic'] = 1.-newProbAnaemia
                ageGroup.redistributePopulation()

    def _getFlowBetweenMAMandSAM(self, ageGroup):
        fromSAMtoMAMupdate = {}
        fromMAMtoSAMupdate = {}
        fracMovingOut = {}
        fracMovingOut['MAM'] = self.constants.demographics['fraction MAM to SAM']
        fracMovingOut['SAM'] = self.constants.demographics['fraction SAM to MAM']
        for wastingCat in self.constants.wastedList:
            if wastingCat == 'MAM':
                fromSAMtoMAMupdate[wastingCat] = (1. + (1. - ageGroup.wastingTreatmentUpdate[wastingCat]) * fracMovingOut[wastingCat])
                fromMAMtoSAMupdate[wastingCat] = 1.
            elif wastingCat == 'SAM':
                fromSAMtoMAMupdate[wastingCat] = 1.
                fromMAMtoSAMupdate[wastingCat] = (1. + (1. - ageGroup.wastingTreatmentUpdate[wastingCat]) * fracMovingOut[wastingCat])
        ageGroup.fromSAMtoMAMupdate = fromSAMtoMAMupdate
        ageGroup.fromMAMtoSAMupdate = fromMAMtoSAMupdate

    def _updatePopulation(self, population):
        for risk in self.programInfo.programAreas.keys():
            # get relevant programs, determined by risk area
            applicableProgs = self._getApplicablePrograms(risk)
            for ageGroup in population.ageGroups:
                for program in applicableProgs:
                    if ageGroup.age in program.relevantAges:
                        if risk == 'Stunting':
                            program._getStuntingUpdate(ageGroup)
                        elif risk == 'Anaemia':
                            program._getAnaemiaUpdate(ageGroup)
                        elif risk == 'Wasting prevention':
                            program._getWastingPreventionUpdate(ageGroup)
                        elif risk == 'Wasting treatment':
                            program._getWastingTreatmentUpdate(ageGroup)
                        elif risk == 'Breastfeeding':
                            program._getBreastfeedingupdate(ageGroup)
                        elif risk == 'Diarrhoea':
                            program._getDiarrhoeaUpdate(ageGroup)
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
                if risk == 'Wasting treatment':
                    # need to account for flow between MAM and SAM
                    self._getFlowBetweenMAMandSAM(ageGroup)


                # TODO: need to update distributions etc here.
                # TODO: update mortality
                # UPDATE STUNTING DISTRIBUTION
                # oldProbStunting = ageGroup.getFracRisk(risk)
                # newProbStunting = oldProbStunting * update
                # ageGroup.restratify(newProbStunting) # write this
                # redistribute population based on new distribution
                # ageGroup.redistribute() # use distributions of ageGroups











