from itertools import product

class Box:
    def __init__(self, populationSize):
        self.populationSize = populationSize
        self.mortalityRate = None
        self.cumulativeDeaths = 0

class AgeGroup:
    def __init__(self, age, populationSize, boxes):
        self.age = age
        self.populationSize = populationSize
        self.boxes = boxes


class Population(object):
    def __init__(self, name, project):
        self.name = name
        self.project = project
        self.childAges = project.childAges
        self.PWages = project.PWages
        self.WRAages = project.WRAages
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
        self.popSizes = {age:pop for age, pop in zip(self.project.PWages, PWpop)}

    def _makeBoxes(self):
        for idx in range(len(self.popSizes)):
            ageName = self.project.PWages[idx]
            popSize = self.popSizes[idx]
            self.boxes[ageName] = {}
            for anaemiaCat in self.anaemiaList:
                thisPop = popSize * self.anaemiaDist[anaemiaCat][ageName]
                self.boxes[ageName][anaemiaCat] = Box(thisPop)


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

