from copy import deepcopy as dcp
from scipy.stats import norm
class Model:
    def __init__(self, filePath):
        import data2 as data
        import populations2 as pops
        import program_info
        from constants import Constants
        self.project = data.setUpProject(filePath) # one modification comes below for IYCF target pops
        self.constants = Constants(self.project)
        self.programInfo = program_info.ProgramInfo(self.constants)
        self.populations = pops.setUpPopulations(self.project, self.constants)
        # caution: maintain order below
        # use populations to adjust the baseline coverage
        self.programInfo._setBaselineCov(self.populations)
        # use adjusted coverages to calculate conditional probabilities
        # self._setConditionalProbabilities()

        #self._setIYCFtargetPop(self.populations) # TODO: This is not complete

        # self._setInitialCoverages()

        self.year = int(self.project.year)
        self.cumulativeAgeingOutStunted = 0
        self.cumulativeThrive = 0
        self.cumulativeBirths = 0
        self.cumulativeDeaths = 0
        # self.newCoverages = self.project.costCurveInfo['baseline coverage']
        # initialise baseline coverages
        # self._updateCoverages() # superseded by code above

    def _setConditionalProbabilities(self, population):
        population.baselineCovs = self.programInfo.baselineCovs # pop has access to adjusted baseline cov
        population._setConditionalProbabilities()

    # def _setInitialCoverages(self):
    #     """
    #     Convert baseline coverage to coverage metric used in model.
    #     Requires population sizes at time t=0.
    #     :return:
    #     """
    #     self.baselineCoverage = {}
    #     for program in self.programInfo.programs:
    #         program._setBaselineCoverage(self.populations)
    #         self.baselineCoverage[program.name] = program.restrictedBaselineCov

    def _updateCoverages(self, newCoverages):
        for program in self.programInfo.programs:
            program.updateCoverageTMP(newCoverages[program.name], self.populations) # TODO: USING TMP JUST FOR TESTING
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
        '''newCoverages is required to be the unrestricted coverage % (i.e. people covered / entire target pop) '''
        self._updateCoverages(newCoverages) # TODO: change the call in here
        for pop in self.populations[:1]:
            # update probabilities using current risk distributions
            self._setConditionalProbabilities(pop)
        for pop in self.populations[:1]: # update all the populations
            self._updatePopulation(pop)
            # combine direct and indirect updates to each risk area that we model
            self._combineUpdates(pop)
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

    def _updatePopulation(self, population):
        for risk in self.programInfo.programAreas.keys():
            # get relevant programs and age groups, determined by risk area
            applicableProgs = self._getApplicablePrograms(risk)
            ageGroups = self._getApplicableAgeGroups(population, risk)
            for ageGroup in ageGroups:
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
                            program._getDiarrhoeaIncidenceUpdate(ageGroup)
                        elif risk == 'Mortality':
                            program._getMortalityUpdate(ageGroup)
                        elif risk == 'Birth outcomes':
                            program._getBirthOutcomeUpdate(ageGroup)
                        elif risk == 'Family planning':
                            program._getFamilyPlanningUpdate(ageGroup)
                        # elif risk == 'Birth age': # TODO: change implementation from previous mode version -- Calculate probabilities using RR etc.
                        #     program._getBirthAgeUpdate(ageGroup)
                        else:
                            print ":: Risk _{}_ not found. No update applied ::".format(risk)
                            continue
                    else:
                        continue
                # TODO: put diarrhoea update down here??
                if risk == 'Breastfeeding':  # flow on effects to diarrhoea (does not diarrhoea incidence & is independent of below)
                    self._getEffectsFromBFupdate(ageGroup)
                if risk == 'Diarrhoea': # flow-on effects from incidence
                    self._getEffectsFromDiarrhoeaIncidence(ageGroup)
                if risk == 'Wasting treatment':
                    # need to account for flow between MAM and SAM
                    self._getFlowBetweenMAMandSAM(ageGroup)

    def _combineUpdates(self, population):
        """
        Each risk area modelled can be impacted from direct and indirect pathways, so we combine these here
        :param population:
        :return:
        """
        if population.name == 'Children':
            for ageGroup in population.ageGroups:
                # stunting: direct, diarrhoea, breastfeeding
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
        elif population.name == 'Pregnant women':
            for ageGroup in population.ageGroups:
                ageGroup.totalAnaemiaUpdate = ageGroup.anaemiaUpdate
        elif population.name == 'Non-pregnant women':
            for ageGroup in population.ageGroups:
                ageGroup.totalAnaemiaUpdate = ageGroup.anaemiaUpdate
                ageGroup.totalFPUpdate = ageGroup.FPupdate
                ageGroup.totalBAUpdate = ageGroup.birthAgeUpdate

    def _updateDistributions(self, population):
        """
        Uses assumption that each ageGroup in a population has a default update
        value which exists (not across populations though)
        :param ageGroup:
        :return:
        """
        if population.name == 'Children': # TODO: could map these things using a dictionary of risks with corresponding distributions & outcomes. Then function could be made to call.
            for ageGroup in population.ageGroups:
                for cause in self.constants.causesOfDeath:
                    ageGroup.referenceMortality[cause] *= ageGroup.mortalityUpdate[cause]
                # stunting
                oldProbStunting = ageGroup.getFracRisk('Stunting')
                newProbStunting = oldProbStunting * ageGroup.totalStuntingUpdate # TODO: what happens when this results in prob > 1?
                ageGroup.stuntingDist = self.restratify(newProbStunting)
                ageGroup.redistributePopulation()
                # anaemia
                oldProbAnaemia = ageGroup.getFracRisk('Anaemia')
                newProbAnaemia = oldProbAnaemia * ageGroup.totalAnaemiaUpdate
                ageGroup.anaemiaDist['anaemic'] = newProbAnaemia
                ageGroup.anaemiaDist['not anaemic'] = 1.-newProbAnaemia
                # wasting
                newProbWasted = 0.
                for wastingCat in ['SAM', 'MAM']:
                    oldProbThisCat = ageGroup.getWastedFrac(wastingCat)
                    newProbThisCat = oldProbThisCat * ageGroup.totalWastingUpdate[wastingCat]
                    ageGroup.wastingDist[wastingCat] = newProbThisCat
                    newProbWasted += newProbThisCat
                # normality constraint on non-wasted proportions only
                nonWastedDist = self.restratify(newProbWasted)
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
                newBorns.birthDist[BO] *= sum(PWage.birthUpdate[BO]*PWage.getAgeGroupPopulation() for PWage in population.ageGroups) / PWpopSize
            # update anaemia distribution
            for ageGroup in population.ageGroups:
                oldProbAnaemia = ageGroup.getFracRisk('Anaemia')
                newProbAnaemia = oldProbAnaemia * ageGroup.totalAnaemiaUpdate
                ageGroup.anaemiaDist['anaemic'] = newProbAnaemia
                ageGroup.anaemiaDist['not anaemic'] = 1.-newProbAnaemia
                ageGroup.redistributePopulation()
        elif population.name == 'Non-pregnant women':
            for ageGroup in population.ageGroups:
                # anaemia
                oldProbAnaemia = ageGroup.getFracRisk('Anaemia')
                newProbAnaemia = oldProbAnaemia * ageGroup.totalAnaemiaUpdate
                ageGroup.anaemiaDist['anaemic'] = newProbAnaemia
                ageGroup.anaemiaDist['not anaemic'] = 1.-newProbAnaemia
                ageGroup.redistributePopulation()
            # weighted sum account for different effect and target pops across nonPW age groups # TODO: is this true or need to scale by frac targeted?
            nonPWpop = population.getTotalPopulation()
            # FPcov = sum(nonPWage.FPupdate * nonPWage.getAgeGroupPopulation() for nonPWage in population.ageGroups) / nonPWpop
            # population._updateFracPregnancyAverted(FPcov)

    def _getFlowBetweenMAMandSAM(self, ageGroup):
        ageGroup.fromSAMtoMAMupdate = {}
        ageGroup.fromMAMtoSAMupdate = {}
        ageGroup.fromSAMtoMAMupdate['MAM'] = (1. + (1.-ageGroup.wastingTreatmentUpdate['SAM']) * self.constants.demographics['fraction SAM to MAM'])
        ageGroup.fromSAMtoMAMupdate['SAM'] = 1.
        ageGroup.fromMAMtoSAMupdate['SAM'] = (1. - (1.-ageGroup.wastingTreatmentUpdate['MAM']) * self.constants.demographics['fraction MAM to SAM'])
        ageGroup.fromMAMtoSAMupdate['MAM'] = 1.

    def _getEffectsFromDiarrhoeaIncidence(self, ageGroup):
        # get flow-on effects to stunting, anaemia and wasting
        Z0 = ageGroup._getZa()
        ageGroup.incidences['Diarrhoea'] *= ageGroup.diarrhoeaIncidenceUpdate
        Zt = ageGroup._getZa() # updated incidence
        beta = ageGroup._getFracDiarrhoea(Z0, Zt)
        ageGroup._updateProbConditionalDiarrhoea(Zt)
        for risk in ['Stunting', 'Anaemia']:
            ageGroup.diarrhoeaUpdate[risk] *= self._getUpdatesFromDiarrhoeaIncidence(beta, ageGroup, risk)
        wastingUpdate = self._getWastingUpdateFromDiarrhoea(beta, ageGroup)
        for wastingCat in self.constants.wastedList:
            ageGroup.diarrhoeaUpdate[wastingCat] *= wastingUpdate[wastingCat]

    def _getEffectsFromBFupdate(self, ageGroup):
        # get number at risk before
        sumBefore = ageGroup._getDiarrhoeaRiskSum()
        # update correct BF distribution
        ageGroup.bfDist[ageGroup.correctBF] *= ageGroup.bfPracticeUpdate
        # update distribution of incorrect practices
        popSize = ageGroup.getAgeGroupPopulation()
        numCorrectBefore = ageGroup.getNumberCorrectlyBF()
        numCorrectAfter = popSize * ageGroup.bfDist[ageGroup.correctBF]
        numShifting = numCorrectAfter - numCorrectBefore
        numIncorrectBefore = popSize - numCorrectBefore
        fracCorrecting = numShifting / numIncorrectBefore if numIncorrectBefore > 0.01 else 0.
        for practice in ageGroup.incorrectBF:
            ageGroup.bfDist[practice] *= 1. - fracCorrecting
        ageGroup.redistributePopulation()
        # number at risk after
        sumAfter = ageGroup._getDiarrhoeaRiskSum()
        # update diarrhoea incidence baseline, even though not directly used in this calculation
        ageGroup.incidences['Diarrhoea'] *= sumAfter / sumBefore
        beta = ageGroup._getFracDiarrhoeaFixedZ()  # TODO: this could probably be calculated prior to update coverages
        for risk in ['Stunting', 'Anaemia']:
            ageGroup.bfUpdate[risk] = self._getUpdatesFromDiarrhoeaIncidence(beta, ageGroup, risk)
        ageGroup.bfUpdate.update(self._getWastingUpdateFromDiarrhoea(beta, ageGroup))

    def _getUpdatesFromDiarrhoeaIncidence(self, beta, ageGroup, risk):
        oldProb = ageGroup.getRiskFromDist(risk)
        newProb = 0.
        probThisRisk = ageGroup.probConditionalDiarrhoea[risk]
        for bfCat in ageGroup.const.bfList:
            pab = ageGroup.bfDist[bfCat]
            t1 = beta[bfCat] * probThisRisk['diarrhoea']
            t2 = (1.-beta[bfCat]) * probThisRisk['no diarrhoea']
            newProb += pab * (t1 + t2)
        reduction = (oldProb - newProb) / oldProb
        update = 1. - reduction
        return update

    def _getWastingUpdateFromDiarrhoea(self, beta, ageGroup):
        update = {}
        for wastingCat in self.constants.wastedList:
            update[wastingCat] = 1.
            probWasted = ageGroup.probConditionalDiarrhoea[wastingCat]
            oldProb = ageGroup.wastingDist[wastingCat]
            newProb = 0.
            for bfCat in self.constants.bfList:
                pab = ageGroup.bfDist[bfCat]
                t1 = beta[bfCat] * probWasted['diarrhoea']
                t2 = (1.-beta[bfCat]) * probWasted['no diarrhoea']
                newProb += pab*(t1+t2)
            reduction = (oldProb - newProb)/oldProb
            update[wastingCat] *= 1. - reduction
        return update

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
                            self.cumulativeDeaths += deaths

    def _applyChildAgeing(self):
        # TODO: longer term, I think this should be re-written
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
        ageingOutStunted = oldest.getAgeGroupNumberStunted() * oldest.ageingRate
        ageingOutNotStunted = oldest.getAgeGroupNumberNotStunted() * oldest.ageingRate
        self.cumulativeAgeingOutStunted += ageingOutStunted
        self.cumulativeThrive += ageingOutNotStunted
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
                restratifiedProb = self.restratify(totalProbStunted)
                for stuntingCat in self.constants.stuntingList:
                    numAgeingInStratified[stuntingCat] += restratifiedProb[stuntingCat] * numAgeingIn[prevStunt]
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
            distributionNow = ageGroup.getStuntingDistribution()
            probStunting = sum(distributionNow[stuntingCat] for stuntingCat in self.constants.stuntedList)
            ageGroup.stuntingDist = self.restratify(probStunting)
            ageGroup.redistributePopulation()

    def _applyBirths(self): # TODO; re-write this function in future
        # num annual births = birth rate x num WRA x (1 - frac preg averted)
        nonPW = self.populations[2]
        numWRA = self.populations[2].getTotalPopulation() # TODO: best way to get total WRA pop? COULD BE WRONG
        PW = self.populations[1]
        annualBirths = nonPW.birthRate * numWRA * (1. - nonPW.fracPregnancyAverted)
        # calculate total number of new babies and add to cumulative births
        numNewBabies = annualBirths * self.constants.timestep
        self.cumulativeBirths += numNewBabies
        # restratify stunting and wasting
        newBorns = self.populations[0].ageGroups[0]
        restratifiedStuntingAtBirth = {}
        restratifiedWastingAtBirth = {}
        for outcome in self.constants.birthOutcomes:
            totalProbStunted = newBorns.probRiskAtBirth['Stunting'][outcome] * newBorns.totalStuntingUpdate
            restratifiedStuntingAtBirth[outcome] = self.restratify(totalProbStunted)
            #wasting
            restratifiedWastingAtBirth[outcome] = {}
            probWastedAtBirth = newBorns.probRiskAtBirth['Wasting'] # TODO: consider removing 'wasting' and just have 'sam'/mam
            totalProbWasted = 0
            # distribute proportions for wasted categories
            for wastingCat in self.constants.wastedList:
                probWastedThisCat = probWastedAtBirth[wastingCat][outcome] * newBorns.totalWastingUpdate[wastingCat]
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
        nonPW = self.populations[2]
        numWRA = self.populations[2].getTotalPopulation()
        PW = self.populations[1]
        PWpop = nonPW.pregnancyRate * numWRA * (1. - nonPW.fracPregnancyAverted)
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
            PWpop = self.populations[1].ageGroups[idx].getAgeGroupPopulation()
            nonPW = projectedWRApop - PWpop
            #distribute over risk factors
            for anaemiaCat in self.constants.anaemiaList:
                thisBox = ageGroup.boxes[anaemiaCat]
                thisBox.populationSize = nonPW * ageGroup.anaemiaDist[anaemiaCat]

    def restratify(self, fractionYes):
        # Going from binary stunting/wasting to four fractions
        # Yes refers to more than 2 standard deviations below the global mean/median
        # in our notes, fractionYes = alpha
        if fractionYes > 1:
            fractionYes = 1
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


    def updateRiskDists(self):
        for ageGroup in self.populations[0].ageGroups:
            ageGroup.updateStuntingDist()
            ageGroup.updateWastingDist()
            ageGroup.updateBFDist()
            ageGroup.updateAnaemiaDist()

    def updateYearlyRiskDists(self):
        for pop in self.populations[1:]:
            for ageGroup in pop.ageGroups:
                ageGroup.updateAnaemiaDist()

    def moveModelOneTimeStep(self):
        """
        Responsible for updating children since they have monthly time steps
        :return:
        """
        self._applyChildMortality()
        self._applyChildAgeing()
        self._applyBirths()
        self.updateRiskDists()

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
        self.updateYearlyRiskDists()

    def getOutcome(self, outcome):
        if outcome == 'total stunted':
            return self.cumulativeAgeingOutStunted
        elif outcome == 'stunting prev':
            return self.populations[0].getTotalFracStunted()
        elif outcome == 'thrive':
            return self.cumulativeThrive
        elif outcome == 'child deaths':
            return self.cumulativeDeaths







