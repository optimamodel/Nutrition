from itertools import product

class Box:
    def __init__(self, populationSize):
        self.populationSize = populationSize
        self.mortalityRate = None
        self.cumulativeDeaths = 0

class AgeGroup:
    def __init__(self, age, populationSize, boxes):
        self.name = age
        self.populationSize = populationSize
        self.boxes = boxes
        self.conditionalProb = {}


class Population(object):
    def __init__(self, name, project):
        self.name = name
        self.project = project
        self.childAges = project.childAges
        self.PWages = project.PWages
        self.WRAages = project.WRAages
        self.risks = ['Stunting', 'Wasting', 'Breastfeeding', 'Anaemia']
        self.stuntingDist = project.riskDistributions['Stunting']
        self.wastingDist = project.riskDistributions['Wasting']
        self.bfDist = project.riskDistributions['Breastfeeding']
        self.anaemiaDist = project.riskDistributions['Anaemia']
        self.stuntingList = project.riskCategories['Stunting']
        self.wastingList = project.riskCategories['Wasting']
        self.bfList = project.riskCategories['Breastfeeding']
        self.anaemiaList = project.riskCategories['Anaemia']
        self.stuntedList = self.stuntingList[2:] # TODO: the structuring of this data could be improved depending on usage below
        self.wastedList = self.wastingList[2:]
        self.anaemicList = self.anaemiaList[1:]
        self.allRisks = [self.stuntingList, self.wastingList, self.bfList, self.anaemiaList]
        self.ORstuntingBO = project.ORconditionBirth['stunting']
        self.birthOutcomes = ["Pre-term SGA", "Pre-term AGA", "Term SGA", "Term AGA"]
        self.baselineCov = project.costCurveInfo['baseline coverage']
        self.boxes = {}

    def _getPopulation(self, ages, riskLists):
        from itertools import product
        allCombinations = product(*[ages, riskLists])
        populationSize = sum([self.boxes[age][cat] for age, cat in allCombinations])
        return populationSize

    def getDistribution(self, risk):
        return self.project.riskDistributions[risk]

    def solveQuadratic(self, oddsRatio, fracA, fracB):
        # solves quadratic to calculate probabilities where e.g.:
        # fracA is fraction covered by intervention
        # fracB is fraction of pop. in a particular risk status
        from numpy import sqrt, roots
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
    def __init__(self, name, project):
        super(Children, self).__init__(name, project)
        self.ageSpans = [1., 5., 6., 12., 36.]
        self.ageGroups = []
        self._makePopSizes()
        self._makeBoxes()
        self._setChildrenReferenceMortality()
        self._updateMortalityRates()
        self._setProbConditionalCoverage()
        self._setProbWastedIfCovered()
        self._setProbStuntedAtBirth()
        self._setProbWastedAtBirth()

    def _makePopSizes(self):
        # for children less than 1 year, annual live births
        monthlyBirths = self.project.demographics['number of live births'] / 12.
        popSize = [pop * monthlyBirths for pop in self.ageSpans[:3]]
        # children > 1 year, who are not counted in annual 'live births'
        months = sum(self.ageSpans[3:])
        popRemainder = self.project.demographics['population U5'] - monthlyBirths * 12.
        monthlyRate = popRemainder/months
        popSize += [pop * monthlyRate for pop in self.ageSpans[3:]]
        self.popSizes = {age:pop for age, pop in zip(self.project.childAges, popSize)}

    def _makeBoxes(self):
        for age in self.project.childAges:
            popSize = self.popSizes[age]
            boxes = {}
            for stuntingCat in self.stuntingList:
                boxes[stuntingCat] = {}
                for wastingCat in self.wastingList:
                    boxes[stuntingCat][wastingCat] = {}
                    for bfCat in self.bfList:
                        boxes[stuntingCat][wastingCat][bfCat] = {}
                        for anaemiaCat in self.anaemiaList:
                            thisPop = popSize * self.stuntingDist[stuntingCat][age] *\
                                      self.wastingDist[wastingCat][age] * self.bfDist[bfCat][age] * \
                                      self.anaemiaDist[anaemiaCat][age]
                            boxes[stuntingCat][wastingCat][bfCat][anaemiaCat] = Box(thisPop)
            self.ageGroups.append(AgeGroup(age, popSize, boxes))

    def _setChildrenReferenceMortality(self):
        # Equation is:  LHS = RHS * X
        # we are solving for X
        # Calculate RHS for each age and cause
        RHS = {}
        for age in self.childAges:
            RHS[age] = {}
            for cause in self.project.causesOfDeath:
                RHS[age][cause] = 0.
                for stuntingCat in self.stuntingList:
                    for wastingCat in self.wastingList:
                        for bfCat in self.bfList:
                            for anaemiaCat in self.anaemiaList:
                                t1 = self.stuntingDist[stuntingCat][age]
                                t2 = self.wastingDist[wastingCat][age]
                                t3 = self.bfDist[bfCat][age]
                                t4 = self.anaemiaDist[anaemiaCat][age]
                                t5 = self.project.RRdeath['Stunting'][cause][stuntingCat][age]
                                t6 = self.project.RRdeath['Wasting'][cause][wastingCat][age]
                                t7 = self.project.RRdeath['Breastfeeding'][cause][bfCat][age]
                                t8 = self.project.RRdeath['Anaemia'][cause][anaemiaCat][age]
                                RHS[age][cause] += t1 * t2 * t3 * t4 * t5 * t6 * t7 * t8
        # RHS for newborns only
        age = '<1 month'
        for cause in self.project.causesOfDeath:
            RHS[age][cause] = 0.
            for breastfeedingCat in self.bfList:
                Pbf = self.bfDist[breastfeedingCat][age]
                RRbf = self.project.RRdeath['Breastfeeding'][cause][breastfeedingCat][age]
                for birthoutcome in self.birthOutcomes:
                    Pbo = self.project.birthDist[birthoutcome]
                    RRbo = self.project.RRdeath['Birth outcomes'][cause][birthoutcome]
                    for anemiaStatus in self.anaemiaList:
                        Pan = self.anaemiaDist[anemiaStatus][age]
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
        ageName = self.ageGroups[0].name
        m0 = Mnew * LiveBirths / 1000. / AgePop[0]
        MortalityCorrected[ageName] = m0
        # 1-5 months
        ageName = self.ageGroups[1].name
        m1 = (Minfant - Mnew) * LiveBirths / 1000. * 5. / 11. / AgePop[1]
        MortalityCorrected[ageName] = m1
        # 6-12 months
        ageName = self.ageGroups[2].name
        m2 = (Minfant - Mnew) * LiveBirths / 1000. * 6. / 11. / AgePop[2]
        MortalityCorrected[ageName] = m2
        # 12-24 months
        ageName = self.ageGroups[3].name
        m3 = (Mu5 - Minfant) * LiveBirths / 1000. * 1. / 4. / AgePop[3]
        MortalityCorrected[ageName] = m3
        # 24-60 months
        ageName = self.ageGroups[4].name
        m4 = (Mu5 - Minfant) * LiveBirths / 1000. * 3. / 4. / AgePop[4]
        MortalityCorrected[ageName] = m4
        # Calculate LHS for each age and cause of death then solve for X
        Xdictionary = {}
        for age in self.childAges:
            Xdictionary[age] = {}
            for cause in self.project.causesOfDeath:
                LHS_age_cause = MortalityCorrected[age] * self.project.deathDist[cause][age]
                Xdictionary[age][cause] = LHS_age_cause / RHS[age][cause]
        self.referenceMortality = Xdictionary

    def _updateMortalityRates(self):
        # Newborns first
        ageGroup = self.ageGroups[0]
        age = ageGroup.name
        for bfCat in self.bfList:
            count = 0.
            for cause in self.project.causesOfDeath:
                Rb = self.project.RRdeath['Breastfeeding'][cause][bfCat][age]
                for outcome in self.birthOutcomes:
                    pbo = self.project.birthDist[outcome]
                    Rbo = self.project.RRdeath['Birth outcomes'][cause][outcome]
                    count += Rb * pbo * Rbo * self.referenceMortality[age][cause]
            for stuntingCat in self.stuntingList:
                for wastingCat in self.wastingList:
                    for anaemiaCat in self.anaemiaList:
                        ageGroup.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].mortalityRate = count
        # over 1 months
        for ageGroup in self.ageGroups[1:]:
            age = ageGroup.name
            for stuntingCat in self.stuntingList:
                for wastingCat in self.wastingList:
                    for bfCat in self.bfList:
                        for anemiaStatus in self.anaemiaList:
                            count = 0.
                            for cause in self.project.causesOfDeath:
                                t1 = self.referenceMortality[age][cause]
                                t2 = self.project.RRdeath['Stunting'][cause][stuntingCat][age]
                                t3 = self.project.RRdeath['Wasting'][cause][wastingCat][age]
                                t4 = self.project.RRdeath['Breastfeeding'][cause][bfCat][age]
                                t5 = self.project.RRdeath['Anaemia'][cause][anemiaStatus][age]
                                count += t1 * t2 * t3 * t4 * t5
                            ageGroup.boxes[stuntingCat][wastingCat][bfCat][anemiaStatus].mortalityRate = count

    def _getPopulation(self, ageGroups, risks):
        """ Get population size for given age groups and combinations of given risks"""
        populationSize = sum([group.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize
                              for group in ageGroups for stuntingCat, wastingCat, bfCat, anaemiaCat in product(*risks)])
        return populationSize

    def getTotalPopulation(self):
        return self._getPopulation(self.ageGroups, self.allRisks)

    def getTotalNumberStunted(self):
        risks = self._replaceRiskList(0, self.stuntedList)
        return self._getPopulation(self.ageGroups, risks)

    def getTotalFracStunted(self):
        return self.getTotalNumberStunted() / self.getTotalPopulation()

    def getFracStuntedFirstCompartment(self):
        risks = self._replaceRiskList(0, self.stuntedList)
        firstComp = self.ageGroups[0]
        return self._getPopulation([firstComp], risks) / firstComp.populationSize

    def getTotalWasted(self):
        risks = self._replaceRiskList(1, self.wastedList)
        return self._getPopulation(self.ageGroups, risks)

    def getFracWastedFirstCompartment(self):
        risks = self._replaceRiskList(1, self.wastedList)
        firstComp = self.ageGroups[0]
        return self._getPopulation([firstComp], risks) / firstComp.populationSize

    def getTotalAnaemic(self):
        risks = self._replaceRiskList(3, self.anaemicList)
        return self._getPopulation(self.ageGroups, risks)

    def _replaceRiskList(self, index, newList):
        """replaces one risk list in a list of risk lists. index is the position of list to replace """
        alteredList = self.allRisks[:]
        alteredList[index] = newList
        return alteredList

    def _setProbConditionalCoverage(self):
        """Set the conditional probabilities of a risk factor (except wasting) given program coverage.
        Note that this value is dependent upon the baseline coverage of the program"""
        risks = [risk for i, risk in enumerate(self.risks) if i !=1 ] # remove wasting
        conditionalProb = {}
        for risk in risks:
            cats = self.project.riskCategories[risk]# TODO: Could use a better data construction back in the Population class
            middle = len(cats) / 2
            relevantCats = cats[middle:] # assumes list is symmetric
            dist = self.project.riskDistributions[risk]
            conditionalProb[risk] = {}
            for ageGroup in self.ageGroups:
                age = ageGroup.name
                for program in self.project.programList:
                    # data
                    OR = self.project.ORstuntingProgram[program][age]
                    fracCovered = self.baselineCov[program]
                    fracImpacted = sum(dist[cat][age] for cat in relevantCats)
                    pn, pc = self.solveQuadratic(OR, fracCovered, fracImpacted) # TODO: could use the numpy roots here.
                    conditionalProb[risk][program] = {}
                    conditionalProb[risk][program]['covered'] = pc
                    conditionalProb[risk][program]['not covered'] = pn
                ageGroup.conditionalProb.update(conditionalProb)

    def _setProbWastedIfCovered(self):
        for wastingCat in self.wastedList:
            conditionalProb = {}
            conditionalProb[wastingCat] = {}
            for ageGroup in self.ageGroups:
                age = ageGroup.name
                for program in self.project.programList:
                    #data
                    OR = self.project.ORwastingProgram[wastingCat][program][age]
                    fracCovered = self.baselineCov[program]
                    fracThisCatAge =  self.wastingDist[wastingCat][age]
                    pn, pc = self.solveQuadratic(OR, fracCovered, fracThisCatAge)
                    conditionalProb[wastingCat][program] = {}
                    conditionalProb[wastingCat][program]['covered'] = pc
                    conditionalProb[wastingCat][program]['not covered'] = pn
                    ageGroup.conditionalProb.update(conditionalProb)

    def _setProbConditionalDiarrhoea(self):
        


    def _setProbStuntedAtBirth(self):
        """Sets the probabilty of stunting conditional on birth outcome"""
        #from numpy import roots
        coeffs = self.getBirthStuntingQuarticCoefficients()
        #p0 = roots(coeffs) # TODO: the same solution can be found with in-built solver, but need to look into all the checks from manual function
        p0 = self.getBaselineProbabilityViaQuartic(coeffs)
        probStuntedAtBirth = {}
        probStuntedAtBirth['Term AGA'] = p0
        for BO in ["Pre-term SGA","Pre-term AGA","Term SGA"]:
            OR = self.project.ORconditionBirth['stunting'][BO]
            probStuntedAtBirth[BO] = p0*OR / (1.-p0+OR*p0)
            pi = probStuntedAtBirth[BO]
            if(pi<0. or pi>1.):
                raise ValueError("probability of stunting at birth, at outcome %s, is out of range (%f)"%(BO, pi))

    def _setProbWastedAtBirth(self):
        probWastedAtBirth = {}
        for wastingCat in self.wastedList:
            coEffs = self.getBirthWastingQuarticCoefficients(wastingCat)
            p0 = self.getBaselineProbabilityViaQuartic(coEffs)
            probWastedAtBirth[wastingCat] = {}
            probWastedAtBirth[wastingCat]['Term AGA'] = p0
            for birthOutcome in ["Pre-term SGA","Pre-term AGA","Term SGA"]:
                probWastedAtBirth[wastingCat][birthOutcome] = {}
                OR = self.project.ORconditionBirth[wastingCat][birthOutcome]
                probWastedAtBirth[wastingCat][birthOutcome] = p0*OR / (1.-p0+OR*p0)
                pi = p0*OR / (1.-p0+OR*p0)
                if(pi<0. or pi>1.):
                    raise ValueError("probability of wasting at birth, at outcome %s, is out of range (%f)"%(birthOutcome, pi))
        self.probWastedAtBirth = probWastedAtBirth

    def getBirthStuntingQuarticCoefficients(self):
        OR = [1.]*4
        OR[0] = 1.
        OR[1] = self.ORstuntingBO["Term SGA"]
        OR[2] = self.ORstuntingBO["Pre-term AGA"]
        OR[3] = self.ORstuntingBO["Pre-term SGA"]
        FracBO = [0.]*4
        FracBO[1] = self.project.birthDist["Term SGA"]
        FracBO[2] = self.project.birthDist["Pre-term AGA"]
        FracBO[3] = self.project.birthDist["Pre-term SGA"]
        FracBO[0] = 1. - sum(FracBO[1:3])
        fracStunted = self.getFracStuntedFirstCompartment()
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

    def getBirthWastingQuarticCoefficients(self, wastingCat):
        FracBO = [0.]*4
        FracBO[1] = self.project.birthDist["Term SGA"]
        FracBO[2] = self.project.birthDist["Pre-term AGA"]
        FracBO[3] = self.project.birthDist["Pre-term SGA"]
        FracBO[0] = 1. - sum(FracBO[1:3])
        OR = [1.]*4
        OR[0] = 1.
        OR[1] = self.project.ORconditionBirth[wastingCat]["Term SGA"]
        OR[2] = self.project.ORconditionBirth[wastingCat]["Pre-term AGA"]
        OR[3] = self.project.ORconditionBirth[wastingCat]["Pre-term SGA"]
        fracWasted = self.getFracWastedFirstCompartment()
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

    def getBaselineProbabilityViaQuartic(self, coEffs):
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
        if self.evalQuartic(p0min, coEffs)==0:
            baselineProbability = p0min
            return baselineProbability
        if self.evalQuartic(p0max, coEffs)==0:
            baselineProbability = p0max
            return baselineProbability
        PositiveAtMin = self.evalQuartic(p0min, coEffs)>0
        PositiveAtMax = self.evalQuartic(p0max, coEffs)>0
        if(PositiveAtMin == PositiveAtMax):
            raise ValueError("ERROR: Quartic function evaluated at 0 & 1 both on the same side")
        while interval > tolerance:
            p0x = (p0max+p0min)/2.
            PositiveAtP0 = self.evalQuartic(p0x, coEffs)>0
            if(PositiveAtP0 == PositiveAtMin):
                p0min = p0x
                PositiveAtMin = self.evalQuartic(p0min, coEffs)>0
            else:
                p0max = p0x
                PositiveAtMax = self.evalQuartic(p0max, coEffs)>0
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

    def evalQuartic(self, p0, coEffs):
        from math import pow
        A,B,C,D,E = coEffs
        return A*pow(p0,4) + B*pow(p0,3) + C*pow(p0,2) + D*p0 + E

    # Going from binary stunting/wasting to four fractions
    # Yes refers to more than 2 standard deviations below the global mean/median
    # in our notes, fractionYes = alpha
    def restratify(self, fractionYes):
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

class PW(Population):
    def __init__(self, name, project):
        super(PW, self).__init__(name, project)
        self.ageGroups = []
        self._makePopSizes()
        self._makeBoxes()
        self._setPWReferenceMortality()
        self._updateMortalityRates()

    def _makePopSizes(self):
        PWpop = self.project.ageDistributions
        self.popSizes = {age:pop for age, pop in PWpop.iteritems()}

    def _makeBoxes(self):
        for age in self.project.PWages:
            popSize = self.popSizes[age]
            boxes = {}
            for anaemiaCat in self.anaemiaList:
                thisPop = popSize * self.anaemiaDist[anaemiaCat][age]
                boxes[anaemiaCat] = Box(thisPop)
            self.ageGroups.append(AgeGroup(age, popSize, boxes))

    def _setPWReferenceMortality(self):
        #Equation is:  LHS = RHS * X
        #we are solving for X
        # Calculate RHS for each age and cause
        RHS = {}
        for age in self.PWages:
            RHS[age] = {}
            for cause in self.project.causesOfDeath:
                RHS[age][cause] = 0.
                for anaemiaCat in self.anaemiaList:
                    t1 = self.anaemiaDist[anaemiaCat][age]
                    t2 = self.project.RRdeath['Anaemia'][cause][anaemiaCat][age]
                    RHS[age][cause] += t1 * t2
        # get age populations
        agePop = [age.populationSize for age in self.ageGroups]
        # Correct raw mortality for units (per 1000 live births)
        liveBirths = self.project.demographics['number of live births']
        # The following assumes we only have a single mortality rate for PW
        mortalityRate = self.project.mortalityRates['maternal mortality']
        mortalityCorrected = {}
        for index in range(len(self.PWages)):
            age = self.PWages[index]
            if index == 0:
                mortalityCorrected[age] = (mortalityRate * liveBirths / 1000.) * (4. / 34.) / agePop[index]
            else:
                mortalityCorrected[age] = (mortalityRate * liveBirths / 1000.) * (9. / 34.) / agePop[index]

        # Calculate LHS for each age and cause of death then solve for X
        Xdictionary = {}
        for age in self.PWages:
            Xdictionary[age] = {}
            for cause in self.project.causesOfDeath:
                LHS_age_cause = mortalityCorrected[age] * self.project.deathDist[cause][age]
                Xdictionary[age][cause] = LHS_age_cause / RHS[age][cause]
        self.referenceMortality = Xdictionary

    def _updateMortalityRates(self):
        for ageGroup in self.ageGroups:
            age = ageGroup.name
            for anaemiaCat in self.anaemiaList:
                count = 0
                for cause in self.project.causesOfDeath:
                    t1 = self.referenceMortality[age][cause]
                    t2 = self.project.RRdeath['Anaemia'][cause][anaemiaCat][age]
                    count += t1 * t2
                ageGroup.boxes[anaemiaCat].mortalityRate = count


class WRA(Population):
    def __init__(self, name, project):
        super(WRA, self).__init__(name, project)
        self.ageGroups = []
        self._makePopSizes()
        self._makeBoxes()

    def _makePopSizes(self):
        WRApop = self.project.ageDistributions
        self.popSizes = {age:pop for age, pop in zip(self.project.WRAages, WRApop)}

    def _makeBoxes(self):
        for idx in range(len(self.popSizes)):
            ageName = self.project.PWages[idx]
            popSize = self.popSizes[idx]
            self.boxes[ageName] = {}
            for anaemiaCat in self.anaemiaList:
                thisPop = popSize * self.anaemiaDist[anaemiaCat][ageName]
                self.boxes[ageName][anaemiaCat] = Box(thisPop)

