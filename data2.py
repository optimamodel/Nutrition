import pandas as pd

class Project:
    def __init__(self, filepath, programsToKeep=None):
        self.filename = filepath
        self.workbook = pd.ExcelFile(filepath)
        self.sheetNames = self.workbook.sheet_names
        self.childAges = ["<1 month", "1-5 months", "6-11 months", "12-23 months", "24-59 months"]
        self.WRAages = ['WRA: 15-19 years', 'WRA: 20-29 years', 'WRA: 30-39 years', 'WRA: 40-49 years']
        self.PWages = ["PW: 15-19 years", "PW: 20-29 years", "PW: 30-39 years", "PW: 40-49 years"]
        self.BO = ['Term AGA', 'Term SGA', 'Pre-term AGA', 'Pre-term SGA']
        self.programList = list(self.readSheet('Interventions cost and coverage', [0]).index) if not programsToKeep else programsToKeep
        self.readAllData()

    #####--- WRAPPER METHODS ---######

    def readAllData(self):
        self.readProgramData()
        self.readDemographicsData()
        self.readMortalityData()
        self.getAllIYCFpackages()

    def readProgramData(self):
        self.getStuntingProgram()
        self.getBirthOutcomes()
        self.getAnaemiaProgram()
        self.getwastingProgram()
        self.getChildProgram()
        self.getFamilyPrograms()
        self.getCostCoverageInfo()
        self.getProgramTargetPop()

    def readDemographicsData(self):
        self.getDemographics()
        self.getAgeDist()
        self.getRiskDist()
        self.getAnaemiaDist()
        self.getProjections()

    def readMortalityData(self):
        self.getDeathDist()
        self.getRelativeRisks()
        self.getBOrisks()
        self.getIncidences()
        self.getORforCondition()
        self.getMortalityRates()
        self.padRelativeRisks()


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
        for field in ['Non-pregnant women population', 'PW population']:
            ageDist.update(baseline.loc[field].to_dict('index'))
        self.ageDistributions = {key: item['Values'] for key, item in ageDist.iteritems()}

    def getRiskDist(self):
        dist = self.readSheet('Distributions', [0,1])
        riskDist = {}
        self.riskCategories = {}
        for field in ['Stunting', 'Wasting', 'Breastfeeding']:
            riskDist[field] = dist.loc[field].to_dict('index')
            self.riskCategories[field] = list(dist.loc[field].index)
        self.riskCategories['Birth outcomes'] = self.BO
        self.riskDistributions = riskDist

    def getAnaemiaDist(self):
        field = 'Anaemia'
        dist = self.readSheet('Prevalence of anaemia', [0,1])
        anaemiaDist = dist.loc[field].to_dict('index')
        self.riskCategories[field] = list(dist.loc[field].index)
        self.riskDistributions[field] = anaemiaDist

    def getProjections(self):
        self.projections = self.readSheet('Demographic projections', [0], 'dict')

    ### MORTALITY ###

    def getDeathDist(self):
        self.deathDist = self.readSheet('Causes of death', [0], 'index')
        self.causesOfDeath = self.deathDist.keys()

    def getRelativeRisks(self):
        RRsheet = self.readSheet('Relative risks', [0,1,2], 'index')
        self.RRdeath = self.makeDict(RRsheet)

    def getBOrisks(self):
        BOsheet = self.readSheet('Birth outcomes & risks', [0,1])
        self.birthDist = BOsheet.loc['Distribution'].to_dict('index')['Fraction of births']
        self.ORconditionBirth = BOsheet.loc['OR for condition'].to_dict('index')
        self.RRdeath['Birth outcomes'] = BOsheet.loc['RR of death by cause'].to_dict('index')

    def getIncidences(self):
        self.incidences = self.readSheet('Incidence of conditions', [0], 'index')

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

    def padRelativeRisks(self):
        # pad with 1's for causes not included
        for risk in ['Stunting', 'Wasting', 'Anaemia', 'Breastfeeding']:
            if risk == 'Anaemia': # only risk across all pops
                ages = self.childAges + self.WRAages + self.PWages
            else:
                ages = self.childAges
            RRs = self.RRdeath[risk]
            for cause in self.causesOfDeath:
                if RRs.get(cause) is None:
                    RRs[cause] = {}
                    for status in self.riskCategories[risk]:
                        RRs[cause][status] = {}
                        for age in ages:
                            RRs[cause][status][age] = 1.
                self.RRdeath[risk].update(RRs)
        RRs = self.RRdeath['Birth outcomes']
        for cause in self.causesOfDeath:
            if RRs.get(cause) is None:
                RRs[cause] = {}
                for status in self.riskCategories['Birth outcomes']:
                    RRs[cause][status] = 1.
            self.RRdeath['Birth outcomes'].update(RRs)

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
        self.ORstuntingProgram.update(self.createIYCFpackages(stuntingEffects, packagesDict))
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


