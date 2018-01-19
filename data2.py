import pandas as pd
from copy import deepcopy as dcp

class Project:
    def __init__(self, filepath, programsToKeep=None):
        self.filename = filepath
        self.workbook = pd.ExcelFile(filepath)
        self.sheetNames = self.workbook.sheet_names
        self.childAges = ["<1 month", "1-5 months", "6-11 months", "12-23 months", "24-59 months"]
        self.WRAages = ['WRA: 15-19 years', 'WRA: 20-29 years', 'WRA: 30-39 years', 'WRA: 40-49 years']
        self.PWages = ["PW: 15-19 years", "PW: 20-29 years", "PW: 30-39 years", "PW: 40-49 years"]
        self.birthOutcomes = ['Term AGA', 'Term SGA', 'Pre-term AGA', 'Pre-term SGA']
        self.getProgramsForAnalysis()
        self.readAllData()

    #####--- WRAPPER METHODS ---######

    def readAllData(self):
        self.readProgramData() # TODO: program dependencies for IYCF not set properly b/c they are set-up later. Order may matter, need to check. Hacky fix is to add them to program dependcies sheet.
        self.readDemographicsData()
        self.readMortalityData()
        self.getAllIYCFpackages()
        self.padRequiredFields()
        self.combineRelatedData()

    def readProgramData(self):
        self.getStuntingProgram()
        self.getBirthOutcomes()
        self.getAnaemiaProgram()
        self.getWastingProgram()
        self.getChildProgram()
        self.getFamilyPrograms()
        self.getBirthAgePrograms()
        self.getCostCoverageInfo()
        self.getProgramTargetPop()
        self.getProgramRiskAreas()
        self.getProgramDependencies()

    def readDemographicsData(self):
        self.getDemographics()
        self.getAgeDist()
        self.getRiskDist()
        self.getAnaemiaDist()
        self.getBirthDist()
        self.getProjections()
        self.getAppropriateBF()
        self.getPopulationRiskAreas()

    def readMortalityData(self):
        self.getDeathDist()
        self.getRelativeRisks()
        self.getBOrisks()
        self.getIncidences()
        self.getConditions()
        self.getORforCondition()
        self.getMortalityRates()

    def padRequiredFields(self):
        self.padRelativeRisks()
        self.padStuntingORprograms()
        self.padWastingORprograms()
        self.padBForPrograms()
        self.padAnaemiaORprograms()
        self.padChildPrograms()

    def combineRelatedData(self):
        self.combineORprogram()


    #####--- WORKER METHODS ---######

    ## DEMOGRAPHICS ##
    def getDemographics(self):
        baseline = self.readSheet('Baseline year demographics', [0,1])
        demographics = {}
        for field in ['Current year', 'Food']:
            demographics.update(baseline.loc[field].to_dict('index'))
        self.demographics = {key: item['Values'] for key, item in demographics.iteritems()}
        self.year = self.demographics['year']

    def getAgeDist(self):
        baseline = self.readSheet('Baseline year demographics', [0,1])
        agePop = {}
        for field in ['Non-pregnant women population', 'PW population']:
            agePop.update(baseline.loc[field].to_dict('index'))
        self.populationByAge = {key: item['Values'] for key, item in agePop.iteritems()}
        ageDist = {}
        for field in ['Age distribution pregnant']:
            ageDist.update(baseline.loc[field].to_dict('index'))
        self.PWageDistribution = {key: item['Values'] for key, item in ageDist.iteritems()}

    def getRiskDist(self):
        dist = self.readSheet('Distributions', [0,1])
        riskDist = {}
        self.riskCategories = {}
        for field in ['Stunting', 'Wasting', 'Breastfeeding']:
            riskDist[field] = dist.loc[field].to_dict('dict')
            self.riskCategories[field] = list(dist.loc[field].index)
        self.riskCategories['Birth outcomes'] = self.birthOutcomes
        self.riskDistributions = riskDist

    def getAnaemiaDist(self):
        field = 'Anaemia'
        dist = self.readSheet('Prevalence of anaemia', [0,1])
        anaemiaDist = dist.loc[field].to_dict('dict')
        self.riskCategories[field] = list(dist.loc[field].index)
        self.riskDistributions[field] = anaemiaDist

    def getBirthDist(self):
        birthsSheet = self.readSheet('Distribution births', [0, 1])
        self.birthAgeDist = birthsSheet.loc['Birth age order'].to_dict('dict')['Fraction']
        self.birthIntervalDist = birthsSheet.loc['Birth intervals'].to_dict('dict')['Fraction']

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
        self.RRageOrder = BOsheet.loc['RR age order'].to_dict('index')
        self.RRinterval = BOsheet.loc['RR interval'].to_dict('index')

    def getIncidences(self):
        self.incidences = self.readSheet('Incidence of conditions', [0], 'dict')

    def getConditions(self):
        self.conditions = self.readSheet('Incidence of conditions', [0], 'index').keys()

    def getORforCondition(self):
        ORsheet = self.readSheet('Odds ratios', [0,1])
        ORs = ORsheet.loc['OR stunting progression'].to_dict(orient='index')
        del ORs['Stunting progression']['<1 month']
        for field in ['OR stunting by condition', 'OR SAM by condition', 'OR MAM by condition', 'OR anaemia by condition']:
            ORs[field] = {}
            ORs[field].update(ORsheet.loc[field].to_dict(orient='index'))
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
        # treat BO differently
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
        self.ORstuntingProgram = ORsheet.loc['OR stunting by program'].to_dict(orient='index')

    def getProgramTargetPop(self):
        targetPopSheet = self.readSheet('Programs target population', [0,1])
        targetPop = {}
        for pop in ['Children', 'Pregnant women', 'Non-pregnant WRA', 'General population']:
            targetPop.update(targetPopSheet.loc[pop].to_dict(orient='index'))
        self.programTargetPop = targetPop

    def getProgramRiskAreas(self):
        areas = self.readSheet('Program risk areas', [0])
        booleanFrame = areas.isnull()
        self.programAreas = {}
        for program, areas in booleanFrame.iterrows():
            for risk, value in areas.iteritems():
                if self.programAreas.get(risk) is None:
                    self.programAreas[risk] = []
                if not value:
                    self.programAreas[risk].append(program)

    def getCostCoverageInfo(self):
        self.costCurveInfo = self.readSheet('Programs cost and coverage', [0], 'dict')
        #self.baselineCov = {program: info['Baseline coverage'] for program, info in self.costCurveInfo.iteritems()}

    def getProgramDependencies(self): # TODO: will need to put IYCF dependencies in (maybe have them in the spreadsheet, but will be ignored if not selected by user)
        dependencies = self.readSheet('Program dependencies', [0])
        programDep = {}
        for program, dependency in dependencies.iterrows():
            programDep[program] = {}
            for dependType, value in dependency.iteritems():
                if isinstance(value, unicode): # cell not empty
                    programDep[program][dependType] = value.replace(", ", ",").split(',') # assumes programs separated by ", "
                else:
                    programDep[program][dependType] = []
        # pad the remaining programs
        missingProgs = list(set(self.programList) - set(programDep.keys()))
        for program in missingProgs:
            programDep[program] = {}
            for field in dependencies.columns:
                programDep[program][field] = []
        self.programDependency = programDep

    def getProgramsForAnalysis(self):
        includeSheet = self.readSheet('Programs to include', [0])
        includeSheet = includeSheet[pd.notnull(includeSheet)]
        self.programList = []
        for program, value in includeSheet.iterrows():
            self.programList.append(program)

    def getFamilyPrograms(self):
        self.famPlanMethods = self.readSheet('Programs family planning', [0], 'index')

    def getChildProgram(self):
        childSheet = self.readSheet('Programs for children', [0,1,2])
        childDict = childSheet.to_dict(orient='index')
        self.childPrograms = self.makeDict(childDict)

    def getBirthAgePrograms(self):
        programSheet = self.readSheet('Programs birth age', [0,1])
        self.birthAgeProgram = programSheet.loc['Birth age program'].to_dict('dict')
        self.birthAges = self.birthAgeProgram.keys()

    def getAnaemiaProgram(self):
        anaemiaSheet = self.readSheet('Programs anemia', [0,1])
        self.RRanaemiaProgram = anaemiaSheet.loc['Relative risks'].to_dict(orient='index')
        self.ORanaemiaProgram = anaemiaSheet.loc['Odds ratios'].to_dict(orient='index')

    def getWastingProgram(self):
        self.ORwastingProgram = {}
        wastingSheet = self.readSheet('Programs wasting', [0,1])
        self.ORwastingProgram['SAM'] = wastingSheet.loc['OR SAM by program'].to_dict(orient='index')
        self.ORwastingProgram['MAM'] = wastingSheet.loc['OR MAM by program'].to_dict(orient='index')

    def combineORprogram(self):
        self.ORprograms = {}
        self.RRprograms = {} # to accommodate anaemia data
        self.ORprograms['Stunting'] = self.ORstuntingProgram
        self.ORprograms['Wasting'] = self.ORwastingProgram
        self.ORprograms['Anaemia'] = self.ORanaemiaProgram
        self.ORprograms['Breastfeeding'] = self.ORappropriateBFprogram
        self.RRprograms['Anaemia'] = self.RRanaemiaProgram
        self.RRprograms['Stunting'] = {}
        self.RRprograms['Wasting'] = {}
        self.RRprograms['Breastfeeding'] = {}

    def getBirthOutcomes(self):
        BOprograms = self.readSheet('Programs birth outcomes', [0,1], 'index')
        newBOprograms = {}
        for program in BOprograms.keys():
            if not newBOprograms.get(program[0]):
                newBOprograms[program[0]] = {}
            newBOprograms[program[0]][program[1]] = BOprograms[program]
        self.BOprograms = newBOprograms

    def getAppropriateBF(self):
        self.correctBF = self.readSheet('Appropriate breastfeeding', [0], 'dict')['Practice']

    def getPopulationRiskAreas(self):
        areas = self.readSheet('Population risk areas', [0])
        booleanFrame = areas.isnull()
        self.populationAreas = {}
        for program, areas in booleanFrame.iterrows():
            for risk, value in areas.iteritems():
                if self.populationAreas.get(risk) is None:
                    self.populationAreas[risk] = []
                if not value:
                    self.populationAreas[risk].append(program)

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

    def padStuntingORprograms(self):
        '''Pads missing values with 1s'''
        ORs = dcp(self.ORstuntingProgram)
        for program in self.programList:
            if program not in ORs:
                ORs[program] = {}
                for age in self.childAges:
                    ORs[program][age] = 1.
        self.ORstuntingProgram = ORs

    def padWastingORprograms(self):
        '''Pads missing values with 1s'''
        ORs = dcp(self.ORwastingProgram)
        for wastingCat in ['SAM', 'MAM']:
            for program in self.programList:
                if program not in ORs[wastingCat]:
                    ORs[wastingCat][program] = {}
                    for age in self.childAges:
                        ORs[wastingCat][program][age] = 1.
        self.ORwastingProgram = ORs

    def padBForPrograms(self):
        ORs = dcp(self.ORappropriateBFprogram)
        missingProgs = set(self.programList) - set(ORs.keys())
        padded = {program:{age:1. for age in self.childAges} for program in missingProgs}
        ORs.update(padded)
        self.ORappropriateBFprogram = ORs

    def padAnaemiaORprograms(self):
        ORs = dcp(self.ORanaemiaProgram)
        missingProgs = set(self.programList) - set(ORs.keys()) - set(self.RRanaemiaProgram.keys())
        padded = {program:{age:1. for age in self.childAges + self.PWages + self.WRAages} for program in missingProgs}
        ORs.update(padded)
        self.ORanaemiaProgram = ORs

    def padChildPrograms(self):
        '''Need all causes to have a value for the present programs'''
        fields = ['Affected fraction', 'Effectiveness mortality', 'Effectiveness incidence']
        programsPresent = self.childPrograms.keys()
        effectiveness = {}
        for program in programsPresent:
            for cause in self.causesOfDeath + ['MAM', 'SAM']:
                if self.childPrograms[program].get(cause) is None:
                    self.childPrograms[program][cause] = {}
                for field in fields:
                    if self.childPrograms[program][cause].get(field) is None:
                        self.childPrograms[program][cause][field] = {}
                    for age in self.childAges:
                        if self.childPrograms[program][cause][field].get(age) is None:
                            self.childPrograms[program][cause][field][age] = 0
        for age in self.childAges:
            effectiveness[age] = {}
            for program in programsPresent:
                effectiveness[age][program] = {}
                for cause in self.causesOfDeath + ['MAM', 'SAM']:
                    effectiveness[age][program][cause] = {}
                    for field in fields:
                        effectiveness[age][program][cause][field] = self.childPrograms[program][cause][field][age]
        self.childPrograms = effectiveness


    def _getMissingElements(self, listA, listB):
        missingElements = set(listA) - set(listB)
        return missingElements




    ### IYCF ###

    def getAllIYCFpackages(self):
        effects = self.readSheet('IYCF package odds ratios', [0,1,2])
        BFeffects = effects.loc['OR for correct breastfeeding']
        stuntingEffects = effects.loc['OR for stunting']
        packagesDict = self.defineIYCFpackages()
        costCurveInfo = self.getIYCFcostCoverageSaturation(packagesDict)
        self.programTargetPop.update(self.getIYCFtargetPop(packagesDict))
        self.ORappropriateBFprogram = self.createIYCFpackages(BFeffects, packagesDict)
        self.ORstuntingProgram.update(self.createIYCFpackages(stuntingEffects, packagesDict))
        for field in ['unit cost', 'saturation coverage', 'baseline coverage']:
            self.costCurveInfo[field].update(costCurveInfo[field])

    def createIYCFpackages(self, effects, packagesDict):
        '''Creates IYCF packages based on user input in 'IYCFpackages' '''
        # non-empty cells denote program combination
        # get package combinations
        # create new program
        newPrograms = {}
        ORs = {}
        for key, item in packagesDict.items():
            if newPrograms.get(key) is None:
                newPrograms[key] = {}
            for age in self.childAges:
                ORs[age] = 1.
                for pop, mode in item:
                    row = effects.loc[pop, mode]
                    thisOR = row[age]
                    ORs[age] *= thisOR
            newPrograms[key].update(ORs)
        return newPrograms

    def defineIYCFpackages(self):
        IYCFpackages = self.readSheet('IYCF packages', [0,1])
        packagesDict = {}
        for packageName, package in IYCFpackages.groupby(level=[0, 1]):
            if packageName[0] not in packagesDict:
                packagesDict[packageName[0]] = []
            for mode in package:
                col = package[mode]
                if col.notnull()[0]:
                    if mode == 'Mass media':
                        ageModeTuple = [(pop, mode) for pop in self.childAges[:-1]] # exclude 24-59 months
                    else:
                        ageModeTuple = [(packageName[1], mode)]
                    packagesDict[packageName[0]] += ageModeTuple
        return packagesDict

    def getIYCFcostCoverageSaturation(self, IYCFpackages):
        IYCFcost = self.readSheet('IYCF cost & coverage', [0,1]).loc['Unit costs']
        infoList = ['unit cost', 'saturation coverage', 'baseline coverage']
        packageCostSaturation = {}
        for field in infoList:
            packageCostSaturation[field] = {}
        for name, package in IYCFpackages.iteritems():
            cost = 0
            for pop, mode in package:
                cost += IYCFcost[mode][pop]
            packageCostSaturation['unit cost'][name] = cost
            # TEMP VALUES
            packageCostSaturation['saturation coverage'][name] = 0.95
            packageCostSaturation['baseline coverage'][name] = 0.
        return packageCostSaturation

    def getIYCFtargetPop(self, packageModalities):
        IYCFtargetPop = self.readSheet('IYCF cost & coverage', [0, 1]).loc['Target populations']
        newTargetPops = {}
        for name, package in packageModalities.iteritems():
            newTargetPops[name] = {}
            for pop, mode in package:
                if pop not in newTargetPops[name]:
                    newTargetPops[name][pop] = {}
                newTargetPops[name][pop][mode] = IYCFtargetPop[mode][pop]
        # convert 'pregnant women' to its age bands
        newTargetPops = self.createAgeBands(newTargetPops, packageModalities.keys(), self.PWages, 'Pregnant women')
        # target pop is sum of fractions exposed to modality for each age band
        fracTargeted = {}
        for program, popModes in newTargetPops.iteritems():
            fracTargeted[program] = {}
            for pop, modes in popModes.iteritems():
                fracTargeted[program][pop] = sum(frac for frac in modes.values())
        allAges = self.childAges + self.PWages + self.WRAages
        for program, pop in fracTargeted.iteritems():
            missingAges = self._getMissingElements(allAges, pop.keys())
            for age in missingAges:
                fracTargeted[program][age] = 0.
        return fracTargeted

    def createAgeBands(self, dictToUpdate, keyList, listOfAges, pop):
        for key in keyList:  # could be program, ages
            subDict = dictToUpdate[key].pop(pop, None)
            newAgeGroups = {age:subDict for age in listOfAges if subDict is not None}
            dictToUpdate[key].update(newAgeGroups)
        return dictToUpdate

def setUpProject(filePath):
    project = Project(filePath)
    return project