from copy import deepcopy as dcp
class Constants:
    """Thie class contains all the constants (lists of categories mostly) to be used across many classes"""
    def __init__(self, data):
        self.allYears = dcp(data.simulationYears)
        self.baselineYear = int(dcp(data.year))
        if self.baselineYear == self.allYears[0]: # demographic projection data includes baseline
            self.calibrationYears = self.allYears[1:2] # year before coverage change
            self.simulationYears = self.allYears[2:] # year after coverage change
        else:
            self.calibrationYears = self.allYears[:1] # year before coverage change
            self.simulationYears = self.allYears[1:] # year after coverage change
        self.stuntingList = dcp(data.riskCategories['Stunting'])
        self.wastingList = dcp(data.riskCategories['Wasting'])
        self.bfList = dcp(data.riskCategories['Breastfeeding'])
        self.anaemiaList = dcp(data.riskCategories['Anaemia'])
        self.birthOutcomes = dcp(data.riskCategories['Birth outcomes'])
        self.stuntedList = self.stuntingList[2:]
        self.notStuntedList = self.stuntingList[:2]
        self.wastedList = self.wastingList[2:]
        self.nonWastedList = self.wastingList[:2]
        self.anaemicList = self.anaemiaList[1:]
        self.nonAnaemicList = self.anaemiaList[:1]
        self.allRisks = [self.stuntingList, self.wastingList, self.bfList, self.anaemiaList]
        self.childAges = dcp(data.childAges)
        self.PWages = dcp(data.PWages)
        self.WRAages = dcp(data.WRAages)
        self.allAges = self.childAges + self.PWages + self.WRAages
        self.timestep = 1./12.
        self.causesOfDeath = dcp(data.causesOfDeath)
        self.conditions = dcp(data.conditions)
        self.risks = ['Stunting', 'Wasting', 'Breastfeeding', 'Anaemia'] # TODO: read from spreadsheet
        self.childAgeSpans = [1., 5., 6., 12., 36.]
        self.womenAgeingRates = [1./5., 1./10., 1./10., 1./10.] # this is in years
        self.PWageDistribution = dcp(data.PWageDistribution)
        self.popProjections = dcp(data.projections)
        self.correctBF = dcp(data.correctBF)
        self.RRdiarrhoea = dcp(data.RRdeath['Child diarrhoea']['Diarrhoea incidence'])
        self.RRdeath = dcp(data.RRdeath)
        self.ORcondition = dcp(data.ORcondition)
        self.ORstuntingBO = dcp(data.ORconditionBirth['stunting'])
        self.ORconditionBirth = dcp(data.ORconditionBirth)
        self.BOprograms = dcp(data.BOprograms)
        self.demographics = dcp(data.demographics)
        self.famPlanMethods = dcp(data.famPlanMethods)
        self.RRageOrder = dcp(data.RRageOrder)
        self.RRinterval = dcp(data.RRinterval)
        self.birthAges = dcp(data.birthAges)
        self.birthAgeProgram = dcp(data.birthAgeProgram)
        self.programList = dcp(data.programList)
        self.costCurveInfo = dcp(data.costCurveInfo)
        self.currentExpenditure = dcp(data.currentExpenditure)
        self.availableBudget = dcp(data.availableBudget)
        self.programTargetPop = dcp(data.programTargetPop) # frac of each population which is targeted
        self.programImpactedPop = dcp(data.programImpactedPop)
        self.programDependency = dcp(data.programDependency)
        self.programAreas = dcp(data.programAreas)
        self.referencePrograms = dcp(data.referencePrograms)
        self.programAnnualSpending = dcp(data.programAnnualSpending) # TODO: b/c not really constant, pass this into programs as different param