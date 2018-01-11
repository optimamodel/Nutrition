from itertools import product
from copy import deepcopy as dcp

class Box:
    def __init__(self, populationSize):
        self.populationSize = populationSize
        self.mortalityRate = None
        self.cumulativeDeaths = 0

class WomenAgeGroup:
    def __init__(self, age, populationSize, boxes, anaemiaDist, ageSpan, constants):
        self.age = age
        self.populationSize = populationSize
        self.boxes = boxes
        self.anaemiaDist = anaemiaDist
        self.ageingRate = 1./ageSpan
        self.const = constants
        self.anaemiaUpdate = 1.
        self.probConditionalCoverage = {}
        self.probConditionalDiarrhoea = {}
        self.probConditionalStunting = {}
        self.programEffectiveness = {}

class ChildAgeGroup:
    def __init__(self, age, populationSize, boxes, anaemiaDist, incidences, stuntingDist, wastingDist, BFdist, birthDist,
                 ageSpan, constants):
        self.age = age
        self.populationSize = populationSize
        self.boxes = boxes
        self.anaemiaDist = anaemiaDist
        self.stuntingDist = stuntingDist
        self.wastingDist = wastingDist
        self.bfDist = BFdist
        self.birthDist = birthDist
        self.incidences = incidences
        self.const = constants
        self.correctBF = self.const.correctBF[age]
        self.incorrectBF = list(set(self.const.bfList) - set(self.correctBF))
        self.ageingRate = 1./ageSpan
        self.probConditionalCoverage = {}
        self.probConditionalDiarrhoea = {}
        self.probConditionalStunting = {}
        self.programEffectiveness = {}
        self._setUpdateStorage()


    def _setUpdateStorage(self):
        # storing updates
        self.stuntingUpdate = 1.
        self.anaemiaUpdate = 1.
        self.bfUpdate = {}
        self.diarrhoeaUpdate = {}
        for risk in ['Stunting', 'Anaemia'] + self.const.wastedList:
            self.bfUpdate[risk] = 1.
        self.mortalityUpdate = {}
        for cause in self.const.causesOfDeath:
            self.mortalityUpdate[cause] = 1.
        self.diarrhoeaUpdate = {}
        for risk in self.const.wastedList + ['Stunting', 'Anaemia']:
            self.diarrhoeaUpdate[risk] = 1.
        self.birthUpdate = {}
        for BO in self.const.birthOutcomes:
            self.birthUpdate[BO] = 1.
        self.wastingPreventionUpdate = {}
        self.wastingTreatmentUpdate = {}
        for wastingCat in self.const.wastedList:
            self.wastingPreventionUpdate[wastingCat] = 1.
            self.wastingTreatmentUpdate[wastingCat] = 1.

    def _getPopulation(self, risks):
        """ Get population size for given age groups and combinations of given risks"""
        populationSize = sum(self.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize
                              for stuntingCat, wastingCat, bfCat, anaemiaCat in product(*risks))
        return populationSize

    def _replaceRiskList(self, index, newList):
        """replaces one risk list in a list of risk lists. index is the position of list to replace """
        alteredList = self.const.allRisks[:]
        alteredList[index] = newList
        return alteredList

    def getNumberStunted(self):
        risks = self._replaceRiskList(0, self.const.stuntedList)
        return self._getPopulation(risks)

    def getStuntedFrac(self):
        return self.getNumberStunted() / self.populationSize

    def getNumberAnaemic(self):
        risks = self._replaceRiskList(3, self.const.anaemicList)
        return self._getPopulation(risks)

    def getAnaemicFrac(self):
        return self.getNumberAnaemic() / self.populationSize

    def getFracRisk(self, risk):
        if risk == 'Stunting':
            return self.getStuntedFrac()
        elif risk == 'Anaemia':
            return self.getAnaemicFrac()

    def getFracWasted(self, wastingCat):
        return self.getNumberWasted(wastingCat) / self.populationSize

    def getNumberWasted(self, wastingCat):
        risks = self._replaceRiskList(1, [wastingCat])
        return self._getPopulation(risks)

    def getNumberCorrectlyBF(self):
        risks = self._replaceRiskList(2, [self.correctBF])
        return self._getPopulation(risks)

    def redistributePopulation(self):
        for stuntingCat in self.const.stuntingList:
            for wastingCat in self.const.wastingList:
                for bfCat in self.const.bfList:
                    for anaemiaCat in self.const.anaemiaList:
                        self.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize = self.stuntingDist[stuntingCat] * \
                                                                                                self.wastingDist[wastingCat] * \
                                                                                                self.bfDist[bfCat] * \
                                                                                                self.anaemiaDist[anaemiaCat] * \
                                                                                                self.populationSize

    def _getFracDiarrhoeaFixedZ(self):
        beta = {}
        RRnot = self.const.RRdiarrhoea['none'][self.age]
        for bfCat in self.const.bfList:
            RDa = self.const.RRdiarrhoea[bfCat][self.age]
            beta[bfCat] = RDa/RRnot
        return beta

    def _getFracDiarrhoea(self, Z0, Zt):
        beta = {}
        RRnot = self.const.RRdiarrhoea["none"][self.age]
        for bfCat in self.const.bfList:
            RDa = self.const.RRdiarrhoea[bfCat][self.age]
            beta[bfCat] = 1. - (RRnot * Z0 - RDa * Zt) / \
                          (RRnot * Z0)
            # RDa * Zt[age] / (RRnot * Z0[age])
        return beta

    def _getZa(self):
        riskSum = self._getDiarrhoeaRiskSum()
        incidence = self.incidences['Diarrhoea']
        return incidence / riskSum

    def _getDiarrhoeaRiskSum(self):
        return sum(self.const.RRdiarrhoea[bfCat][self.age] * self.bfDist[bfCat] for bfCat in self.const.bfList)

    def _getAverageOR(self, Za, risk):
        from math import pow
        RRnot = self.const.RRdiarrhoea['none'][self.age]
        if risk == 'Stunting':
            OR = self.const.ORcondition['OR stunting by condition']['Diarrhoea'][self.age]
        elif risk == 'Anaemia':
            OR = self.const.ORcondition['OR anaemia by condition']['Severe diarrhoea'][self.age]
        elif risk == 'MAM' or risk == 'SAM':
            OR = self.const.ORcondition['OR '+risk+' by condition']['Diarrhoea'][self.age]
        else:
            print 'risk factor is invalid'
        AO = pow(OR, RRnot * Za * 1./self.ageingRate)
        return AO

    def _updateProbConditionalDiarrhoea(self, Zt):
        # stunting and anaemia
        AO = {}
        for risk in ['Stunting', 'Anaemia']:
            if risk == 'Anaemia':
                AO[risk] = self._getAverageOR(Zt * self.const.demographics['fraction severe diarrhoea'], risk)
            else:
                AO[risk] = self._getAverageOR(Zt, risk)
            Omega0 = self.probConditionalDiarrhoea[risk]['no diarrhoea']
            self.probConditionalDiarrhoea[risk]['diarrhoea'] = Omega0 * AO[risk] / (1. - Omega0 + AO[risk] * Omega0)
        # wasting cats
        for wastingCat in self.const.wastedList:
            AO = self._getAverageOR(Zt, wastingCat)
            Omega0 = self.probConditionalDiarrhoea[wastingCat]['no diarrhoea']
            self.probConditionalDiarrhoea[wastingCat]['diarrhoea'] = Omega0 * AO / (1. - Omega0 + AO * Omega0)

    def restratify(self, fractionYes): # TODO: may not be the best place for this. Model?
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

class Population(object):
    def __init__(self, name, project, constants):
        self.name = name
        self.project = dcp(project) # TODO: may not want to dcp all this -- only really want to get distribution data from project
        self.const = constants
        self.stuntingDist = self.project.riskDistributions['Stunting']
        self.wastingDist = self.project.riskDistributions['Wasting']
        self.bfDist = self.project.riskDistributions['Breastfeeding']
        self.anaemiaDist = self.project.riskDistributions['Anaemia']
        self.birthDist = self.project.birthDist
        self.baselineCov = self.project.costCurveInfo['baseline coverage']
        self.incidences = self.project.incidences
        self.RRdiarrhoea = self.project.RRdeath['Child diarrhoea']['Diarrhoea incidence']
        self.ORcondition = self.project.ORcondition
        self.boxes = {}

    def getDistribution(self, risk):
        return self.project.riskDistributions[risk]

    def _solveQuadratic(self, oddsRatio, fracA, fracB):
        # solves quadratic to calculate probabilities where e.g.:
        # fracA is fraction covered by intervention
        # fracB is fraction of pop. in a particular risk status
        from numpy import sqrt
        eps = 1.e-5
        a = (1. - fracA) * (1. - oddsRatio)
        b = (oddsRatio - 1) * fracB - oddsRatio * fracA - (1. - fracA)
        c = fracB
        det = sqrt(b ** 2 - 4. * a * c)
        if (abs(a) < eps):
            p0 = -c / b
        else:
            soln1 = (-b + det) / (2. * a)
            soln2 = (-b - det) / (2. * a)
            if (soln1 > 0.) and (soln1 < 1.): p0 = soln1
            if (soln2 > 0.) and (soln2 < 1.): p0 = soln2
        p1 = p0 * oddsRatio / (1. - p0 + oddsRatio * p0)
        return p0, p1

class Children(Population):
    def __init__(self, name, project, constants):
        super(Children, self).__init__(name, project, constants)
        self.ageGroups = []
        self.probRiskAtBirth = {}
        self._makePopSizes()
        self._makeBoxes()
        self._setChildrenReferenceMortality()
        self._updateMortalityRates()
        self._setProbConditionalStunting()
        self._setProbConditionalCoverage()
        self._setProbWastedIfCovered()
        self._setProbStuntedAtBirth()
        self._setProbWastedAtBirth()
        self._setProbConditionalDiarrhoea()
        self._setProbWastedIfDiarrhoea()
        self._setProgramEffectiveness()
        self._setCorrectBFpractice()

    ##### DATA WRANGLING ######

    def _makePopSizes(self):
        # for children less than 1 year, annual live births
        monthlyBirths = self.const.demographics['number of live births'] / 12.
        popSize = [pop * monthlyBirths for pop in self.const.childAgeSpans[:3]]
        # children > 1 year, who are not counted in annual 'live births'
        months = sum(self.const.childAgeSpans[3:])
        popRemainder = self.const.demographics['population U5'] - monthlyBirths * 12.
        monthlyRate = popRemainder/months
        popSize += [pop * monthlyRate for pop in self.const.childAgeSpans[3:]]
        self.popSizes = {age:pop for age, pop in zip(self.const.childAges, popSize)}

    def _makeBoxes(self):
        for idx in range(len(self.project.childAges)):
            age = self.project.childAges[idx]
            popSize = self.popSizes[age]
            boxes = {}
            stuntingDist = self.stuntingDist[age]
            anaemiaDist = self.anaemiaDist[age]
            wastingDist = self.wastingDist[age]
            bfDist = self.bfDist[age]
            birthDist = self.birthDist
            incidences = self.project.incidences[age]
            ageingRate = 1./self.const.childAgeSpans[idx]
            for stuntingCat in self.const.stuntingList:
                boxes[stuntingCat] = {}
                for wastingCat in self.const.wastingList:
                    boxes[stuntingCat][wastingCat] = {}
                    for bfCat in self.const.bfList:
                        boxes[stuntingCat][wastingCat][bfCat] = {}
                        for anaemiaCat in self.const.anaemiaList:
                            thisPop = popSize * stuntingDist[stuntingCat] * anaemiaDist[anaemiaCat] * \
                                      wastingDist[wastingCat] * bfDist[bfCat]
                            boxes[stuntingCat][wastingCat][bfCat][anaemiaCat] = Box(thisPop)
            self.ageGroups.append(ChildAgeGroup(age, popSize, boxes,
                                           anaemiaDist, incidences, stuntingDist, wastingDist, bfDist, birthDist,
                                                ageingRate, self.const))

    def _setChildrenReferenceMortality(self):
        # Equation is:  LHS = RHS * X
        # we are solving for X
        # Calculate RHS for each age and cause
        RHS = {}
        for age in self.const.childAges:
            RHS[age] = {}
            for cause in self.project.causesOfDeath:
                RHS[age][cause] = 0.
                for stuntingCat in self.const.stuntingList:
                    for wastingCat in self.const.wastingList:
                        for bfCat in self.const.bfList:
                            for anaemiaCat in self.const.anaemiaList:
                                t1 = self.stuntingDist[age][stuntingCat]
                                t2 = self.wastingDist[age][wastingCat]
                                t3 = self.bfDist[age][bfCat]
                                t4 = self.anaemiaDist[age][anaemiaCat]
                                t5 = self.project.RRdeath['Stunting'][cause][stuntingCat][age]
                                t6 = self.project.RRdeath['Wasting'][cause][wastingCat][age]
                                t7 = self.project.RRdeath['Breastfeeding'][cause][bfCat][age]
                                t8 = self.project.RRdeath['Anaemia'][cause][anaemiaCat][age]
                                RHS[age][cause] += t1 * t2 * t3 * t4 * t5 * t6 * t7 * t8
        # RHS for newborns only
        age = '<1 month'
        for cause in self.project.causesOfDeath:
            RHS[age][cause] = 0.
            for breastfeedingCat in self.const.bfList:
                Pbf = self.bfDist[age][breastfeedingCat]
                RRbf = self.project.RRdeath['Breastfeeding'][cause][breastfeedingCat][age]
                for birthoutcome in self.const.birthOutcomes:
                    Pbo = self.birthDist[birthoutcome]
                    RRbo = self.project.RRdeath['Birth outcomes'][cause][birthoutcome]
                    for anemiaStatus in self.const.anaemiaList:
                        Pan = self.anaemiaDist[age][anemiaStatus]
                        RRan = self.project.RRdeath['Anaemia'][cause][anemiaStatus][age]
                        RHS[age][cause] += Pbf * RRbf * Pbo * RRbo * Pan * RRan
        # calculate total mortality by age (corrected for units)
        AgePop = [age.populationSize for age in self.ageGroups]
        MortalityCorrected = {}
        LiveBirths = self.project.demographics["number of live births"]
        Mnew = self.project.mortalityRates["neonatal mortality"]
        Minfant = self.project.mortalityRates["infant mortality"]
        Mu5 = self.project.mortalityRates["under 5 mortality"]
        # Newborns
        ageName = self.ageGroups[0].age
        m0 = Mnew * LiveBirths / 1000. / AgePop[0]
        MortalityCorrected[ageName] = m0
        # 1-5 months
        ageName = self.ageGroups[1].age
        m1 = (Minfant - Mnew) * LiveBirths / 1000. * 5. / 11. / AgePop[1]
        MortalityCorrected[ageName] = m1
        # 6-12 months
        ageName = self.ageGroups[2].age
        m2 = (Minfant - Mnew) * LiveBirths / 1000. * 6. / 11. / AgePop[2]
        MortalityCorrected[ageName] = m2
        # 12-24 months
        ageName = self.ageGroups[3].age
        m3 = (Mu5 - Minfant) * LiveBirths / 1000. * 1. / 4. / AgePop[3]
        MortalityCorrected[ageName] = m3
        # 24-60 months
        ageName = self.ageGroups[4].age
        m4 = (Mu5 - Minfant) * LiveBirths / 1000. * 3. / 4. / AgePop[4]
        MortalityCorrected[ageName] = m4
        # Calculate LHS for each age and cause of death then solve for X
        for ageGroup in self.ageGroups:
            ageGroup.referenceMortality = {}
            age = ageGroup.age
            for cause in self.const.causesOfDeath:
                LHS_age_cause = MortalityCorrected[age] * self.project.deathDist[cause][age]
                ageGroup.referenceMortality[cause] = LHS_age_cause / RHS[age][cause]

    def _updateMortalityRates(self):
        # Newborns first
        ageGroup = self.ageGroups[0]
        age = ageGroup.age
        for bfCat in self.const.bfList:
            count = 0.
            for cause in self.project.causesOfDeath:
                Rb = self.project.RRdeath['Breastfeeding'][cause][bfCat][age]
                for outcome in self.const.birthOutcomes:
                    pbo = self.birthDist[outcome]
                    Rbo = self.project.RRdeath['Birth outcomes'][cause][outcome]
                    count += Rb * pbo * Rbo * ageGroup.referenceMortality[cause]
            for stuntingCat in self.const.stuntingList:
                for wastingCat in self.const.wastingList:
                    for anaemiaCat in self.const.anaemiaList:
                        ageGroup.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].mortalityRate = count
        # over 1 months
        for ageGroup in self.ageGroups[1:]:
            age = ageGroup.age
            for stuntingCat in self.const.stuntingList:
                for wastingCat in self.const.wastingList:
                    for bfCat in self.const.bfList:
                        for anemiaStatus in self.const.anaemiaList:
                            count = 0.
                            for cause in self.project.causesOfDeath:
                                t1 = ageGroup.referenceMortality[cause]
                                t2 = self.project.RRdeath['Stunting'][cause][stuntingCat][age]
                                t3 = self.project.RRdeath['Wasting'][cause][wastingCat][age]
                                t4 = self.project.RRdeath['Breastfeeding'][cause][bfCat][age]
                                t5 = self.project.RRdeath['Anaemia'][cause][anemiaStatus][age]
                                count += t1 * t2 * t3 * t4 * t5
                            ageGroup.boxes[stuntingCat][wastingCat][bfCat][anemiaStatus].mortalityRate = count

    def _applyMortality(self):
        for ageGroup in self.ageGroups:
            for stuntingCat in self.const.stuntingList:
                for wastingCat in self.const.wastingList:
                    for bfCat in self.const.bfList:
                        for anaemiaCat in self.const.anaemiaList:
                            thisBox = ageGroup.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat]
                            deaths = thisBox.populationSize * thisBox.mortalityRate * self.const.timestep # monthly deaths
                            thisBox.populationSize -= deaths
                            thisBox.cumulativeDeaths += deaths




    # TODO: do we need the below since we have it in age groups? Could make wrapper functions

    def _getPopulation(self, ageGroups, risks):
        """ Get population size for given age groups and combinations of given risks"""
        populationSize = sum([group.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize
                              for group in ageGroups for stuntingCat, wastingCat, bfCat, anaemiaCat in product(*risks)])
        return populationSize

    #TODO: all these functions cn now use the fact that each age group has distribution stored

    def getTotalPopulation(self):
        return self._getPopulation(self.ageGroups, self.const.allRisks)


    def getFracRisk(self, risk):
        # TODO: fix this
        if risk == 'Stunting':
            return self.getTotalFracStunted()
        # elif risk == 'Anaemia':
        #     return self.getTotalFracAnaemic()

    def getTotalNumberStunted(self):
        risks = self._replaceRiskList(0, self.const.stuntedList)
        return self._getPopulation(self.ageGroups, risks)

    def getTotalFracStunted(self):
        return self.getTotalNumberStunted() / self.getTotalPopulation()

    def getFracStuntedFirstCompartment(self):
        risks = self._replaceRiskList(0, self.const.stuntedList)
        firstComp = self.ageGroups[0]
        return self._getPopulation([firstComp], risks) / firstComp.populationSize

    def getFracStuntedGivenAge(self, age):
        ageMap = {'<1 month': 0, '1-5 months': 1, '6-11 months': 2, '12-23 months': 3, '24-59 months': 4}
        indx = ageMap[age]
        risks = self._replaceRiskList(0, self.const.stuntedList)
        thisAge = self.ageGroups[indx]
        return self._getPopulation([thisAge], risks) / thisAge.populationSize

    def getTotalWasted(self):
        risks = self._replaceRiskList(1, self.const.wastedList)
        return self._getPopulation(self.ageGroups, risks)

    def getFracWastedFirstCompartment(self):
        risks = self._replaceRiskList(1, self.const.wastedList)
        firstComp = self.ageGroups[0]
        return self._getPopulation([firstComp], risks) / firstComp.populationSize

    def getTotalAnaemic(self):
        risks = self._replaceRiskList(3, self.const.anaemicList)
        return self._getPopulation(self.ageGroups, risks)

    def _replaceRiskList(self, index, newList):
        """replaces one risk list in a list of risk lists. index is the position of list to replace """
        alteredList = self.const.allRisks[:]
        alteredList[index] = newList
        return alteredList










    def _setProbConditionalStunting(self):
        """Calculate the probability of stunting given previous stunting between age groups"""
        for indx in range(1, len(self.ageGroups)):
            ageGroup = self.ageGroups[indx]
            thisAge = ageGroup.age
            prevAgeGroup = self.ageGroups[indx-1]
            prevAge = prevAgeGroup.age
            OR = self.project.ORcondition['Stunting progression'][thisAge]
            fracStuntedThisAge = self.getFracStuntedGivenAge(thisAge)
            fracStuntedPrev = self.getFracStuntedGivenAge(prevAge)
            pn, pc = self._solveQuadratic(OR, fracStuntedPrev, fracStuntedThisAge)
            ageGroup.probConditionalStunting['stunted'] = pc
            ageGroup.probConditionalStunting['not stunted'] = pn

    def _setProbConditionalCoverage(self):
        """Set the conditional probabilities of a risk factor (except wasting) given program coverage.
        Note that this value is dependent upon the baseline coverage of the program"""
        risks = [risk for i, risk in enumerate(self.const.risks) if i !=1 ] # remove wasting
        for risk in risks:
            cats = self.project.riskCategories[risk]
            middle = len(cats) / 2
            relevantCats = cats[middle:] # assumes list is symmetric
            dist = self.project.riskDistributions[risk]
            for ageGroup in self.ageGroups:
                age = ageGroup.age
                ageGroup.probConditionalCoverage[risk] = {}
                for program in self.project.programList:
                    ageGroup.probConditionalCoverage[risk][program] = {}
                    fracCovered = self.baselineCov[program]
                    fracImpacted = sum(dist[age][cat] for cat in relevantCats)
                    if self.project.RRprograms[risk].get(program) is not None:
                        RR = self.project.RRprograms[risk][program][age]
                        pn = fracImpacted/(RR*fracCovered + (1.-fracCovered))
                        pc = RR * pn
                    else: # OR
                        OR = self.project.ORprograms[risk][program][age]
                        pn, pc = self._solveQuadratic(OR, fracCovered, fracImpacted)
                    ageGroup.probConditionalCoverage[risk][program]['covered'] = pc
                    ageGroup.probConditionalCoverage[risk][program]['not covered'] = pn

    def _setProbWastedIfCovered(self):
        for wastingCat in self.const.wastedList:
            conditionalProb = {}
            conditionalProb[wastingCat] = {}
            for ageGroup in self.ageGroups:
                age = ageGroup.age
                for program in self.project.programList:
                    OR = self.project.ORwastingProgram[wastingCat][program][age]
                    fracCovered = self.baselineCov[program]
                    fracThisCatAge =  self.wastingDist[age][wastingCat]
                    pn, pc = self._solveQuadratic(OR, fracCovered, fracThisCatAge)
                    conditionalProb[wastingCat][program] = {}
                    conditionalProb[wastingCat][program]['covered'] = pc
                    conditionalProb[wastingCat][program]['not covered'] = pn
                    ageGroup.probConditionalCoverage.update(conditionalProb)

    def _setProbConditionalDiarrhoea(self):
        risks = ['Stunting', 'Anaemia']
        for ageGroup in self.ageGroups:
            incidence = ageGroup.incidences['Diarrhoea']
            age = ageGroup.age
            for risk in risks:
                ageGroup.probConditionalDiarrhoea[risk] = {}
                cats = self.project.riskCategories[risk]
                middle = len(cats) / 2
                relevantCats = cats[middle:] # assumes specific order and length
                dist = self.project.riskDistributions[risk]
                Z0 = ageGroup._getZa()
                Zt = Z0 # true for initialisation
                beta = ageGroup._getFracDiarrhoea(Z0, Zt)
                if risk == 'Anaemia':  # anaemia only caused by severe diarrhea
                    Yt = Zt * self.project.demographics['fraction severe diarrhoea']
                else:
                    Yt = Zt
                AO = ageGroup._getAverageOR(Yt, risk)
                fracDiarrhoea = sum(beta[bfCat] * ageGroup.bfDist[bfCat] for bfCat in self.const.bfList)
                fracImpactedThisAge = sum(dist[age][cat] for cat in relevantCats)
                pn, pc = self._solveQuadratic(AO, fracDiarrhoea, fracImpactedThisAge)
                ageGroup.probConditionalDiarrhoea[risk]['diarrhoea'] = pc
                ageGroup.probConditionalDiarrhoea[risk]['no diarrhoea'] = pn

    def _setProbWastedIfDiarrhoea(self):
        for ageGroup in self.ageGroups:
            Z0 = ageGroup._getZa()
            Zt = Z0 # true for initialisation
            beta = ageGroup._getFracDiarrhoea(Z0, Zt)
            for wastingCat in self.const.wastedList:
                A0 = ageGroup._getAverageOR(Zt, wastingCat)
                ageGroup.probConditionalDiarrhoea[wastingCat] = {}
                fracDiarrhoea = sum(beta[bfCat] * ageGroup.bfDist[bfCat] for bfCat in self.const.bfList)
                fracThisCat = ageGroup.wastingDist[wastingCat]
                pn, pc = self._solveQuadratic(A0, fracDiarrhoea, fracThisCat)
                ageGroup.probConditionalDiarrhoea[wastingCat]['no diarrhoea'] = pn
                ageGroup.probConditionalDiarrhoea[wastingCat]['diarrhoea'] = pc

    def _setProbStuntedAtBirth(self):
        """Sets the probabilty of stunting conditional on birth outcome"""
        coeffs = self._getBirthStuntingQuarticCoefficients()
        p0 = self._getBaselineProbabilityViaQuartic(coeffs)
        probStuntedAtBirth = {}
        probStuntedAtBirth['Term AGA'] = p0
        for BO in ["Pre-term SGA","Pre-term AGA","Term SGA"]:
            OR = self.const.ORconditionBirth['stunting'][BO]
            probStuntedAtBirth[BO] = p0*OR / (1.-p0+OR*p0)
            pi = probStuntedAtBirth[BO]
            if(pi<0. or pi>1.):
                raise ValueError("probability of stunting at birth, at outcome %s, is out of range (%f)"%(BO, pi))
        self.probRiskAtBirth['Stunting'] = probStuntedAtBirth

    def _setProbWastedAtBirth(self):
        probWastedAtBirth = {}
        for wastingCat in self.const.wastedList:
            coEffs = self._getBirthWastingQuarticCoefficients(wastingCat)
            p0 = self._getBaselineProbabilityViaQuartic(coEffs)
            probWastedAtBirth[wastingCat] = {}
            probWastedAtBirth[wastingCat]['Term AGA'] = p0
            for birthOutcome in ["Pre-term SGA","Pre-term AGA","Term SGA"]:
                probWastedAtBirth[wastingCat][birthOutcome] = {}
                OR = self.project.ORconditionBirth[wastingCat][birthOutcome]
                probWastedAtBirth[wastingCat][birthOutcome] = p0*OR / (1.-p0+OR*p0)
                pi = p0*OR / (1.-p0+OR*p0)
                if(pi<0. or pi>1.):
                    raise ValueError("probability of wasting at birth, at outcome %s, is out of range (%f)"%(birthOutcome, pi))
        self.probRiskAtBirth['Wasting'] = probWastedAtBirth

    def _getBirthStuntingQuarticCoefficients(self):
        OR = [1.]*4
        OR[0] = 1.
        OR[1] = self.const.ORstuntingBO["Term SGA"]
        OR[2] = self.const.ORstuntingBO["Pre-term AGA"]
        OR[3] = self.const.ORstuntingBO["Pre-term SGA"]
        FracBO = [0.]*4
        FracBO[1] = self.birthDist["Term SGA"]
        FracBO[2] = self.birthDist["Pre-term AGA"]
        FracBO[3] = self.birthDist["Pre-term SGA"]
        FracBO[0] = 1. - sum(FracBO[1:3])
        fracStunted = self.getFracStuntedGivenAge('<1 month')
        # [i] will refer to the three non-baseline birth outcomes
        A = FracBO[0]*(OR[1]-1.)*(OR[2]-1.)*(OR[3]-1.)
        B = (OR[1]-1.)*(OR[2]-1.)*(OR[3]-1.) * ( \
            sum( FracBO[0] / (OR[i]-1.)         for i in (1,2,3)) + \
            sum( OR[i] * FracBO[i] / (OR[i]-1.) for i in (1,2,3)) - \
            fracStunted )
        C = sum( FracBO[0] * (OR[i]-1.)         for i in (1,2,3)) + \
            sum( OR[i] * FracBO[i] * ((OR[1]-1.)+(OR[2]-1.)+(OR[3]-1.)-(OR[i]-1.)) for i in (1,2,3) ) - \
            sum( fracStunted*(OR[1]-1.)*(OR[2]-1.)*(OR[3]-1.)/(OR[i]-1.) for i in (1,2,3))
        D = FracBO[0] + \
            sum( OR[i] * FracBO[i] for i in (1,2,3)) - \
            sum( fracStunted * (OR[i]-1.) for i in (1,2,3))
        E = -fracStunted
        return [A,B,C,D,E]

    def _getBirthWastingQuarticCoefficients(self, wastingCat):
        FracBO = [0.]*4
        FracBO[1] = self.birthDist["Term SGA"]
        FracBO[2] = self.birthDist["Pre-term AGA"]
        FracBO[3] = self.birthDist["Pre-term SGA"]
        FracBO[0] = 1. - sum(FracBO[1:3])
        OR = [1.]*4
        OR[0] = 1.
        OR[1] = self.const.ORconditionBirth[wastingCat]["Term SGA"]
        OR[2] = self.const.ORconditionBirth[wastingCat]["Pre-term AGA"]
        OR[3] = self.const.ORconditionBirth[wastingCat]["Pre-term SGA"]
        fracWasted = self.getFracStuntedGivenAge('<1 month')
        # [i] will refer to the three non-baseline birth outcomes
        A = FracBO[0]*(OR[1]-1.)*(OR[2]-1.)*(OR[3]-1.)
        B = (OR[1]-1.)*(OR[2]-1.)*(OR[3]-1.) * ( \
            sum( FracBO[0] / (OR[i]-1.)         for i in (1,2,3)) + \
            sum( OR[i] * FracBO[i] / (OR[i]-1.) for i in (1,2,3)) - \
            fracWasted )
        C = sum( FracBO[0] * (OR[i]-1.)         for i in (1,2,3)) + \
            sum( OR[i] * FracBO[i] * ((OR[1]-1.)+(OR[2]-1.)+(OR[3]-1.)-(OR[i]-1.)) for i in (1,2,3) ) - \
            sum( fracWasted*(OR[1]-1.)*(OR[2]-1.)*(OR[3]-1.)/(OR[i]-1.) for i in (1,2,3))
        D = FracBO[0] + \
            sum( OR[i] * FracBO[i] for i in (1,2,3)) - \
            sum( fracWasted * (OR[i]-1.) for i in (1,2,3))
        E = -fracWasted
        return [A,B,C,D,E]

    def _getBaselineProbabilityViaQuartic(self, coEffs):
        from numpy import sqrt, isnan
        baselineProbability = 0
        # if any CoEffs are nan then baseline prob is -E (initial % stunted)
        if isnan(coEffs).any():
            baselineProbability = -coEffs[4]
            return baselineProbability
        tolerance = 0.00001
        p0min = 0.
        p0max = 1.
        interval = p0max - p0min
        if self._evalQuartic(p0min, coEffs)==0:
            baselineProbability = p0min
            return baselineProbability
        if self._evalQuartic(p0max, coEffs)==0:
            baselineProbability = p0max
            return baselineProbability
        PositiveAtMin = self._evalQuartic(p0min, coEffs)>0
        PositiveAtMax = self._evalQuartic(p0max, coEffs)>0
        if(PositiveAtMin == PositiveAtMax):
            raise ValueError("ERROR: Quartic function evaluated at 0 & 1 both on the same side")
        while interval > tolerance:
            p0x = (p0max+p0min)/2.
            PositiveAtP0 = self._evalQuartic(p0x, coEffs)>0
            if(PositiveAtP0 == PositiveAtMin):
                p0min = p0x
                PositiveAtMin = self._evalQuartic(p0min, coEffs)>0
            else:
                p0max = p0x
                PositiveAtMax = self._evalQuartic(p0max, coEffs)>0
            interval = p0max - p0min
        baselineProbability = p0x
        # Check 2nd deriv has no solutions between 0 and 1
        A,B,C,D,E = coEffs
        AA = 4.*3.*A
        BB = 3.*2.*B
        CC = 2.*C
        det = sqrt(BB**2 - 4.*AA*CC)
        soln1 = (-BB + det)/(2.*AA)
        soln2 = (-BB - det)/(2.*AA)
        if((soln1>0.)and(soln1<1.)):
            print "Warning problem with solving Quartic, see soln1"
        if((soln2>0.)and(soln2<1.)):
            print "Warning problem with solving Quartic, see soln2"
        return baselineProbability

    def _evalQuartic(self, p0, coEffs):
        from math import pow
        A,B,C,D,E = coEffs
        return A*pow(p0,4) + B*pow(p0,3) + C*pow(p0,2) + D*p0 + E

    def _setProgramEffectiveness(self):
        for ageGroup in self.ageGroups:
            age = ageGroup.age
            ageGroup.programEffectiveness = self.project.childPrograms[age]

    def _setCorrectBFpractice(self):
        for ageGroup in self.ageGroups:
            age = ageGroup.age
            ageGroup.correctBFpractice = self.project.correctBF[age]

class PregnantWomen(Population):
    def __init__(self, name, project, constants):
        super(PregnantWomen, self).__init__(name, project, constants)
        self.ageGroups = []
        self._makePopSizes()
        self._makeBoxes()
        self._setPWReferenceMortality()
        self._updateMortalityRates()
        self._setProbAnaemicIfCovered()

    # ##### PROGRAM UPDATES #####
    #
    # def _update(self, programInfo):
    #     """Update all the age group parameters based upon risk area.  """
    #     for risk in self.const.risks:
    #         # first get relevant programs, determined by risk area
    #         applicableProgs = self._getApplicablePrograms(risk, programInfo)
    #         for ageGroup in self.ageGroups:
    #             for program in applicableProgs:
    #                 # TODO: could put in check to see if ageGroup is impacted by program or not...
    #                 program._updateAgeGroup(ageGroup, risk)
    #     self._updateMortalityRates()

    ##### DATA WRANGLING ######

    def _makePopSizes(self):
        PWpop = self.project.populationByAge
        self.popSizes = {age:pop for age, pop in PWpop.iteritems()}

    def _makeBoxes(self):
        for idx in range(len(self.const.PWages)):
            age = self.const.PWages[idx]
            popSize = self.popSizes[age]
            boxes = {}
            anaemiaDist = self.anaemiaDist[age]
            ageingRate = self.const.womenAgeingRates[idx]
            for anaemiaCat in self.const.anaemiaList:
                thisPop = popSize * anaemiaDist[anaemiaCat]
                boxes[anaemiaCat] = Box(thisPop)
            self.ageGroups.append(WomenAgeGroup(age, popSize, boxes, anaemiaDist, ageingRate, self.const))

    def _setPWReferenceMortality(self):
        #Equation is:  LHS = RHS * X
        #we are solving for X
        # Calculate RHS for each age and cause
        RHS = {}
        for age in self.const.PWages:
            RHS[age] = {}
            for cause in self.project.causesOfDeath:
                RHS[age][cause] = 0.
                for anaemiaCat in self.const.anaemiaList:
                    t1 = self.anaemiaDist[age][anaemiaCat]
                    t2 = self.project.RRdeath['Anaemia'][cause][anaemiaCat][age]
                    RHS[age][cause] += t1 * t2
        # get age populations
        agePop = [age.populationSize for age in self.ageGroups]
        # Correct raw mortality for units (per 1000 live births)
        liveBirths = self.project.demographics['number of live births']
        # The following assumes we only have a single mortality rate for PW
        mortalityRate = self.project.mortalityRates['maternal mortality']
        mortalityCorrected = {}
        for index in range(len(self.const.PWages)):
            age = self.const.PWages[index]
            if index == 0:
                mortalityCorrected[age] = (mortalityRate * liveBirths / 1000.) * (4. / 34.) / agePop[index]
            else:
                mortalityCorrected[age] = (mortalityRate * liveBirths / 1000.) * (9. / 34.) / agePop[index]

        # Calculate LHS for each age and cause of death then solve for X
        Xdictionary = {}
        for age in self.const.PWages:
            Xdictionary[age] = {}
            for cause in self.project.causesOfDeath:
                LHS_age_cause = mortalityCorrected[age] * self.project.deathDist[cause][age]
                Xdictionary[age][cause] = LHS_age_cause / RHS[age][cause]
        self.referenceMortality = Xdictionary

    def _updateMortalityRates(self):
        for ageGroup in self.ageGroups:
            age = ageGroup.age
            for anaemiaCat in self.const.anaemiaList:
                count = 0
                for cause in self.project.causesOfDeath:
                    t1 = self.referenceMortality[age][cause]
                    t2 = self.project.RRdeath['Anaemia'][cause][anaemiaCat][age]
                    count += t1 * t2
                ageGroup.boxes[anaemiaCat].mortalityRate = count

    def _setProbAnaemicIfCovered(self):
        risk = 'Anaemia'
        for ageGroup in self.ageGroups:
            age = ageGroup.age
            for program in self.project.programList:
                ageGroup.probConditionalCoverage[program] = {}
                fracCovered = self.baselineCov[program]
                fracImpacted = sum(self.anaemiaDist[age][cat] for cat in self.const.anaemicList)
                if self.project.ORprograms[risk].get(program) is None:
                    RR = self.project.RRprograms[risk][program][age]
                    pn = fracImpacted / (RR * fracCovered + (1. - fracCovered))
                    pc = RR * pn
                else:
                    OR = self.project.ORprograms[risk][program][age]
                    pn, pc = self._solveQuadratic(OR, fracCovered, fracImpacted)
                ageGroup.probConditionalCoverage[program]['covered'] = pc
                ageGroup.probConditionalCoverage[program]['not covered'] = pn

class NonPregnantWomen(Population):
    def __init__(self, name, project, constants):
        super(NonPregnantWomen, self).__init__(name, project, constants)
        self.ageGroups = []
        self._makePopSizes()
        self._makeBoxes()

    ##### PROGRAM UPDATES #####

    def _update(self, programInfo):
        """Update all the age group parameters based upon risk area.  """
        for risk in self.const.risks:
            # first get relevant programs, determined by risk area
            applicableProgs = self._getApplicablePrograms(risk, programInfo)
            for ageGroup in self.ageGroups:
                for program in applicableProgs:
                    # TODO: could put in check to see if ageGroup is impacted by program or not...
                    program._updateAgeGroup(ageGroup, risk)


    ##### DATA WRANGLING ######

    def _makePopSizes(self):
        WRApop = self.project.populationByAge
        self.popSizes = {age:pop for age, pop in WRApop.iteritems()}

    def _makeBoxes(self):
        for age in self.const.WRAages:
            popSize = self.popSizes[age]
            boxes = {}
            anaemiaDist = self.anaemiaDist[age]
            for anaemiaCat in self.const.anaemicList:
                thisPop = popSize * anaemiaDist[anaemiaCat]
                boxes[anaemiaCat] = Box(thisPop)
            self.ageGroups.append(WomenAgeGroup(age, popSize, boxes, anaemiaDist))



def setUpPopulations(project, constants):
    children = Children('Children', project, constants)
    pregnantWomen = PregnantWomen('Pregnant women', project, constants)
    nonPregnantWomen = NonPregnantWomen('Non-pregnant women', project, constants)
    return [children, pregnantWomen, nonPregnantWomen]