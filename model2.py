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

        # TODO: this may not be the best way to do this -- make it a bit more streamlined?
        self._setInitialCoverages()

        self.year = int(self.project.year)
        self.cumulativeAgeingOutStunted = 0
        self.cumulativeBirths = 0
        # self.newCoverages = self.project.costCurveInfo['baseline coverage']
        # initialise baseline coverages
        # self._updateCoverages() # superseded by code above

    def _setInitialCoverages(self):
        """
        Convert baseline coverage to coverage metric used in model.
        Requires population sizes at time t=0.
        :return:
        """
        self.baselineCoverage = {}
        for program in self.programInfo.programs:
            program._setBaselineCoverage(self.populations)
            self.baselineCoverage[program.name] = program.restrictedBaselineCov

    def _updateCoverages(self):
        for program in self.programInfo.programs:
            program.updateCoverage(self.newCoverages[program.name], self.populations)
        self.programInfo._restrictCoverages(self.populations)


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
        for pop in self.populations: # update all the populations
            self._updatePopulation(pop)
            if pop.name == 'Children':
                # combine direct and indirect updates to each risk area that we model
                self._combineUpdates(pop) # This only needs to be called for children
            self._updateDistributions(pop)
            self._updateMortalityRates(pop)

    def _updateMortalityRates(self, pop):
        if pop.name != 'Non-pregnant women':
            pop._updateMortalityRates()

    def _getApplicablePrograms(self, risk):
        applicableProgNames = self.programInfo.programAreas[risk]
        programs = list(filter(lambda x: x.name in applicableProgNames, self.programInfo.programs))
        return programs

    def _getApplicableAgeGroups(self, population, risk):
        applicableAgeNames = population.populationAreas[risk]
        ageGroups = list(filter(lambda x: x.age in applicableAgeNames, population.ageGroups))
        return ageGroups

    def _updatePopulation(self, population): # TODO: could put all populations in here, would make for cleaner searching
        for risk in self.programInfo.programAreas.keys():
            # get relevant programs and age groups, determined by risk area
            applicableProgs = self._getApplicablePrograms(risk)
            ageGroups = self._getApplicableAgeGroups(population, risk)
            for ageGroup in ageGroups:
                for program in applicableProgs:
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
                        else:
                            print ":: Risk _{}_ not found. No update applied ::".format(risk)
                            continue

                if risk == 'Wasting treatment':
                    # need to account for flow between MAM and SAM
                    self._getFlowBetweenMAMandSAM(ageGroup)

    def _combineUpdates(self, population):
        """
        Each risk area modelled can be impacted from direct and indirect pathways, so we combine these here
        :param population:
        :return:
        """
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

    def _updateDistributions(self, population):
        """
        Uses assumption that each ageGroup in a population has a default update
        value which exists (not across populations though)
        :param ageGroup:
        :return:
        """
        if population.name == 'Children': # TODO: could map these things using a dictionary of risks with corresponding disttributions & outcomes. Then function could be made to call.
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
                for wastingCat in self.constants.wastedList:
                    oldProbThisCat = ageGroup.getFracWasted(wastingCat)
                    newProbThisCat = oldProbThisCat * ageGroup.totalWastingUpdate[wastingCat]
                    ageGroup.wastingDist[wastingCat] = newProbThisCat
                    newProbWasted += newProbThisCat
                # normality constraint on non-wasted proportions only
                nonWastedDist = ageGroup.restratify(newProbWasted)
                for nonWastedCat in self.constants.nonWastedList:
                    ageGroup.wastingDist[nonWastedCat] = nonWastedDist[nonWastedCat]
                ageGroup.redistributePopulation()
        elif population.name == 'Pregnant women':
            # update PW anaemia but also birth distribution for <1 month age group
            # update birth distribution
            newBorns = self.populations[0].ageGroups[0]
            PWpopSize = population.getTotalPopulation()
            # weighted sum accounts for different effects and target pops across PW age groups.
            for BO in self.constants.birthOutcomes:
                newBorns.birthDist[BO] *= sum(PWage.birthUpdate[BO]*PWage.populationSize for PWage in population.ageGroups) / PWpopSize
            # update anaemia distribution
            for ageGroup in population.ageGroups:
                oldProbAnaemia = ageGroup.getFracRisk('Anaemia')
                newProbAnaemia = oldProbAnaemia * ageGroup.totalAnaemiaUpdate
                ageGroup.anaemiaDist['anaemic'] = newProbAnaemia
                ageGroup.anaemiaDist['not anaemic'] = 1.-newProbAnaemia
                ageGroup.redistributePopulation()
        elif population.name == 'Non-pregnant women':
            for ageGroup in population.ageGroups:
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

    def _applyChildMortality(self):
        ageGroups = self.populations[0].ageGroups
        for ageGroup in ageGroups:
            for stuntingCat in self.constants.stuntingList:
                for wastingCat in self.constants.wastingList:
                    for bfCat in self.constants.bfList:
                        for anaemiaCat in self.constants.anaemiaList:
                            thisBox = ageGroup.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat]
                            deaths = thisBox.populationSize * thisBox.mortalityRate * self.constants.timestep # monthly deaths
                            thisBox.populationSize -= deaths
                            thisBox.cumulativeDeaths += deaths

    def _applyChildAgeing(self):
        # TODO: longer term, I think this should be re-written
        # TODO: old implementation uses boxes, but I think it is equivalent to do this with ageGroups,
        # TODO: then update boxes popsize once at end based on distribution.

        # get number ageing out of each age group
        ageGroups = self.populations[0].ageGroups
        numAgeGroups = len(ageGroups)
        ageingOut = [None] * numAgeGroups
        for idx in range(numAgeGroups):
            ageGroup = ageGroups[idx]
            ageingOut[idx] = {}
            for stuntingCat in self.constants.stuntingList:
                ageingOut[idx][stuntingCat] = {}
                for wastingCat in self.constants.wastingList:
                    ageingOut[idx][stuntingCat][wastingCat] = {}
                    for bfCat in self.constants.bfList:
                        ageingOut[idx][stuntingCat][wastingCat][bfCat] = {}
                        for anaemiaCat in self.constants.anaemiaList:
                            thisBox = ageGroup.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat]
                            ageingOut[idx][stuntingCat][wastingCat][bfCat][anaemiaCat] = thisBox.populationSize * ageGroup.ageingRate
        oldest = ageGroups[-1]
        ageingOutStunted = oldest.getNumberStunted() * oldest.ageingRate
        # ageingOutNotStunted = (oldest.populationSize - oldest.getNumberStunted()) * oldest.ageingRate # not sure if we use this
        self.cumulativeAgeingOutStunted += ageingOutStunted # TODO: this needs to be updated in Model
        # self.cumulativeAgeingOutNotStunted += ageingOutNotStunted
        # first age group does not have ageing in
        newborns = ageGroups[0]
        for stuntingCat in self.constants.stuntingList:
            for wastingCat in self.constants.wastingList:
                for bfCat in self.constants.bfList:
                    for anaemiaCat in self.constants.anaemiaList:
                        newbornBox = newborns.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat]
                        newbornBox.populationSize -= ageingOut[0][stuntingCat][wastingCat][bfCat][anaemiaCat]
        # for older age groups, account for previous stunting (binary)
        for idx in range(1, numAgeGroups):
            ageGroup = ageGroups[idx]
            numAgeingIn = {}
            numAgeingIn['stunted'] = 0.
            numAgeingIn['not stunted'] = 0.
            for prevBF in self.constants.bfList:
                for prevWT in self.constants.wastingList:
                    for prevAN in self.constants.anaemiaList:
                        numAgeingIn['stunted'] += sum(ageingOut[idx-1][stuntingCat][prevWT][prevBF][prevAN] for stuntingCat in ['high', 'moderate'])
                        numAgeingIn['not stunted'] += sum(ageingOut[idx-1][stuntingCat][prevWT][prevBF][prevAN] for stuntingCat in ['mild', 'normal'])
            # those ageing in moving into the 4 categories
            numAgeingInStratified = {}
            for stuntingCat in self.constants.stuntingList:
                numAgeingInStratified[stuntingCat] = 0.
            for prevStunt in ['stunted', 'not stunted']:
                totalProbStunted = ageGroup.probConditionalStunting[prevStunt] * ageGroup.totalStuntingUpdate # TODO:check this is correct
                restatifiedProb = ageGroup.restratify(min(1.,totalProbStunted))
                for stuntingCat in self.constants.stuntingList:
                    numAgeingInStratified[stuntingCat] += restatifiedProb[stuntingCat] * numAgeingIn[prevStunt]
            # distribute those ageing in amongst those stunting categories but also BF, wasting and anaemia
            for wastingCat in self.constants.wastingList:
                pw = ageGroup.wastingDist[wastingCat]
                for bfCat in self.constants.bfList:
                    pbf = ageGroup.bfDist[bfCat]
                    for anaemiaCat in self.constants.anaemiaList:
                        pa = ageGroup.anaemiaDist[anaemiaCat]
                        for stuntingCat in self.constants.stuntingList:
                            thisBox = ageGroup.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat]
                            thisBox.populationSize -= ageingOut[idx][stuntingCat][wastingCat][bfCat][anaemiaCat]
                            thisBox.populationSize += numAgeingInStratified[stuntingCat] * pw * pbf * pa
            # gaussianise
            probStunting = ageGroup.getStuntedFrac() # TODO; this should be impacted by change in box pops
            ageGroup.stuntingDist = ageGroup.restratify(probStunting)
            ageGroup.redistributePopulation()


    def _applyBirths(self): # TODO; re-write this function in future
        # num annual births = birth rate x num WRA x (1 - frac preg averted)
        numWRA = self.populations[2].getTotalPopulation() # TODO: best way to get total WRA pop?
        PW = self.populations[1]
        annualBirths = PW.birthRate * numWRA * (1. - PW.fracPregnancyAverted)
        # calculate total number of new babies and add to cumulative births
        numNewBabies = annualBirths * self.constants.timestep
        self.cumulativeBirths += numNewBabies
        # restratify stunting and wasting
        children = self.populations[0]
        newBorns = children.ageGroups[0]
        restratifiedStuntingAtBirth = {}
        restratifiedWastingAtBirth = {}
        for outcome in self.constants.birthOutcomes:
            totalProbStunted = children.probRiskAtBirth['Stunting'][outcome] * newBorns.totalStuntingUpdate # TODO: this has to exist before this function is called
            restratifiedStuntingAtBirth[outcome] = self.restratify(totalProbStunted)
            #wasting
            restratifiedWastingAtBirth[outcome] = {}
            probWastedAtBirth = children.probRiskAtBirth['Wasting'] # TODO: consider removing 'wasting' and just have 'sam'/mam
            totalProbWasted = 0
            # distribute proportions for wasted categories
            for wastingCat in self.constants.wastedList:
                probWastedThisCat = probWastedAtBirth[wastingCat][outcome] * newBorns.totalWastingUpdate
                restratifiedWastingAtBirth[outcome][wastingCat] = probWastedThisCat
                totalProbWasted += probWastedThisCat
            # normality constraint on non-wasted proportions
            for nonWastedCat in self.constants.nonWastedList:
                wastingDist = self.restratify(totalProbWasted)
                restratifiedWastingAtBirth[outcome][nonWastedCat] = wastingDist[nonWastedCat]
        # sum over birth outcome for full stratified stunting and wasting fractions, then apply to birth distribution
        stuntingFractions = {}
        wastingFractions = {}
        for wastingCat in self.constants.wastingList:
            wastingFractions[wastingCat] = 0.
            for outcome in self.constants.birthOutcomes:
                wastingFractions[wastingCat] += restratifiedWastingAtBirth[outcome][wastingCat] * newBorns.birthDist[outcome]
        for stuntingCat in self.constants.stuntingList:
            stuntingFractions[stuntingCat] = 0
            for outcome in self.constants.birthOutcomes:
                stuntingFractions[stuntingCat] += restratifiedStuntingAtBirth[outcome][stuntingCat] * newBorns.birthDist[outcome]
        for stuntingCat in self.constants.stuntingList:
            for wastingCat in self.constants.wastingList:
                for bfCat in self.constants.bfList:
                    pbf = newBorns.bfDist[bfCat]
                    for anaemiaCat in self.constants.anaemiaList:
                        pa = newBorns.anaemiaDist[anaemiaCat]
                        newBorns.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize += numNewBabies * \
                                                                                                     pbf * pa * \
                                                                                                     stuntingFractions[stuntingCat] * \
                                                                                                     wastingFractions[wastingCat]


    def _applyPWMortality(self):
        PW = self.populations[1]
        for ageGroup in PW.ageGroups:
            for anaemiaCat in self.constants.anaemiaList:
                thisBox = ageGroup.boxes[anaemiaCat]
                deaths = thisBox.populationSize * thisBox.mortalityRate
                thisBox.cumulativeDeaths += deaths

    def _updatePWpopulation(self):
        """Use prenancy rate to distribute PW into age groups.
        Distribute into age bands by age distribution, assumed constant over time."""
        numWRA = self.populations[2].getTotalPopulation()
        PW = self.populations[1]
        PWpop = PW.pregnancyRate * numWRA * (1. - PW.fracPregnancyAverted)
        for ageGroup in PW.ageGroups:
            popSize = PWpop * self.constants.PWageDistribution[ageGroup.age] # TODO: could put this in PW age groups for easy access
            for anaemiaCat in self.constants.anaemiaList:
                thisBox = ageGroup.boxes[anaemiaCat]
                thisBox.populationSize = popSize * ageGroup.anaemiaDist[anaemiaCat]

    def _updateWRApopulation(self):
        """Uses projected figures to determine the population of WRA not pregnant in a given age band and year
        warning: PW pop must be updated first."""
        #assuming WRA and PW have same age bands
        WRA = self.populations[2]
        ageGroups = WRA.ageGroups
        for idx in range(len(ageGroups)):
            ageGroup = ageGroups[idx]
            projectedWRApop = self.constants.popProjections[ageGroup.age][self.year]
            PWpop = self.populations[1].ageGroups[idx].populationSize
            nonPW = projectedWRApop - PWpop
            #distribute over risk factors
            for anaemiaCat in self.constants.anaemiaList:
                thisBox = ageGroup.boxes[anaemiaCat]
                thisBox.populationSize = nonPW * ageGroup.anaemiaDist[anaemiaCat]

    def restratify(self, fractionYes):
        # Going from binary stunting/wasting to four fractions
        # Yes refers to more than 2 standard deviations below the global mean/median
        # in our notes, fractionYes = alpha
        from scipy.stats import norm
        invCDFalpha = norm.ppf(fractionYes)
        fractionHigh     = norm.cdf(invCDFalpha - 1.)
        fractionModerate = fractionYes - norm.cdf(invCDFalpha - 1.)
        fractionMild     = norm.cdf(invCDFalpha + 1.) - fractionYes
        fractionNormal   = 1. - norm.cdf(invCDFalpha + 1.)
        restratification = {}
        restratification["normal"] = fractionNormal
        restratification["mild"] = fractionMild
        restratification["moderate"] = fractionModerate
        restratification["high"] = fractionHigh
        return restratification

    def moveModelOneTimeStep(self):
        """
        Responsible for updating children since they have monthly time steps
        :return:
        """
        self._applyChildMortality()
        self._applyChildAgeing()
        self._applyBirths()
        # self.updateRiskDistributions() # TODO: don't think I need this b/c distributions already updated (stored in age groups)

    def moveModelOneYear(self):
        """
        Responsible for updating all populations
        :return:
        """
        self.year += 1
        for month in range(12):
            self.moveModelOneTimeStep()
        self._applyPWMortality()
        self._updatePWpopulation()
        self._updateWRApopulation()
        # self.updateYearlyRiskDistributions() # TODO: don't think I need this






