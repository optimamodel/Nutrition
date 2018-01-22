from copy import deepcopy as dcp
class Constants:
    """Thie class contains all the constants (lists of categories mostly) to be used across many classes"""
    def __init__(self, project):
        self.stuntingList = dcp(project.riskCategories['Stunting'])
        self.wastingList = dcp(project.riskCategories['Wasting'])
        self.bfList = dcp(project.riskCategories['Breastfeeding'])
        self.anaemiaList = dcp(project.riskCategories['Anaemia'])
        self.birthOutcomes = dcp(project.riskCategories['Birth outcomes'])
        self.stuntedList = self.stuntingList[2:]
        self.notStuntedList = self.stuntingList[:2]
        self.wastedList = self.wastingList[2:]
        self.nonWastedList = self.wastingList[:2]
        self.anaemicList = self.anaemiaList[1:]
        self.allRisks = [self.stuntingList, self.wastingList, self.bfList, self.anaemiaList]
        self.childAges = dcp(project.childAges)
        self.PWages = dcp(project.PWages)
        self.WRAages = dcp(project.WRAages)
        self.allAges = self.childAges + self.PWages + self.WRAages
        self.timestep = 1./12.
        self.causesOfDeath = dcp(project.causesOfDeath)
        self.conditions = dcp(project.conditions)
        self.risks = ['Stunting', 'Wasting', 'Breastfeeding', 'Anaemia'] # TODO: read from spreadsheet
        self.childAgeSpans = [1., 5., 6., 12., 36.]
        self.womenAgeingRates = [1./5., 1./10., 1./10., 1./10.] # this is in years
        self.PWageDistribution = dcp(project.PWageDistribution)
        self.popProjections = dcp(project.projections)
        self.correctBF = dcp(project.correctBF)
        self.RRdiarrhoea = dcp(project.RRdeath['Child diarrhoea']['Diarrhoea incidence'])
        self.RRdeath = dcp(project.RRdeath)
        self.ORcondition = dcp(project.ORcondition)
        self.ORstuntingBO = dcp(project.ORconditionBirth['stunting'])
        self.ORconditionBirth = dcp(project.ORconditionBirth)
        self.BOprograms = dcp(project.BOprograms)
        self.demographics = dcp(project.demographics)
        self.famPlanMethods = dcp(project.famPlanMethods)
        self.RRageOrder = dcp(project.RRageOrder)
        self.RRinterval = dcp(project.RRinterval)
        self.birthAges = dcp(project.birthAges)
        self.birthAgeProgram = dcp(project.birthAgeProgram)
        # self.mortalityRates = dcp(project.mortalityRates)
        self.programList = dcp(project.programList)
        self.costCurveInfo = dcp(project.costCurveInfo)
        self.programTargetPop = dcp(project.programTargetPop) # frac of each population which is targeted
        self.programImpactedPop = dcp(project.programImpactedPop)
        self.programDependency = dcp(project.programDependency)
        self.programAreas = dcp(project.programAreas)
        self.referencePrograms = dcp(project.referencePrograms)