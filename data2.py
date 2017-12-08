import pandas as pd

class Project:
    def __init__(self, filepath, programsToKeep=None):
        self.filename = filepath
        self.workbook = pd.ExcelFile(filepath)
        self.sheetNames = self.workbook.sheet_names
        self.childAges = ["<1 month", "1-5 months", "6-11 months", "12-23 months", "24-59 months"]
        self.WRAages = ['WRA: 15-19 years', 'WRA: 20-29 years', 'WRA: 30-39 years', 'WRA: 40-49 years']
        self.PWages = ["PW: 15-19 years", "PW: 20-29 years", "PW: 30-39 years", "PW: 40-49 years"]
        self.programList = list(self.workbook.parse('Interventions cost and coverage', index_col=[0]).index) if not programsToKeep else programsToKeep
        self.readAllData()

    def readAllData(self):
        self.readProgramData()
        self.readMortalityData()
        self.readMortalityData()
        self.getAllIYCFpackages()

    #####--- WRAPPER METHODS ---######

    def readProgramData(self): # TODO: should get all this data to have the outer-most key as programs, so can create objects and pass it this data. Wasting may cause an issue given it has two 'types'
        self.getStuntingProgram()
        self.getBirthOutcomes()
        self.getAnaemiaProgram()
        self.getwastingProgram()
        self.getChildProgram()
        self.getFamilyPrograms()
        self.getCostCoverageInfo()
        self.getProgramTargetPop()

    def readMortalityData(self):
        self.getRelativeRisks()
        self.getBOrisks()
        self.getDeathDist()
        self.getIncidences()
        self.getAnaemiaDist()
        self.getORforCondition()
        self.getMortalityRates()

    def readDemographicsData(self):
        self.getDemographics()
        self.getAgeDist()
        self.getRiskDist()
        self.getProjections()

    #####--- WORKER METHODS ---######

    ## DEMOGRAPHICS ##
    def getDemographics(self):
        baseline = self.readSheet('Baseline year demographics', [0,1])
        demographics = {}
        for field in ['Current year', 'Food']:
            demographics.update(baseline.loc[field].to_dict('index'))
        self.demographics = {key: item['Values'] for key, item in demographics.iteritems()}

    def getAgeDist(self):
        baseline = self.readSheet('Baseline year demographics', [0,1])
        ageDist = {}
        for field in ['Women of reproductive age', 'Age distribution pregnant']:
            ageDist.update(baseline.loc[field].to_dict('index'))
        self.ageDistributions = {key: item['Values'] for key, item in ageDist.iteritems()}

    def getRiskDist(self):
        dist = self.readSheet('Distributions', [0,1], 'index')
        riskDist = {}
        for field in ['Women of reproductive age', 'Age distribution pregnant']:
            riskDist.update(dist.loc[field].to_dict('index'))
        self.riskDistributions = {key: item['Values'] for key, item in riskDist.iteritems()}

    def getProjections(self):
        self.projections = self.readSheet('Demographic projections', [0], 'dict')

    ### MORTALITY ###
    def getRelativeRisks(self):
        RRsheet = self.readSheet('Relative risks', [0,1,2], 'index')
        self.RRdeath = self.makeDict(RRsheet)

    def getBOrisks(self):
        BOsheet = self.readSheet('Birth outcomes & risks', [0,1])
        self.birthDist = BOsheet.loc['Distribution'].to_dict('index')
        self.ORconditionBirth = BOsheet.loc['OR for condition'].to_dict('index')
        self.RRdeathBirth = BOsheet.loc['RR of death by cause'].to_dict('index')

    def getDeathDist(self):
        self.deathDist = self.readSheet('Causes of death', [0], 'index')

    def getIncidences(self):
        self.incidences = self.readSheet('Incidence of conditions', [0], 'index')

    def getAnaemiaDist(self): # TODO: need to check which kind of anaemia we want to model, severe or all
        self.anemiaDist = self.readSheet('Prevalence of anemia', [0], 'index')

    def getORforCondition(self):
        ORsheet = self.readSheet('Odds ratios', [0,1])
        ORs = ORsheet.loc['OR stunting progression'].to_dict(orient='index')
        del ORs['Stunting progression']['<1 month']
        for field in ['OR stunting condition', 'OR SAM by condition', 'OR MAM by condition']:
            ORs.update(ORsheet.loc[field].to_dict(orient='index'))
        self.ORcondition = ORs

    def getMortalityRates(self):
        baseline = self.readSheet('Baseline year demographics', [0,1])
        mortalityRates = baseline.loc['Mortality rates'].to_dict(orient='index')
        self.mortalityRates = {key: item['Values'] for key, item in mortalityRates.iteritems()}

    ####--- PROGRAMS ---####
    def getStuntingProgram(self):
        ORsheet = self.readSheet('Odds ratios', [0,1])
        self.ORstuntingProgram = ORsheet.loc['OR stunting by intervention'].to_dict(orient='index') # TODO: careful - this needs to include IYCF

    def getProgramTargetPop(self):
        targetPopSheet = self.readSheet('Interventions target population', [0,1])
        targetPop = {}
        for pop in ['Children', 'Pregnant women', 'Non-pregnant WRA']:
            targetPop.update(targetPopSheet.loc[pop].to_dict(orient='index'))
        self.programTargetPop = targetPop

    def getCostCoverageInfo(self):
        self.costCurveInfo = self.readSheet('Interventions cost and coverage', [0], 'index')

    def getFamilyPrograms(self):
        self.familyPlanningMethods = self.readSheet('Interventions family planning', [0])

    def getChildProgram(self):
        childSheet = self.readSheet('Interventions for children', [0,1,2])
        childDict = childSheet.to_dict(orient='index')
        self.childPrograms = self.makeDict(childDict)

    def getAnaemiaProgram(self):
        anaemiaSheet = self.readSheet('Interventions anemia', [0,1])
        self.RRanaemia = anaemiaSheet.loc['Relative risks'].to_dict(orient='index')
        self.ORanaemia = anaemiaSheet.loc['Odds ratios'].to_dict(orient='index')

    def getwastingProgram(self):
        self.ORwastingProgram = {}
        wastingSheet = self.readSheet('Interventions wasting', [0,1])
        self.ORwastingProgram['SAM'] = wastingSheet.loc['OR SAM by intervention'].to_dict(orient='index')
        self.ORwastingProgram['MAM'] = wastingSheet.loc['OR MAM by intervention'].to_dict(orient='index')

    def getBirthOutcomes(self):
        BOprograms = self.readSheet('Interventions birth outcomes', [0,1], 'index')
        newBOprograms = {}
        for program in BOprograms.keys():
            newBOprograms[program[0]] = {}
            newBOprograms[program[0]][program[1]] = BOprograms[program]
        self.BOprograms = newBOprograms

    def getAppropriateBF(self):
        self.appropriateBF = self.readSheet('Appropriate breastfeeding', [0], 'dict')['Practice']

    def makeDict(self, mydict):
        '''myDict is a spreadsheet with 3 index cols, converted to dict using orient='index' '''
        resultDict = {}
        for key in mydict.keys():
            resultDict.update({key[0]:{key[1]:{key[2]:mydict[key]}}})
        return resultDict

    def readSheet(self, name, cols, dictOrient=None):
        df = self.workbook.parse(name, index_col=cols).dropna(how='all')
        if dictOrient:
            df = df.to_dict(dictOrient)
        return df

    ### IYCF ###

    def getAllIYCFpackages(self):
        effects = self.readSheet('IYCF package odds ratios', [0,1,2])
        BFeffects = effects.loc['OR for correct breastfeeding']
        stuntingEffects = effects.loc['OR for stunting']
        IYCFpackages = self.readSheet('IYCF packages', [0,1])
        packagesDict = self.defineIYCFpackages(IYCFpackages)
        self.ORappropriateBFprogram = self.createIYCFpackages(BFeffects, packagesDict)
        self.ORstuntingProgram = self.createIYCFpackages(stuntingEffects, packagesDict)
        self.programList += packagesDict.keys()

    def createIYCFpackages(self, effects, packagesDict):
        '''Creates IYCF packages based on user input in 'IYCFpackages' '''
        # non-empty cells denote program combination
        # get package combinations
        # create new intervention
        newInterventions = {}
        ORs = {}
        for key, item in packagesDict.items():
            if newInterventions.get(key) is None:
                newInterventions[key] = {}
            for age in self.childAges:
                ORs[age] = 1.
                for pop, mode in item:
                    row = effects.loc[pop, mode]
                    thisOR = row[age]
                    ORs[age] *= thisOR
            newInterventions[key].update(ORs)
        return newInterventions

    def defineIYCFpackages(self, IYCFpackages):
        packagesDict = {}
        for packageName, package in IYCFpackages.groupby(level=[0, 1]):
            if packagesDict.get(packageName[0]) is None:
                packagesDict[packageName[0]] = []
            for mode in package:
                col = package[mode]
                if col.notnull()[0]:
                    if mode == 'Mass media':
                        ageModeTuple = [(pop, mode) for pop in self.childAges]
                    else:
                        ageModeTuple = [(packageName[1], mode)]
                    packagesDict[packageName[0]] += ageModeTuple
        return packagesDict


