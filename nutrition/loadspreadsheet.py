import os
import play
from pandas import ExcelFile

class DefaultParams(object):
    def __init__(self, country):
        # TODO: prolly need to sort this path stuff out...
        filepath = os.path.join(os.pardir, 'applications', country, 'data', 'default_params.xlsx')
        self.spreadsheet = ExcelFile(filepath)
        self.readSpreadsheet()

    def readSpreadsheet(self):
        self.impactPop()
        self.progRisks()
        self.popRisks()
        self.anaemiaProgs()

    def impactPop(self):
        sheet = self.readSheet('Programs impacted population', [0,1])
        impacted = {}
        for pop in ['Children', 'Pregnant women', 'Non-pregnant WRA', 'General population']:
            impacted.update(sheet.loc[pop].to_dict(orient='index'))
        self.programImpactedPop = impacted

    def progRisks(self):
        areas = self.readSheet('Program risk areas', [0])
        booleanFrame = areas.isnull()
        self.programAreas = {}
        for program, areas in booleanFrame.iterrows():
            for risk, value in areas.iteritems():
                if self.programAreas.get(risk) is None:
                    self.programAreas[risk] = []
                if not value:
                    self.programAreas[risk].append(program)

    def popRisks(self):
        areas = self.readSheet('Population risk areas', [0])
        booleanFrame = areas.isnull()
        self.populationAreas = {}
        for program, areas in booleanFrame.iterrows():
            for risk, value in areas.iteritems():
                if self.populationAreas.get(risk) is None:
                    self.populationAreas[risk] = []
                if not value:
                    self.populationAreas[risk].append(program)

    def birthOutcomes(self):
        BOprograms = self.readSheet('Programs birth outcomes', [0,1], 'index')
        newBOprograms = {}
        for program in BOprograms.keys():
            if not newBOprograms.get(program[0]):
                newBOprograms[program[0]] = {}
            newBOprograms[program[0]][program[1]] = BOprograms[program]
        self.BOprograms = newBOprograms

    def correctBF(self):
        self.correctBF = self.readSheet('Appropriate breastfeeding', [0], 'dict')['Practice']

    def anaemiaProgs(self):
        anaemiaSheet = self.readSheet('Programs anemia', [0,1])
        self.RRanaemiaProgram = anaemiaSheet.loc['Relative risks of anaemia when receiving intervention'].to_dict(orient='index')
        self.ORanaemiaProgram = anaemiaSheet.loc['Odds ratios of being anaemic when covered by intervention'].to_dict(orient='index')
        print self.RRanaemiaProgram

    def wastingProgs(self):
        self.ORwastingProgram = {}
        wastingSheet = self.readSheet('Programs wasting', [0,1])
        self.ORwastingProgram['SAM'] = wastingSheet.loc['Odds ratio of SAM when covered by program'].to_dict(orient='index')
        self.ORwastingProgram['MAM'] = wastingSheet.loc['Odds ratio of MAM when covered by program'].to_dict(orient='index')

    def childProgs(self):
        childSheet = self.readSheet('Programs for children', [0,1,2])
        childDict = childSheet.to_dict(orient='index')
        self.childPrograms = self.makeDict(childDict)

    def pwProgs(self):
        PWsheet= self.readSheet('Programs for PW', [0,1,2])
        PWdict = PWsheet.to_dict(orient='index')
        self.PWprograms = self.makeDict(PWdict)

    def birthOutcomeRisks(self):
        BOsheet = self.readSheet('Birth outcome risks', [0,1])
        self.ORconditionBirth = BOsheet.loc['OR for condition'].to_dict('index')
        self.RRdeath['Birth outcomes'] = BOsheet.loc['RR of death by cause'].to_dict('index')
        self.RRageOrder = BOsheet.loc['RR age order'].to_dict('index')
        self.RRinterval = BOsheet.loc['RR interval'].to_dict('index')



    def readSheet(self, name, cols, dictOrient=None):
        df = self.spreadsheet.parse(name, index_col=cols).dropna(how='all')
        if dictOrient:
            df = df.to_dict(dictOrient)
        return df

    def makeDict(self, mydict):
        '''myDict is a spreadsheet with 3 index cols, converted to dict using orient='index' '''
        resultDict = {}
        for key in mydict.keys():
            first = key[0]
            sec = key[1]
            third = key[2]
            if resultDict.get(first) is None:
                resultDict[first] = {}
                resultDict[first][sec] = {}
                resultDict[first][sec][third] = mydict[key]
            if resultDict[first].get(sec) is None:
                resultDict[first][sec] = {}
                resultDict[first][sec][third] = mydict[key]
            if resultDict[first][sec].get(third) is None:
                    resultDict[first][sec][third] = mydict[key]
        return resultDict




class InputData(object):
    def __init__(self, country, analysisType, region):
        filepath = os.path.join(os.pardir, 'applications', country, 'data', analysisType, region)
        self.spreadsheet = ExcelFile(filepath)


class UserSettings(object):
    """Stores all the settings for each project, defined by the user"""
    def __init__(self):
        filepath = 'dummy'
        self.spreadsheet = ExcelFile(filepath)
        pass


mine= DefaultParams('master')







