from copy import deepcopy as dcp
class Program(object):
    '''Each instance of this class is an intervention,
    and all necessary data will be stored as attributes. Will store name, targetpop, popsize, coverage, edges etc
    Also want it to set absolute number covered, coverage frac (coverage amongst entire pop), normalised coverage (coverage amongst target pop)'''
    def __init__(self, name, project):
        self.name = name
        self.project = dcp(project)
        self.targetPopSize = None # TODO: read-in from workbook

        self.relevantAgeGroups = None # TODO: get this from 'intervention target pop' sheet, where non-zero implies relevance


        # TODO: The following must be set after a proposed coverage (initially baseline)
        self.numCovered = None
        self.overallCov = None # coverage amongst entire pop. This will be the main coverage metric used in Model
        self.targetCov = None # coverage amongst target pop
        self.newOverallCoverage = None # TODO: this will be updated when new coverage is suggested
        self.exclusionDepedencies = []
        self.thresholdDependencies = []

        # TODO: can write method to assign a cost-curve function to this class

    def _addExclusionDependency(self, program):
        '''Adds links to programs that limit the coverage of this program to target pop not already covered'''
        self.exclusionDepedencies.append(program)

    def _addThresholdDependency(self, program):
        '''Adds links to programs whose coverage acts as a threshold'''
        self.thresholdDependencies.append(program)

    def _updateCoverage(self, newCoverage): # TODO: for now, don't need to update the baseline coverages
        self.newOverallCoverage = newCoverage

    def _updateAgeGroup(self, ageGroup, risk):
        """
        Each update method accounts for a program's _direct_ impact on each risk area.
        The relevant risk distribution or incidence will be updated for the given age group
        :param ageGroup:
        :param risk:
        :return:
        """

        # TODO: may want to create a mapping in order to call relevant update
        # TODO: these functions will ultimately update the relevant distribution of each age group
        if risk == 'Stunting':
            self._getStuntingUpdate(ageGroup)
        elif risk == 'Anaemia':
            self._getAnaemiaUpdate(ageGroup)
        elif risk == 'Wasting':
            self._getWastingUpdate(ageGroup)
        elif risk == 'Breastfeeding':
            self._getBFupdate(ageGroup)
        elif risk == 'Diarrhoea':
            self._getDiarrhoeaUpdate(ageGroup)
        elif risk == 'Mortality':
            self._getMortalityUpdate(ageGroup)
        elif risk == 'Birth outcomes':
            self._getBOupdate(ageGroup)
        elif risk == 'Family planning':
            self._getFPupdate(ageGroup)
        elif risk == 'None':
            pass

    def _getStuntingUpdate(self, ageGroup):
        """
        Will get the total stunting update for a single program.
        Since we assume independence between each kind of stunting update
        and across programs (that is, after we have accounted for dependencies),
        the order of multiplication of updates does not matter.
        """

        # TODO: currently BF and direct diarrhoea incidence are modelled separately. Should this be the case? I.e is BF practices are better, diarrhoea incidence decreases, and this should have impact on both anaemi and wasting!
        risk = 'Stunting'
        update = self._getConditionalProbUpdate(ageGroup, risk)
        # UPDATE STUNTING DISTRIBUTION
        oldProbStunting = ageGroup.getFracRisk(risk)
        newProbStunting = oldProbStunting * update
        #ageGroup.restratify(newProbStunting) # write this
        # redistribute population based on new distribution
        # ageGroup.redistribute() # use distributions of ageGroups

    def _getDiarrhoeaUpdate(self, ageGroup): # TODO: linking this and BF update will be tricky b/c incidence changes
        """
        This function accounts for the _direct_ impact of programs on diarrhoea incidence
        :param ageGroup:
        :return:
        """
        update = self._getEffectivenessUpdate(ageGroup, 'Effectiveness incidence')


    def _getBFupdate(self, ageGroup):
        """
        Accounts for the program's direct impact on breastfeeding practices
        :param ageGroup:
        :return:
        """


    def _getAnaemiaUpdate(self, ageGroup):
        """
        Get the total anaemia update for a single program.

        Programs can impact anaemia:
            1. directly
            2. indirectly through diarrhoea

        :param ageGroup: instance of AgeGroup class
        """
        update = self._getConditionalProbUpdate(ageGroup, 'Anaemia')
    
    def _getWastingUpdate(self, ageGroup):
        pass

    def _getNewProb(self, coverage, probCovered, probNotCovered):
        return coverage * probCovered + (1.-coverage) * probNotCovered

    def _getConditionalProbUpdate(self, ageGroup, risk):
        """This uses law of total probability to update a given age groups for risk types
        Possible risk types are 'Stunting' & 'Anaemia' """
        oldProb = ageGroup.getFracRisk(risk) # TODO: need to write this
        probIfCovered = ageGroup.probConditionalCoverage[risk][self.name]['covered']
        probIfNotCovered = ageGroup.probConditionalCoverage[risk][self.name]['not covered']
        newProb = self._getNewProb(self.newOverallCoverage, probIfCovered, probIfNotCovered)
        reduction = (oldProb - newProb) / oldProb
        update = 1.-reduction
        return update


    def _getWastingPrevalenceUpdate(self, ageGroup):
        wastingUpdate = {} # overall update to prevalence of MAM and SAM
        for wastingCat in self.project.wastedList:
            oldProb = ageGroup.getFracWasted('Wasting', wastingCat) # TODO: WRITE THIS
            probWastedIfCovered = ageGroup.probConditionalCoverage['Wasting'][wastingUpdate][self.name]['covered']
            probWastedIfNotCovered = ageGroup.probConditionalCoverage['Wasting'][wastingUpdate][self.name]['not covered']
            newProb = self._getNewProb(self.newOverallCoverage, probWastedIfCovered, probWastedIfNotCovered)
            reduction = (oldProb - newProb) / oldProb
            wastingUpdate[wastingCat] = 1.-reduction
        return wastingUpdate # TODO: the SAM to MAM etc update needs to be done after combining all the updates

    def _getEffectivenessUpdate(self, ageGroup, effType):
        """This covers mortality and incidence updates"""
        update = {cause: 1. for cause in self.project.causesOfDeath}
        for cause in self.project.causesOfDeath:
            affFrac = ageGroup.programEffectiveness[self.name][cause]['Affected fraction']
            effectiveness = ageGroup.programEffectiveness[self.name][cause][effType]
            oldCov = self.overallCov
            reduction = affFrac * effectiveness * (self.newOverallCoverage - oldCov) / (1. - effectiveness*oldCov)
            update[cause] *= 1. - reduction
        return update

    def _getBirthOutcomeUpdate(self):
        BOupdate = {BO: 1. for BO in self.project.BO}
        for outcome in self.project.BO:
            affFrac = self.project.BOprograms[self.name]['affected fraction'][outcome]
            eff = self.project.BOprograms[self.name]['effectiveness'][outcome]
            oldCov = self.overallCov
            reduction = affFrac * eff * (self.newOverallCoverage - oldCov) / (1. - eff*oldCov)
            BOupdate[outcome] = 1. - reduction
        return BOupdate

    def _getBFpracticeUpdate(self, ageGroup):
        correctPrac = ageGroup.correctBFpractice
        correctFracOld = ageGroup.bfDist[correctPrac]
        probCorrectCovered = ageGroup.probConditionalCoverage['Breastfeeding'][self.name]['covered']
        probCorrectNotCovered = ageGroup.probConditionalCoverage['Breastfeeding'][self.name]['not covered']
        probNew = self._getNewProb(self.newOverallCoverage, probCorrectCovered, probCorrectNotCovered)
        fracChange = probNew - correctFracOld
        correctFracBF = correctFracOld + fracChange
        return correctFracBF



# TODO: don't forget the MAM to SAM updates & the wasting incidence.


def setUpPrograms(project):
    programs = [Program(program, project) for program in project.programList] # list of all programs
    programAreas = dcp(project.programAreas)
    return programs, programAreas