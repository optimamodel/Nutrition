from copy import deepcopy as dcp
from numpy import exp, log

class Program(object):
    '''Each instance of this class is an intervention,
    and all necessary data will be stored as attributes. Will store name, targetpop, popsize, coverage, edges etc
    Also want it to set absolute number covered, coverage frac (coverage amongst entire pop), normalised coverage (coverage amongst target pop)'''
    def __init__(self, name, project):
        self.name = name
        self.project = dcp(project)
        self.ages = self.project.childAges + self.project.PWages + self.project.WRAages

        self.baselineCoverage = self.project.costCurveInfo['baseline coverage'][self.name]
        self.targetPopulations = self.project.programTargetPop[self.name] # frac of each population which is targeted
        self.unitCost = self.project.costCurveInfo['unit cost'][self.name] # TODO: consider putting these in and retrieving from the Constants class
        self.saturation = self.project.costCurveInfo['saturation'][self.name]

        self._setRelevantAges()
        self._setExclusionDependencies()
        self._setThresholdDependencies()
        self._setCostCoverageCurve()

    def updateCoverage(self, newCoverage, populations):
        """Update all values pertaining to coverage for a program"""
        self.proposedCoverageNum = newCoverage
        self._setUnrestrictedPopSize(populations)
        self._setRestrictedPopSize(populations)
        self.proposedCoverageFrac = self.proposedCoverageNum / self.unrestrictedPopSize

    def _setRelevantAges(self):
        """
        Construct list which contains only those age groups to which this program applies
        :return:
        """
        self.relevantAges = []
        for age in self.ages:
            fracTargeted = self.targetPopulations[age]
            if fracTargeted > 0.001: # floating point tolerance
                self.relevantAges.append(age)

    def _setUnrestrictedPopSize(self, populations):
        """
        sum of the total pop for each targeted age group
        """
        self.unrestrictedPopSize = 0.
        for pop in populations:
            self.unrestrictedPopSize += sum(age.populationSize for age in pop.ageGroups
                                           if age.name in self.relevantAges)

    def _setRestrictedPopSize(self, populations):
        self.restrictedPopSize = 0.
        for pop in populations:
            self.restrictedPopSize += sum(age.populationSize * self.targetPopulations[age.name] for age in pop.ageGroups
                                         if age.name in self.relevantAges )

    def _setExclusionDependencies(self):
        """
        List containing the names of programs which restrict the coverage of this program to (1 - coverage of independent program)
        :return:
        """
        self.exclusionDepedencies = []
        dependencies = self.project.programDependency[self.name]['Exclusion dependency']
        for program in dependencies:
            self.exclusionDepedencies.append(program)

    def _setThresholdDependencies(self):
        """
        List containing the name of programs which restrict the coverage of this program to coverage of independent program
        :return:
        """
        self.thresholdDependencies = []
        dependencies = self.project.programDependency[self.name]['Threshold dependency']
        for program in dependencies:
            self.thresholdDependencies.append(program)

    def _setCostCurve(self):
        """
        Sets the cost-coverage curve of this program as a lambda function
        :return:
        """
        self.costCurve = None # TODO: set this

    def _getStuntingUpdate(self, ageGroup):
        """
        Will get the total stunting update for a single program.
        Since we assume independence between each kind of stunting update
        and across programs (that is, after we have accounted for dependencies),
        the order of multiplication of updates does not matter.
        """
        ageGroup.stuntingUpdate *= self._getConditionalProbUpdate(ageGroup, 'Stunting')

    def _getAnaemiaUpdate(self, ageGroup):
        """
        Program which directly impact anaemia.
        :param ageGroup: instance of AgeGroup class
        """
        ageGroup.anaemiaUpdate *= self._getConditionalProbUpdate(ageGroup, 'Anaemia')

    def _getWastingUpdate(self, ageGroup):
        """
        Programs which directly impact wasting prevalence or incidence.
        Wasting update is comprised of two parts:
            1. Prevention interventions, which alter the incidence of wasting
            2. Treatment interventions, which alter the prevalence of wasting
        Update of type 1. is converted into a prevalence update.
        The total update is the product of these two.
        :param ageGroup:
        :return:
        """
        prevUpdate = self._getWastingPrevalenceUpdate(ageGroup)
        incidUpdate = self._getWastingUpdateFromWastingIncidence(ageGroup)
        for wastingCat in ['MAM', 'SAM']:
            combined = prevUpdate[wastingCat] * incidUpdate[wastingCat]
            ageGroup.wastingUpdate[wastingCat] *= combined


    def _getDiarrhoeaUpdate(self, ageGroup):
        """
        This function accounts for the _direct_ impact of programs on diarrhoea incidence
        :param ageGroup:
        :return:
        """
        update = self._getEffectivenessUpdate(ageGroup, 'Effectiveness incidence')
        newIncidence = ageGroup.incidences['Diarrhoea'] * update
        # get flow-on effects to stunting, anaemia and wasting
        Z0 = ageGroup._getZa(ageGroup.incidences['Diarrhoea']) # TODO: currently in children class, would like it in ageGroup class
        Zt = ageGroup._getZa(newIncidence)
        beta = ageGroup.getFracDiarrhoea(Z0, Zt)
        ageGroup.updateProbConditionalDiarrhoea(Zt) # TODO: make this a method of ageGroup
        for risk in ['Stunting', 'Anaemia']:
            ageGroup.diarrhoeaUpdate[risk] *= self._getUpdatesFromDiarrhoeaIncidence(beta, ageGroup, risk)
        ageGroup.diarrhoeaUpdate['Wasting'] *= self._getWastingUpdateFromDiarrhoea(beta, ageGroup)

    def _getBreastfeedingupdate(self, ageGroup):
        """
        Accounts for the program's direct impact on breastfeeding practices
        :param ageGroup:
        :return:
        """
        # TODO: do we even need to consider incidence here at all??
        update = self._getBFpracticeUpdate(ageGroup)
        # update correct BF distribution
        ageGroup.bfDist[ageGroup.correctBF] = update
        # update distribution of incorrect practices
        popSize = ageGroup.populationSize
        numCorrectBefore = ageGroup.getNumberCorrectlyBF()
        numCorrectAfter = popSize * update
        numShifting = numCorrectAfter - numCorrectBefore
        numIncorrectBefore = popSize - numCorrectBefore
        fracCorrecting = numShifting / numIncorrectBefore if numIncorrectBefore > 0.01 else 0.
        for practice in ageGroup.incorrectBF:
            ageGroup.bfDist[practice] *= 1. - fracCorrecting
        ageGroup.redistributePopulation()
        # TODO: not updating diarrhoea incidence here b/c not sure if necessary
        beta = ageGroup._getFracDiarrhoeaFixedZ() #  TODO: this could probably be calculated prior to update coverages
        for risk in ['Stunting', 'Anaemia']:
            ageGroup.bfUpdate[risk] *= self._getUpdatesFromDiarrhoeaIncidence(beta, ageGroup, risk)
        ageGroup.bfUpdate['Wasting'] *= self._getWastingUpdateFromDiarrhoea(beta, ageGroup)

    def _getUpdatesFromDiarrhoeaIncidence(self, beta, ageGroup, risk):
        oldProb = ageGroup.getFracRisk(risk)
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
        probWasted = ageGroup.probConditionalDiarrhoea['Wasting'] # TODO: this has not been created
        for wastingCat in ageGroup.cont.wastingList:
            update[wastingCat] = 1.
            oldProb = ageGroup.wasingDist[wastingCat]
            newProb = 0.
            for bfCat in ageGroup.bfList:
                pab = ageGroup.bfDist[bfCat]
                t1 = beta[bfCat] * probWasted[wastingCat]['diarrhoea']
                t2 = (1.-beta[bfCat]) * probWasted[wastingCat['diarrhoea']]
                newProb += pab*(t1+t2)
            reduction = (oldProb - newProb)/oldProb
            update[wastingCat] *= 1. - reduction
        return update


    def _getMortalityUpdate(self, ageGroup):
        """
        Programs which directly impact mortality rates
        :return:
        """
        # TODO: this update must be used to scale the reference mortality
        update = self._getEffectivenessUpdate(ageGroup, 'Effectiveness mortality')
        for cause in self.project.causesOfDeath:
            ageGroup.mortalityUpdate[cause] *= update[cause]

    def _getBirthOutcomeUpdate(self, ageGroup):
        """
        Programs which directly impact birth outcomes
        :return:
        """
        update = self._getBOUpdate()
        for BO in self.project.birthOutcomes:
            ageGroup.birthUpdate[BO] *= update[BO]

    def _getFamilyPlanningUpdate(self, ageGroup):
        """
        Programs which directly impact family planning
        :return:
        """
    def _getNewProb(self, coverage, probCovered, probNotCovered):
        return coverage * probCovered + (1.-coverage) * probNotCovered

    def _getConditionalProbUpdate(self, ageGroup, risk):
        """This uses law of total probability to update a given age groups for risk types
        Possible risk types are 'Stunting' & 'Anaemia' """
        oldProb = ageGroup.getFracRisk(risk)
        probIfCovered = ageGroup.probConditionalCoverage[risk][self.name]['covered']
        probIfNotCovered = ageGroup.probConditionalCoverage[risk][self.name]['not covered']
        newProb = self._getNewProb(self.proposedCoverageFrac, probIfCovered, probIfNotCovered)
        reduction = (oldProb - newProb) / oldProb
        update = 1.-reduction
        return update

    def _getWastingPrevalenceUpdate(self, ageGroup):
        # overall update to prevalence of MAM and SAM
        update = {}
        for wastingCat in ['SAM', 'MAM']:
            oldProb = ageGroup.getFracWasted(wastingCat)
            probWastedIfCovered = ageGroup.probConditionalCoverage[wastingCat][self.name]['covered']
            probWastedIfNotCovered = ageGroup.probConditionalCoverage[wastingCat][self.name]['not covered']
            newProb = self._getNewProb(self.proposedCoverageFrac, probWastedIfCovered, probWastedIfNotCovered)
            reduction = (oldProb - newProb) / oldProb
            update[wastingCat] = 1-reduction
        return update

    def _getWastingUpdateFromWastingIncidence(self, ageGroup):
        incidenceUpdate = self._getWastingIncidenceUpdate(ageGroup)
        update = {}
        for condition in ['SAM', 'MAM']:
            newIncidence = ageGroup.incidences[condition] * incidenceUpdate[condition]
            reduction = (ageGroup.incidences[condition] - newIncidence)/newIncidence
            update[condition] = 1-reduction
        return update

    def _getWastingIncidenceUpdate(self, ageGroup):
        update = {}
        for condition in ['SAM', 'MAM']:
            affFrac = ageGroup.programEffectiveness[self.name][condition]['Affected fraction']
            effectiveness = ageGroup.programEffectiveness[self.name][condition]['Effectiveness incidence']
            oldCov = self.baselineCoverage
            reduction = affFrac * effectiveness * (self.proposedCoverageFrac - oldCov) / (1. - effectiveness*oldCov)
            update[condition] = 1.-reduction
        return update

    def _getEffectivenessUpdate(self, ageGroup, effType):
        """This covers mortality and incidence updates (except wasting)"""
        update = {cause: 1. for cause in self.project.causesOfDeath}
        for cause in self.project.causesOfDeath:
            affFrac = ageGroup.programEffectiveness[self.name][cause]['Affected fraction']
            effectiveness = ageGroup.programEffectiveness[self.name][cause][effType]
            oldCov = self.baselineCoverage
            reduction = affFrac * effectiveness * (self.proposedCoverageFrac - oldCov) / (1. - effectiveness*oldCov)
            update[cause] *= 1. - reduction
        return update

    def _getBOUpdate(self):
        BOupdate = {BO: 1. for BO in self.project.birthOutcomes}
        for outcome in self.project.birthOutcomes:
            affFrac = self.project.BOprograms[self.name]['affected fraction'][outcome]
            eff = self.project.BOprograms[self.name]['effectiveness'][outcome]
            oldCov = self.baselineCoverage
            reduction = affFrac * eff * (self.proposedCoverageFrac - oldCov) / (1. - eff*oldCov)
            BOupdate[outcome] = 1. - reduction
        return BOupdate

    def _getBFpracticeUpdate(self, ageGroup):
        correctPrac = ageGroup.correctBFpractice
        correctFracOld = ageGroup.bfDist[correctPrac]
        probCorrectCovered = ageGroup.probConditionalCoverage['Breastfeeding'][self.name]['covered']
        probCorrectNotCovered = ageGroup.probConditionalCoverage['Breastfeeding'][self.name]['not covered']
        probNew = self._getNewProb(self.proposedCoverageFrac, probCorrectCovered, probCorrectNotCovered)
        fracChange = probNew - correctFracOld
        correctFracBF = correctFracOld + fracChange
        return correctFracBF

    def _setCostCoverageCurve(self):
        self.costCurve = CostCovCurve(self.unitCost, self.saturation, self.restrictedPopSize, self.unrestrictedPopSize)

    def getSpending(self, covNumber):
        return self.costCurve.getSpending(covNumber)



class CostCovCurve:
    def __init__(self, unitCost, saturation, restrictedPop, unrestrictedPop):
        self.type = 'standard'
        self.unitCost = unitCost
        self.saturation = saturation
        self.restrictedPop = restrictedPop
        self.unrestrictedPop = unrestrictedPop

    def _setCostCovCurve(self):
        curve = self._increasingCostsLogisticCurve()
        return curve

    def _increasingCostsLogisticCurve(self):
        B = self.saturation * self.restrictedPop
        A = -B
        C = 0.
        D = self.unitCost*B/2.
        curve = self.getCostCoverageCurveSpecifyingParameters(A, B, C, D)
        return curve

    def getCostCoverageCurveSpecifyingParameters(self, A, B, C, D):
        '''This is a logistic curve with each parameter (A,B,C,D) provided by the user'''
        logisticCurve = lambda x: (A + (B - A) / (1 + exp(-(x - C) / D)))
        return logisticCurve

    def getSpending(self, covNumber):
        '''Assumes standard increasing marginal costs curve '''
        B = self.saturation * self.restrictedPop
        A = -B
        C = 0.
        D = self.unitCost * B / 2.
        curve = self.inverseLogistic(A, B, C, D)
        spending = curve(covNumber)
        return spending

    def inverseLogistic(self, A, B, C, D):
        if D == 0.: # this is a temp fix for removing interventions
            inverseCurve = lambda y: 0.
        else:
            inverseCurve = lambda y: -D * log((B - y) / (y - A)) + C
        return inverseCurve

def setUpPrograms(project):
    programs = [Program(program, project) for program in project.programList] # list of all programs
    programAreas = dcp(project.programAreas)
    return programs, programAreas