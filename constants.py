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
        self.wastedList = self.wastingList[2:]
        self.anaemicList = self.anaemiaList[1:]
        self.allRisks = [self.stuntingList, self.wastingList, self.bfList, self.anaemiaList]
        self.childAges = dcp(project.childAges)
        self.PWages = dcp(project.PWages)
        self.WRAages = dcp(project.WRAages)
        self.causesOfDeath = dcp(project.causesOfDeath)
        self.risks = ['Stunting', 'Wasting', 'Breastfeeding', 'Anaemia'] # TODO: read from spreadsheet
        self.childAgeSpans = [1., 5., 6., 12., 36.]