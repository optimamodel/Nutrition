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
        self.stuntedList = self.stuntingList[2:]
        self.wastedList = self.wastingList[2:]
        self.anemicList = self.anaemiaList[:1]
        self.allRisks = [self.stuntingList, self.wastingList, self.bfList, self.anaemiaList]
        self.birthOutcomes = ["Pre-term SGA", "Pre-term AGA", "Term SGA", "Term AGA"]
        self.boxes = {}
        self.ageGroups = []

    def _getPopulation(self, ages, riskLists):
        from itertools import product
        allCombinations = product(*[ages, riskLists])
        populationSize = sum([self.boxes[age][cat] for age, cat in allCombinations])
        return populationSize

    def getDistribution(self, risk):
        return self.project.riskDistributions[risk]

class Children(Population):
    def __init__(self, name, project):
        super(Children, self).__init__(name, project)
        self.ageSpans = [1., 5., 6., 12., 36.]
        self._makePopSizes()
        self._makeBoxes()
        self._setChildrenReferenceMortality()
        self._updateMortalityRates()

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

    def _setChildrenReferenceMortality(self): # TODO: TEST
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

    def _updateMortalityRates(self): # TODO: TEST
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




    def _getPopulation(self, ages, risks):
        from operator import itemgetter
        groups = set(ages)
        idxs = [i for i, item in enumerate(self.childAges) if item in groups]
        theseGroups = itemgetter(*idxs)(self.ageGroups)
        populationSize = sum([group.boxes[stuntingCat][wastingCat][bfCat][anaemiaCat].populationSize
                              for group in theseGroups for stuntingCat, wastingCat, bfCat, anaemiaCat in product(*risks)])
        return populationSize

    def getTotalPopulation(self):
        allRisks = [self.stuntingList, self.wastingList, self.bfList, self.anaemiaList]
        return self._getPopulation(self.childAges, allRisks)

    def getTotalStunted(self):
        risks = self._replaceRiskList(0, self.stuntedList)
        return self._getPopulation(self.childAges, risks)

    def getTotalWasted(self):
        risks = self._replaceRiskList(1, self.wastedList)
        return self._getPopulation(self.childAges, risks)

    def getTotalAnaemic(self):
        risks = self._replaceRiskList(3, self.anemicList)
        return self._getPopulation(self.childAges, risks)

    def _replaceRiskList(self, index, newList):
        return self.allRisks[:index] + [newList] + self.allRisks[index+1:]

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
        self._makePopSizes()
        self._makeBoxes()

    def _makePopSizes(self):
        PWpop = self.project.ageDistributions
        self.popSizes = {age:pop for age, pop in PWpop.iteritems()}

    def _makeBoxes(self):
        for age in self.project.PWages:
            popSize = self.popSizes[age]
            self.boxes[age] = {}
            for anaemiaCat in self.anaemiaList:
                thisPop = popSize * self.anaemiaDist[anaemiaCat][age]
                self.boxes[age][anaemiaCat] = Box(thisPop)

    # def _updateMortalityRates(self): # TODO: needs to be adjusted
    #     for ageGroup in self.listOfPregnantWomenAgeCompartments:
    #         ageName = ageGroup.name
    #         for anemiaStatus in self.anemiaList:
    #             count = 0
    #             for cause in self.params.causesOfDeath:
    #                 t1 = self.derived.referenceMortality[ageName][cause]
    #                 t2 = self.params.RRdeathAnemia[ageName][cause][anemiaStatus]
    #                 count += t1 * t2
    #             ageGroup.dictOfBoxes[anemiaStatus].mortalityRate = count


class WRA(Population):
    def __init__(self, name, project):
        super(WRA, self).__init__(name, project)
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

