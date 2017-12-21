
class Program(object):
    '''Each instance of this class is an intervention,
    and all necessary data will be stored as attributes. Will store name, targetpop, popsize,coverage,edges,ORs etc
    Also want it to set absolute number covered, coverage frac (coverage amongst entire pop), normalised coverage (coverage amongst target pop)'''
    def __init__(self, name, project):
        # TODO: set the effectiveness of each intervention to no effect unless specified otherwise
        self.name = name
        self.project = project
        self.targetPopSize = None
        # TODO: The following must be set after a proposed coverage (initially baseline)
        self.numCovered = None
        self.overallCov = None # coverage amongst entire pop
        self.targetCov = None # coverage amongst target pop
        self.exclusionDepedencies = []
        self.thresholdDependencies = []

    def _addExclusionDependency(self, program):
        '''Adds links to programs that limit the coverage of this program to target pop not already covered'''
        self.exclusionDepedencies.append(program)

    def _addThresholdDependency(self, program):
        '''Adds links to programs whose coverage acts as a threshold'''
        self.thresholdDependencies.append(program)

    def _coverageUpdate(self, coverage, probCovered, probNotCovered):
        return coverage * probCovered + (1.-coverage) * probNotCovered

    def _getUpdate(self, ageGroups, newCoverage, risk):
        '''This uses law of total probability to provide updates for risk types'''
        update = {}
        for ageGroup in ageGroups:
            age = ageGroup.name
            update[age] = 1.
            oldProb = ageGroup.getFracRisk(risk) # TODO: need to write this
            probIfCovered = ageGroup.probConditionalCoverage[risk][self.name]['covered']
            probIfNotCovered = ageGroup.probConditionalCoverage[risk][self.name]['not covered']
            newProb = self._coverageUpdate(newCoverage, probIfCovered, probIfNotCovered)
            reduction = (oldProb - newProb) / oldProb
            update[age] = 1.-reduction
        return update


    def _getWastingPrevalenceUpdate(self, ageGroups, newCoverage):
        wastingUpdate = {} # overall update to prevalence of MAM and SAM
        for ageGroup in ageGroups:
            age = ageGroup.name
            wastingUpdate[age] = {}
            for wastingCat in self.project.wastedList:
                oldProb = ageGroup.getFracWasted('Wasting', wastingCat) # TODO: WRITE THIS
                probWastedIfCovered = ageGroup.probConditionalCoverage['Wasting'][wastingUpdate][self.name]['covered']
                probWastedIfNotCovered = ageGroup.probConditionalCoverage['Wasting'][wastingUpdate][self.name]['not covered']
                newProb = self._coverageUpdate(newCoverage, probWastedIfCovered, probWastedIfNotCovered)
                reduction = (oldProb - newProb) / oldProb
                wastingUpdate[age][wastingCat] = 1.-reduction
        return wastingUpdate # TODO: the SAM to MAM etc update needs to be done after combining all the updates

    def _getEffectivenessUpdate(self, ageGroups, newCoverage, effType):
        '''This covers mortality and incidence updates'''
        for ageGroup in ageGroups:
            update = {cause: 1. for cause in self.project.causesOfDeath}
            for cause in self.project.causesOfDeath:
                affFrac = ageGroup.programEffectiveness[self.name][cause]['Affected fraction']
                effectiveness = ageGroup.programEffectiveness[self.name][cause][effType]
                oldCov = self.overallCov
                reduction = affFrac * effectiveness * (newCoverage - oldCov) / (1. - effectiveness*oldCov)
                update[cause] *= 1. - reduction
        return update

    def _getBirthOutcomeUpdate(self, newCoverage):
        BOupdate = {BO: 1. for BO in self.project.BO}
        for outcome in self.project.BO:
            affFrac = self.project.BOprograms[self.name]['affected fraction'][outcome]
            eff = self.project.BOprograms[self.name]['effectiveness'][outcome]
            oldCov = self.overallCov
            reduction = affFrac * eff * (newCoverage - oldCov) / (1. - eff*oldCov)
            BOupdate[outcome] = 1. - reduction
        return BOupdate

    def _getBFpracticeUpdate(self, ageGroups, newCoverage):
        correctFracBF = {}
        for ageGroup in ageGroups:
            age = ageGroup.name
            correctPrac = ageGroup.correctBFpractice
            correctFracOld = ageGroup.bfDist[correctPrac]
            probCorrectCovered = ageGroup.probConditionalCoverage['Breastfeeding'][self.name]['covered']
            probCorrectNotCovered = ageGroup.probConditionalCoverage['Breastfeeding'][self.name]['not covered']
            probNew = self._coverageUpdate(newCoverage, probCorrectCovered, probCorrectNotCovered)
            fracChange = probNew - correctFracOld
            correctFracBF[age] = correctFracOld + fracChange
        return correctFracBF



# TODO: don't forget the MAM to SAM updates & the wasting incidence.


    # def getWastingPrevalenceUpdate(self, newCoverage):
    #     wastingUpdate = {} # overall update to prevalence of MAM and SAM
    #     fromSAMtoMAMupdate = {} # accounts for children moving from SAM to MAM after SAM treatment
    #     fromMAMtoSAMupdate = {} # accounts for children moving from MAM to SAM after MAM treatment
    #     for ageName in self.ages:
    #         fromSAMtoMAMupdate[ageName] = {}
    #         fromMAMtoSAMupdate[ageName] = {}
    #         wastingUpdate[ageName] = {}
    #         for wastingCat in self.wastedList:
    #             fromSAMtoMAMupdate[ageName][wastingCat] = 1.
    #             fromMAMtoSAMupdate[ageName][wastingCat] = 1.
    #             wastingUpdate[ageName][wastingCat] = 1.
    #             oldProbWasting = self.wastingDistribution[ageName][wastingCat]
    #             for intervention in newCoverage.keys():
    #                 probWastingIfCovered = self.derived.probWastedIfCovered[wastingCat][intervention]["covered"][ageName]
    #                 probWastingIfNotCovered = self.derived.probWastedIfCovered[wastingCat][intervention]["not covered"][ageName]
    #                 newProbWasting = newCoverage[intervention]*probWastingIfCovered + (1.-newCoverage[intervention])*probWastingIfNotCovered
    #                 reduction = (oldProbWasting - newProbWasting) / oldProbWasting
    #                 wastingUpdate[ageName][wastingCat] *= 1. - reduction
    #         fromSAMtoMAMupdate[ageName]['MAM'] = (1. + (1.-wastingUpdate[ageName]['SAM']) * self.fracSAMtoMAM)
    #         fromMAMtoSAMupdate[ageName]['SAM'] = (1. - (1.-wastingUpdate[ageName]['MAM']) * self.fracMAMtoSAM)
    #     return wastingUpdate, fromSAMtoMAMupdate, fromMAMtoSAMupdate

def setUpPrograms(project):
    programAreas = {}
    for risk, programList in project.programAreas.iteritems():
        programAreas[risk] = []
        for program in programList:
            programAreas[risk].append(Program(program, project))
    return programAreas