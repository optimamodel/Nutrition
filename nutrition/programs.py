from numpy import exp, log, interp, isnan, array, logical_not
from copy import deepcopy as dcp

class Program(object):
    """Each instance of this class is an intervention,
    and all necessary data will be stored as attributes. Will store name, targetpop, popsize, coverage, edges etc
    Also want it to set absolute number covered, coverage frac (coverage amongst entire pop), normalised coverage (coverage amongst target pop)"""
    def __init__(self, name, constants):
        self.name = name
        self.const = constants
        self.targetPopulations = self.const.programTargetPop[self.name] # frac of each population which is targeted
        self.unitCost = self.const.costCurveInfo['unit cost'][self.name]
        self.saturation = self.const.costCurveInfo['saturation coverage'][self.name]
        self.coverageProjections = dcp(self.const.programAnnualSpending[self.name]) # will be altered
        self.restrictedBaselineCov, self.restrictedCalibrationCov = self.getRestrictedCovs()

        self._setTargetedAges()
        self._setImpactedAges() # TODO: This func could contain the info for how many multiples needed for unrestricted population calculation (IYCF)
        self._setExclusionDependencies()
        self._setThresholdDependencies()

    def getRestrictedCovs(self):
        calibrationCov = self.coverageProjections['Coverage'][1][0]
        restrictedBaseline = self.const.costCurveInfo['baseline coverage'][self.name]
        if isnan(calibrationCov): # if first coverage value comes after the calibration year
            restrictedCalibration = restrictedBaseline
        else: # user specified a calibration year coverage
            restrictedCalibration = calibrationCov
        return restrictedBaseline, restrictedCalibration

    def _setAnnualCoverageFromOptimisation(self, newCoverage): # TODO: this is also less general version of scalar version
        """
        newCoverage is passed from optimisation, which means it's already unrestricted coverage
        :param newCoverage:
        :return:
        """
        self.annualCoverage.update({year: newCoverage for year in self.const.simulationYears})

    def _setInitialCoverage(self, populations):
        """
        Sets values for 'annualCoverages' for the baseline and calibration (typically first 2 years) only.
        If a calibration coverage has been specified in the workbook, this will override the baseline coverage.
        This feature allows different costs to be calculated from the calibration coverage
        :return:
        """
        self._setBaselineCoverage(populations)
        theseYears = [self.const.baselineYear] + self.const.calibrationYears
        self.annualCoverage = {year: self.unrestrictedCalibrationCov for year in theseYears}

    def _setSimCovScalar(self, coverages, restrictedCov=True):
        years = self.const.simulationYears
        if restrictedCov:
            coverages = self._getUnrestrictedCov(coverages)
        interpolated = {year:coverages for year in years}
        self.annualCoverage.update(interpolated)

    def _setCovWorkbook(self):
        years = array(self.const.simulationYears)
        coverages = dcp(self.coverageProjections['Coverage'][1])
        coverages = array(coverages[len(self.const.calibrationYears):]) # remove calibration years
        if len(coverages) > len(years):
            coverages = coverages[:len(years)]
        not_nan = logical_not(isnan(coverages))
        if not any(not_nan):
            # is all nan, assume constant at baseline
            interpolated = {year: self.unrestrictedBaselineCov for year in years}
        else: # TODO: this could be made into a function whhich works for the 'scalar' case as well
            # for 1 or more present values, baseline up to first present value, interpolate between, then constant if end values missing
            trueIndx = [i for i, x in enumerate(not_nan) if x]
            firstTrue = trueIndx[0]
            startCov = [self.restrictedCalibrationCov for x in coverages[:firstTrue]]
            # scaledCov = coverages * self.restrictedPopSize / self.unrestrictedPopSize # convert to unrestricted coverages
            endCov = list(interp(years[firstTrue:], years[not_nan], coverages[not_nan]))
            # scale each coverage
            interpolated = {year: self._getUnrestrictedCov(cov) for year, cov in zip(years, startCov+endCov)}
        self.annualCoverage.update(interpolated)

    def _getUnrestrictedCov(self, restrictedCov):
        return restrictedCov*self.restrictedPopSize / self.unrestrictedPopSize

    def _setBaselineCoverage(self, populations):
        self._setRestrictedPopSize(populations)
        self._setUnrestrictedPopSize(populations)
        self.unrestrictedBaselineCov = (self.restrictedBaselineCov * self.restrictedPopSize) / \
                                          self.unrestrictedPopSize
        self.unrestrictedCalibrationCov = (self.restrictedCalibrationCov * self.restrictedPopSize) / \
                                          self.unrestrictedPopSize

    def _adjustCoverage(self, populations, year):
        # set unrestricted pop size so coverages account for growing population size
        oldURP = dcp(self.unrestrictedPopSize)
        self._setRestrictedPopSize(populations) # TODO: is this the optimal place to do this?
        self._setUnrestrictedPopSize(populations)
        oldCov = self.annualCoverage[year]
        newCov = oldURP * oldCov / self.unrestrictedPopSize
        self.annualCoverage.update({year:newCov})

    def updateCoverage(self, newCoverage, populations):
        """Update all values pertaining to coverage for a program"""
        self.proposedCoverageNum = newCoverage
        self._setUnrestrictedPopSize(populations)
        self._setRestrictedPopSize(populations)
        self.proposedCoverageFrac = self.proposedCoverageNum / self.unrestrictedPopSize

    def updateCoverageFromPercentage(self, newCoverage, populations): # TODO: wrong b/c coverages already converted in UR coverages
        """Update all values pertaining to coverage for a program.
        Assumes new coverage is restricted coverage"""
        self._setUnrestrictedPopSize(populations)
        self._setRestrictedPopSize(populations)
        restrictedCovNum = self.restrictedPopSize * newCoverage
        self.proposedCoverageFrac = restrictedCovNum / self.unrestrictedPopSize

    def _setTargetedAges(self):
        """
        The ages at whom programs are targeted
        :return:
        """
        self.agesTargeted = []
        for age in self.const.allAges:
            fracTargeted = self.const.programTargetPop[self.name][age]
            if fracTargeted > 0.001: # floating point tolerance
                self.agesTargeted.append(age)

    def _setImpactedAges(self):
        """
        The ages who are impacted by this program
        :return:
        """
        self.agesImpacted = []
        for age in self.const.allAges:
            impacted = self.const.programImpactedPop[self.name][age]
            if impacted > 0.001: # floating point tolerance
                self.agesImpacted.append(age)

    def _setUnrestrictedPopSize(self, populations):
        """
        sum of the total pop for each targeted age group
        """
        # TMP SOLUTION: THE DENOMINATOR FOR CALCULATING PROGRAM COVERAGE WILL USE sum(CEILING(FRAC TARGETED) * POP SIZE) over all pops targeted. I.E. FOR IYCF WITH FRAC >1, we get normalised sum
        from math import ceil
        self.unrestrictedPopSize = 0.
        for pop in populations:
            self.unrestrictedPopSize += sum(ceil(self.targetPopulations[age.age])*age.getAgeGroupPopulation() for age in pop.ageGroups
                                           if age.age in self.agesTargeted)

    def _setRestrictedPopSize(self, populations):
        self.restrictedPopSize = 0.
        for pop in populations:
            self.restrictedPopSize += sum(age.getAgeGroupPopulation() * self.targetPopulations[age.age] for age in pop.ageGroups
                                         if age.age in self.agesTargeted)

    def _setExclusionDependencies(self):
        """
        List containing the names of programs which restrict the coverage of this program to (1 - coverage of independent program)
        :return:
        """
        self.exclusionDependencies = []
        dependencies = self.const.programDependency[self.name]['Exclusion dependency']
        for program in dependencies:
            self.exclusionDependencies.append(program)

    def _setThresholdDependencies(self):
        """
        List containing the name of programs which restrict the coverage of this program to coverage of independent program
        :return:
        """
        self.thresholdDependencies = []
        dependencies = self.const.programDependency[self.name]['Threshold dependency']
        for program in dependencies:
            self.thresholdDependencies.append(program)

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

    def _getFamilyPlanningUpdate(self, ageGroup):
        ageGroup.FPupdate *= self.annualCoverage[self.year]

    def _getWastingPreventionUpdate(self, ageGroup):
        update = self._getWastingIncidenceUpdate(ageGroup)
        for wastingCat in self.const.wastedList:
            ageGroup.wastingPreventionUpdate[wastingCat] *= update[wastingCat]

    def _getWastingTreatmentUpdate(self, ageGroup):
        update = self._getWastingPrevalenceUpdate(ageGroup)
        for wastingCat in self.const.wastedList:
            ageGroup.wastingTreatmentUpdate[wastingCat] *= update[wastingCat]

    def _getDiarrhoeaIncidenceUpdate(self, ageGroup):
        """
        This function accounts for the _direct_ impact of programs on diarrhoea incidence
        :param ageGroup:
        :return:
        """
        update = self._getEffectivenessUpdate(ageGroup, 'Effectiveness incidence')
        ageGroup.diarrhoeaIncidenceUpdate *= update['Diarrhoea']

    def _getBreastfeedingupdate(self, ageGroup):
        """
        Accounts for the program's direct impact on breastfeeding practices
        :param ageGroup:
        :return:
        """
        ageGroup.bfPracticeUpdate += self._getBFpracticeUpdate(ageGroup)


    def _getMortalityUpdate(self, ageGroup):
        """
        Programs which directly impact mortality rates
        :return:
        """
        update = self._getEffectivenessUpdate(ageGroup, 'Effectiveness mortality')
        for cause in self.const.causesOfDeath:
            ageGroup.mortalityUpdate[cause] *= update[cause]

    def _getBirthOutcomeUpdate(self, ageGroup):
        """
        Programs which directly impact birth outcomes
        :return:
        """
        update = self._getBOUpdate()
        for BO in self.const.birthOutcomes:
            ageGroup.birthUpdate[BO] *= update[BO]

    def _getBirthAgeUpdate(self, ageGroup):
        update = self._getBAUpdate()
        for BA in self.const.birthAges:
            ageGroup.birthUpdate[BA] *= update[BA]

    def _getNewProb(self, coverage, probCovered, probNotCovered):
        return coverage * probCovered + (1.-coverage) * probNotCovered

    def _getConditionalProbUpdate(self, ageGroup, risk):
        """This uses law of total probability to update a given age groups for risk types
        Possible risk types are 'Stunting' & 'Anaemia' """
        oldProb = ageGroup.getFracRisk(risk)
        probIfCovered = ageGroup.probConditionalCoverage[risk][self.name]['covered']
        probIfNotCovered = ageGroup.probConditionalCoverage[risk][self.name]['not covered']
        newProb = self._getNewProb(self.annualCoverage[self.year], probIfCovered, probIfNotCovered)
        reduction = (oldProb - newProb) / oldProb
        update = 1.-reduction
        return update

    def _getWastingPrevalenceUpdate(self, ageGroup):
        # overall update to prevalence of MAM and SAM
        update = {}
        for wastingCat in self.const.wastedList:
            oldProb = ageGroup.getWastedFrac(wastingCat)
            probWastedIfCovered = ageGroup.probConditionalCoverage[wastingCat][self.name]['covered']
            probWastedIfNotCovered = ageGroup.probConditionalCoverage[wastingCat][self.name]['not covered']
            newProb = self._getNewProb(self.annualCoverage[self.year], probWastedIfCovered, probWastedIfNotCovered)
            reduction = (oldProb - newProb) / oldProb
            update[wastingCat] = 1-reduction
        return update

    def _getWastingUpdateFromWastingIncidence(self, ageGroup):
        incidenceUpdate = self._getWastingIncidenceUpdate(ageGroup)
        update = {}
        for condition in self.const.wastedList:
            newIncidence = ageGroup.incidences[condition] * incidenceUpdate[condition]
            reduction = (ageGroup.incidences[condition] - newIncidence)/newIncidence
            update[condition] = 1-reduction
        return update

    def _getWastingIncidenceUpdate(self, ageGroup):
        update = {}
        oldCov = self.annualCoverage[self.year-1]
        for condition in self.const.wastedList:
            affFrac = ageGroup.programEffectiveness[self.name][condition]['Affected fraction']
            effectiveness = ageGroup.programEffectiveness[self.name][condition]['Effectiveness incidence']
            reduction = affFrac * effectiveness * (self.annualCoverage[self.year] - oldCov) / (1. - effectiveness*oldCov)
            update[condition] = 1.-reduction
        return update

    def _getEffectivenessUpdate(self, ageGroup, effType):
        """This covers mortality and incidence updates (except wasting)"""
        if 'incidence' in effType:
            toIterate = ['Diarrhoea'] # only model diarrhoea incidence
        else: # mortality
            toIterate = self.const.causesOfDeath
        update = {cause: 1. for cause in toIterate}
        oldCov = self.annualCoverage[self.year-1]
        for cause in toIterate:
            affFrac = ageGroup.programEffectiveness[self.name][cause]['Affected fraction']
            effectiveness = ageGroup.programEffectiveness[self.name][cause][effType]
            reduction = affFrac * effectiveness * (self.annualCoverage[self.year] - oldCov) / (1. - effectiveness*oldCov)
            update[cause] *= 1. - reduction
        return update

    def _getBOUpdate(self):
        BOupdate = {BO: 1. for BO in self.const.birthOutcomes}
        oldCov = self.annualCoverage[self.year-1]
        for outcome in self.const.birthOutcomes:
            affFrac = self.const.BOprograms[self.name]['affected fraction'][outcome]
            eff = self.const.BOprograms[self.name]['effectiveness'][outcome]
            reduction = affFrac * eff * (self.annualCoverage[self.year] - oldCov) / (1. - eff*oldCov)
            BOupdate[outcome] = 1. - reduction
        return BOupdate

    def _getBAUpdate(self):
        BAupdate = {BA: 1. for BA in self.const.birthAges}
        oldCov = self.annualCoverage[self.year-1]
        for BA in self.const.birthAges:
            affFrac = self.const.birthAgeProgram[BA]['affected fraction']
            eff = self.const.birthAgeProgram[BA]['effectiveness']
            reduction = affFrac * eff * (self.annualCoverage[self.year] - oldCov) / (1. - eff*oldCov)
            BAupdate[BA] = 1. - reduction
        return BAupdate

    def _getBFpracticeUpdate(self, ageGroup):
        correctPrac = ageGroup.correctBFpractice
        correctFracOld = ageGroup.bfDist[correctPrac]
        probCorrectCovered = ageGroup.probConditionalCoverage['Breastfeeding'][self.name]['covered']
        probCorrectNotCovered = ageGroup.probConditionalCoverage['Breastfeeding'][self.name]['not covered']
        probNew = self._getNewProb(self.annualCoverage[self.year], probCorrectCovered, probCorrectNotCovered)
        fracChange = probNew - correctFracOld
        return fracChange

    def _setCostCoverageCurve(self):
        self.costCurveOb = CostCovCurve(self.unitCost, self.saturation, self.restrictedPopSize, self.unrestrictedPopSize)
        self.costCurveFunc = self.costCurveOb._setCostCovCurve()

    def getSpending(self):
        # spending is base on BASELINE coverages
        return self.costCurveOb.getSpending(self.unrestrictedBaselineCov) # TODO: want to change this so that uses annual Coverages

    def scaleUnitCosts(self, scaleFactor):
        self.unitCost *= scaleFactor
        self._setCostCoverageCurve()

class CostCovCurve:
    def __init__(self, unitCost, saturation, restrictedPop, unrestrictedPop, curveType='linear'):
        self.curveType = curveType
        self.unitCost = unitCost
        self.saturation = saturation
        self.restrictedPop = restrictedPop
        self.unrestrictedPop = unrestrictedPop

    def _setCostCovCurve(self):
        if self.curveType == 'linear':
            curve = self._linearCostCurve()
        else:
            curve = self._increasingCostsLogisticCurve()
        return curve

    def _increasingCostsLogisticCurve(self):
        B = self.saturation * self.restrictedPop
        A = -B
        C = 0.
        D = self.unitCost*B/2.
        curve = self._getLogisticCurve(A, B, C, D)
        return curve

    def _getLogisticCurve(self, A, B, C, D):
        """This is a logistic curve with each parameter (A,B,C,D) provided by the user"""
        logisticCurve = lambda x: (A + (B - A) / (1 + exp(-(x - C) / D)))
        return logisticCurve

    def getSpending(self, covFrac):
        """Assumes standard increasing marginal costs curve or linear """
        covNumber = covFrac * self.unrestrictedPop
        if self.curveType == 'linear':
            m = 1. / self.unitCost
            x0, y0 = [0., 0.]  # extra point
            if x0 == 0.:
                c = y0
            else:
                c = y0 / (m * x0)
            spending = (covNumber - c)/m
        else:
            B = self.saturation * self.restrictedPop
            A = -B
            C = 0.
            D = self.unitCost * B / 2.
            curve = self.inverseLogistic(A, B, C, D)
            spending = curve(covNumber)
        return spending

    def _linearCostCurve(self):
        m = 1. / self.unitCost
        x0, y0 = [0.,0.] #extra point
        if x0 == 0.:
            c = y0
        else:
            c = y0 / (m * x0)
        maxCoverage = self.restrictedPop * self.saturation
        linearCurve = lambda x: (min(m * x + c, maxCoverage))
        return linearCurve

    # def _plotCurve(self):
    #     import matplotlib.pyplot as plt
    #     from numpy import linspace
    #     xpts = linspace(0, 100000000, 10000)
    #     funcVal = []
    #     for x in xpts:
    #         funcVal.append(self.curve(x))
    #     plt.plot(xpts, funcVal)

    def inverseLogistic(self, A, B, C, D):
        if D == 0.: # this is a temp fix for removing interventions
            inverseCurve = lambda y: 0.
        else:
            inverseCurve = lambda y: -D * log((B - y) / (y - A)) + C
        return inverseCurve

def _setPrograms(constants):
    programs = [Program(program, constants) for program in constants.programList] # list of all programs
    return programs