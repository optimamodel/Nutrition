# -*- coding: utf-8 -*-
"""
Created on Fri Feb 26 15:57:07 2016

@author: ruth
"""
import pandas as pd

class Data:
    def __init__(self, causesOfDeath, conditions, interventionList, interventionCompleteList,
                 demographics, projectedBirths, rawMortality, causeOfDeathDist, RRdeathAnemia,
                 RRdeathStunting, RRdeathWasting, RRdeathBreastfeeding, 
                 RRdeathByBirthOutcome, stuntingDistribution, wastingDistribution,
                 breastfeedingDistribution, incidences, RRdiarrhea, ORstuntingCondition,
                 birthOutcomeDist, ORstuntingProgression, ORstuntingBirthOutcome,
                 ORstuntingIntervention, RRanemiaIntervention, ORanemiaIntervention,
                 ORappropriatebfIntervention,
                 ageAppropriateBreastfeeding, coverage, costSaturation,
                 targetPopulation, affectedFraction, effectivenessMortality,
                 effectivenessIncidence, interventionsBirthOutcome, anemiaDistribution,
                 projectedWRApop, projectedWRApopByAge, projectedPWpop,
                 projectedGeneralPop, PWageDistribution, fracExposedMalaria,
                 ORanemiaCondition, fracSevereDia, ORwastingCondition,
                 ORwastingIntervention, ORwastingBirthOutcome, fracSAMtoMAM, fracMAMtoSAM,
                 effectivenessFP, distributionFP, IYCFtargetPop, IYCFprograms, ageOrderDist, 
                 intervalDist, RRageOrder, RRinterval, interventionsBirthAge):


        self.causesOfDeath = causesOfDeath
        self.conditions = conditions
        self.interventionList = interventionList
        self.interventionCompleteList = interventionCompleteList
        self.demographics = demographics
        self.projectedBirths = projectedBirths
        self.rawMortality = rawMortality
        self.causeOfDeathDist = causeOfDeathDist
        self.stuntingDistribution = stuntingDistribution
        self.wastingDistribution = wastingDistribution
        self.breastfeedingDistribution = breastfeedingDistribution
        self.RRdeathAnemia = RRdeathAnemia
        self.RRdeathStunting = RRdeathStunting
        self.RRdeathWasting = RRdeathWasting
        self.RRdeathBreastfeeding = RRdeathBreastfeeding
        self.RRdeathByBirthOutcome = RRdeathByBirthOutcome
        self.ORstuntingProgression = ORstuntingProgression
        self.incidences = incidences
        self.RRdiarrhea = RRdiarrhea
        self.ORstuntingCondition = ORstuntingCondition
        self.ORstuntingBirthOutcome = ORstuntingBirthOutcome
        self.ORwastingBirthOutcome = ORwastingBirthOutcome
        self.birthOutcomeDist = birthOutcomeDist
        self.ORstuntingIntervention = ORstuntingIntervention
        self.RRanemiaIntervention = RRanemiaIntervention
        self.ORanemiaIntervention = ORanemiaIntervention
        self.ORwastingIntervention = ORwastingIntervention
        self.ORappropriatebfIntervention = ORappropriatebfIntervention
        self.ageAppropriateBreastfeeding = ageAppropriateBreastfeeding
        self.coverage = coverage
        self.costSaturation = costSaturation
        self.targetPopulation = targetPopulation
        self.affectedFraction = affectedFraction
        self.effectivenessMortality = effectivenessMortality
        self.effectivenessIncidence = effectivenessIncidence
        self.interventionsBirthOutcome = interventionsBirthOutcome
        self.anemiaDistribution = anemiaDistribution
        self.projectedWRApop = projectedWRApop
        self.projectedWRApopByAge = projectedWRApopByAge
        self.projectedPWpop = projectedPWpop
        self.projectedGeneralPop = projectedGeneralPop
        self.PWageDistribution = PWageDistribution
        self.fracExposedMalaria = fracExposedMalaria
        self.ORanemiaCondition = ORanemiaCondition
        self.ORwastingCondition = ORwastingCondition
        self.fracSevereDia = fracSevereDia
        self.fracSAMtoMAM= fracSAMtoMAM
        self.fracMAMtoSAM = fracMAMtoSAM
        self.effectivenessFP = effectivenessFP
        self.distributionFP = distributionFP
        self.IYCFtargetPop = IYCFtargetPop
        self.IYCFprograms = IYCFprograms
        self.ageOrderDist = ageOrderDist
        self.intervalDist = intervalDist
        self.RRageOrder = RRageOrder
        self.RRinterval = RRinterval
        self.interventionsBirthAge = interventionsBirthAge


def readSheetWithOneIndexCol(sheet, scaleFactor=1.):
    resultDict = {}
    for columnName in sheet:
        resultDict[columnName] = dict(sheet[columnName] / scaleFactor)
    return resultDict

def readSheetWithTwoIndexCols(location, sheetname, indexList):
    # always ignore the first col when creating dictionary
    sheet = pd.read_excel(location, sheetname=sheetname, index_col=indexList)
    sheet = sheet.dropna()
    firstColList = sheet.index.levels[0]
    secondColList = sheet.index.levels[1]
    resultDict = {}
    for outerLevel in firstColList:
        for innerLevel in secondColList:
            for columnName in sheet:
                try:
                    resultDict[innerLevel] = sheet.loc[outerLevel][columnName][innerLevel]
                except KeyError: # do nothing if this combination doesn't exist
                    pass
    return resultDict

def splitSpreadsheetWithTwoIndexCols(sheet, keyForSplitting, rowList=None, scaleFactor=1., defaultValue=1., switchKeys=False):
    """rowList: a list of rows to iterate over, usually interventions or causes of death.
    If switchKeys==True, then first index col will be the outer key, else remaining cols are outer keys.
    scaleFactor: common factor to scale all values by.
    """
    subsheet = sheet.loc[keyForSplitting]
    resultDict = {}
    if rowList is None: # use rows only in subsheet
        rowList = subsheet.index
    if switchKeys:
        for row in rowList:
            resultDict[row] = {}
            for colName in subsheet:
                column = subsheet[colName]
                try:
                    resultDict[row][colName] = column[row] / scaleFactor
                except KeyError:
                    resultDict[row][colName] = defaultValue
    else: # don't switch
        for colName in subsheet:
            resultDict[colName] = {}
            column = subsheet[colName]
            for row in rowList:
                try:
                    resultDict[colName][row] = column[row] / scaleFactor
                except KeyError:
                    resultDict[colName][row] = defaultValue
    return resultDict

def readRelativeRisks(sheet, risk, statusList, causesOfDeath):
    resultDict = {}
    subsheet = sheet.loc[risk]
    for columnName in subsheet:
        column = subsheet[columnName]
        resultDict[columnName] = {}
        for cause in causesOfDeath:
            resultDict[columnName][cause] = {}
            for status in statusList:
                try:
                    resultDict[columnName][cause][status] = column[cause][status]
                except KeyError: # RR set to 1 if cause not in spreadsheet
                    resultDict[columnName][cause][status] = 1
    return resultDict

def readInterventionsByPopulationTabs(sheet, outcome, interventionList, pops, causesOfDeath):
    outcomeDict = {}
    for intervention in interventionList:
        outcomeDict[intervention] = {}
        for pop in pops:
            outcomeDict[intervention][pop] = {}
            for cause in causesOfDeath:
                try:
                    outcomeDict[intervention][pop][cause] = sheet[pop][intervention][cause][outcome]
                except KeyError:
                    outcomeDict[intervention][pop][cause] = 0.
    return outcomeDict

def mapAgeKeys(firstDict, secondDict):
    """Solves the problem of the data workbook not having the correct age band keys"""
    resultDict = {}
    for pop in secondDict.keys():
        dataDict = firstDict[pop]
        mappingList = secondDict[pop]
        for age in dataDict.keys():
            resultDict.update({key: dataDict[age] for key in mappingList if age in key})
    return resultDict

def stratifyPopIntoAgeGroups(dictToUpdate, keyList, listOfAgeGroups, population, keyLevel=0):
    """Solves the problem of data having only 'maternal' or 'WRA' for all age bands.
    Copies single value and creates age groups."""
    for key in keyList: # could be intervention, ages
        if keyLevel == 0:
            subDict = dictToUpdate.pop(population, None)
            newAgeGroups = {age: subDict for age in listOfAgeGroups}
            dictToUpdate.update(newAgeGroups)
        elif keyLevel == 1:
            subDict = dictToUpdate[key].pop(population, None)
            newAgeGroups = {age:subDict for age in listOfAgeGroups if subDict is not None}
            dictToUpdate[key].update(newAgeGroups)
    return dictToUpdate

def readSheet(location, sheetName, indexCols, dropna=True):
    mysheet = pd.read_excel(location, sheetName, index_col=indexCols)
    if dropna:
        mysheet = mysheet.dropna(axis=0, how='all')
    return mysheet


def getIYCFcostCoverageSaturation(IYCFpackages, IYCFcost):
    packageCostSaturation = {}
    coverage = {}
    for name, package in IYCFpackages.iteritems():
        cost = 0
        packageCostSaturation[name] = {}
        for pop, mode in package:
            cost += IYCFcost[mode][pop]
        packageCostSaturation[name]['unit cost'] = cost
        packageCostSaturation[name]['saturation coverage'] = 0.95
        # tmp baseline coverage
        coverage[name] = 0
    return packageCostSaturation, coverage

def defineIYCFpackages(IYCFpackages, thesePops):
    packagesDict = {}
    for packageName, package in IYCFpackages.groupby(level=[0, 1]):
        if packagesDict.get(packageName[0]) is None:
            packagesDict[packageName[0]] = []
        for mode in package:
            col = package[mode]
            if col.notnull()[0]:
                if mode == 'Mass media':
                    ageModeTuple = [(pop, mode) for pop in thesePops]
                else:
                    ageModeTuple = [(packageName[1], mode)]
                packagesDict[packageName[0]] += ageModeTuple
    return packagesDict

def createIYCFpackages(IYCFpackages, effects, childAges):
    '''Creates IYCF packages based on user input in 'IYCFpackages' '''
    # non-empty cells denote program combination
    # get package combinations
    packagesDict = defineIYCFpackages(IYCFpackages, childAges[:-1] + ['Pregnant women'])
    # create new intervention
    newInterventions = {}
    ORs = {}
    for key, item in packagesDict.items():
        if newInterventions.get(key) is None:
            newInterventions[key] = {}
        for age in childAges:
            ORs[age] = 1.
            for pop, mode in item:
                row = effects.loc[pop, mode]
                thisOR = row[age]
                ORs[age] *= thisOR
        newInterventions[key].update(ORs)
    return newInterventions, packagesDict

def getIYCFtargetPop(packageModalities, targetPops, PWages):
    newTargetPops = {}
    for name, package in packageModalities.items():
        newTargetPops[name] = {}
        for pop, mode in package:
            if newTargetPops[name].get(pop) is None:
                newTargetPops[name][pop] = {}
            newTargetPops[name][pop][mode] = targetPops[mode][pop]
    # convert 'pregnant women' to its age bands
    newTargetPops = stratifyPopIntoAgeGroups(newTargetPops, packageModalities.keys(), PWages, 'Pregnant women', keyLevel=1)
    return newTargetPops


def readSpreadsheet(fileName, keyList, interventionsToKeep=None): # TODO: could get all spreadsheet names and iterate with a general 'readSheet' function, then tinker from there.
    from copy import deepcopy as dcp
    location = fileName
    ages = keyList['ages']
    birthOutcomes = keyList['birthOutcomes']
    wastingList = keyList['wastingList']
    stuntingList = keyList['stuntingList']
    breastfeedingList = keyList['breastfeedingList']
    allPops = keyList['allPops']
    anemiaList = keyList['anemiaList']
    PWages = keyList['pregnantWomenAges']
    WRAages = keyList['reproductiveAges']

    # create user-defined IYCF packages
    IYCFeffects = readSheet(location, 'IYCF package odds ratios', [0,1,2])
    IYCFeffectBF = IYCFeffects.loc['OR for correct breastfeeding']
    IYCFeffectStunting = IYCFeffects.loc['OR for stunting']
    IYCFpackages = readSheet(location, 'IYCF packages', [0,1])

    ORappropriatebfIntervention, packageModalities = createIYCFpackages(IYCFpackages, IYCFeffectBF, ages)
    ORstuntingIntervention = createIYCFpackages(IYCFpackages, IYCFeffectStunting, ages)[0]
    IYCFnames = ORappropriatebfIntervention.keys()
    # get interventions list
    interventionsSheet = pd.read_excel(location, sheetname = 'Interventions cost and coverage', index_col=0)
    interventionList = list(interventionsSheet.index)

    # INTERVENTIONS TARGET POPULATION
    targetPopSheet = readSheet(location, 'Interventions target population', [0, 1])
    # children
    targetPopulation = splitSpreadsheetWithTwoIndexCols(targetPopSheet, 'Children', switchKeys=True)
    # pregnant women
    targetPopulation.update(splitSpreadsheetWithTwoIndexCols(targetPopSheet, 'Pregnant women', switchKeys=True))
    # non-pregnant WRA
    targetPopulation.update(splitSpreadsheetWithTwoIndexCols(targetPopSheet, 'Non-pregnant WRA', switchKeys=True))
    # general pop
    targetPopulation.update(splitSpreadsheetWithTwoIndexCols(targetPopSheet, 'General population', switchKeys=True))
    # add target pop for IYCF packages
    IYCFcostCovSheet = readSheet(location, 'IYCF cost & coverage', [0,1])
    IYCFtarget = splitSpreadsheetWithTwoIndexCols(IYCFcostCovSheet, 'Target populations')
    IYCFcost = splitSpreadsheetWithTwoIndexCols(IYCFcostCovSheet, 'Unit costs')

    IYCFtargetPop = getIYCFtargetPop(packageModalities, IYCFtarget, PWages)
    # change PW & WRA to age groups for interventions other than iYCF
    targetPopulation = stratifyPopIntoAgeGroups(targetPopulation, interventionList, WRAages, 'Non-pregnant WRA', keyLevel=1)
    targetPopulation = stratifyPopIntoAgeGroups(targetPopulation, interventionList, PWages, 'Pregnant women', keyLevel=1)

    ### INTERVENTIONS COST AND COVERAGE
    IYCFcostSaturation, IYCFcoverage = getIYCFcostCoverageSaturation(packageModalities, IYCFcost)

    # include IYCF interventions
    interventionList += IYCFnames
    interventionCompleteList =  dcp(interventionList)
    for intervention in interventionList:
        if "IFAS" in intervention:
            if "malaria" in intervention:
                interventionCompleteList.append(intervention + " with bed nets")
    coverage = dict(interventionsSheet["Baseline coverage"])
    coverage.update(IYCFcoverage)
    costSaturation = interventionsSheet[["saturation coverage", "unit cost"]].to_dict(orient='index')
    costSaturation.update(IYCFcostSaturation)

    if interventionsToKeep is not None: # This is a temporary way not use subset of programs - not a long-term fix
        interventionList = interventionsToKeep
        interventionCompleteList = interventionsToKeep
        coverage = {program: cov for program, cov in coverage.iteritems() if program in interventionsToKeep}
        costSaturation = {program:value for program, value in costSaturation.iteritems() if program in interventionsToKeep}

    # add hidden intervention data to coverage and cost saturation
    hiddenInterventionList = list(set(interventionCompleteList) - set(interventionList))
    for intervention in hiddenInterventionList:
        correspondingIntervention = intervention.replace(" with bed nets", "")
        thisCoverage = coverage[correspondingIntervention]
        coverage.update({intervention : thisCoverage})
        thisCostSaturation = costSaturation[correspondingIntervention]
        costSaturation.update({intervention : thisCostSaturation})

    # fill in the remaining ORs for BF practices & for stunting
    # need to add effect of PPCF on stunting
    ORsheet = readSheet(location, 'Odds ratios', [0,1] )
    ORstunting = dict(ORsheet.loc['OR stunting by intervention'])
    for intervention in list(set(interventionCompleteList) - set(IYCFnames)):
        ORappropriatebfIntervention[intervention] = {}
        ORstuntingIntervention[intervention] = {}
        for age in ages:
            ORappropriatebfIntervention[intervention][age] = 1.
            if "Public provision" in intervention:
                ORstuntingIntervention[intervention][age] = ORstunting[age][intervention]
            else:
                ORstuntingIntervention[intervention][age] = 1.

    ### BASELINE YEAR DEMOGRAPHICS
    demographicsSheet = readSheet(location, 'Baseline year demographics', [0,1])
    # population
    population = splitSpreadsheetWithTwoIndexCols(demographicsSheet, "Current year")
    populationDict = population['Values']
    # mortality
    mortality = splitSpreadsheetWithTwoIndexCols(demographicsSheet, "Mortality rates")
    rawMortality = mortality['Values']
    # food
    food = splitSpreadsheetWithTwoIndexCols(demographicsSheet, "Food")
    foodDemographicsDict = food['Values']
    # join to demographics dict
    populationDict.update(foodDemographicsDict)
    demographics = populationDict
    # WRA age distribution
    WRAageDistribution = splitSpreadsheetWithTwoIndexCols(demographicsSheet, "Women of reproductive age")
    mappingDict = {"Values": WRAages} # make age bands consistent
    WRAageDistribution = mapAgeKeys(WRAageDistribution, mappingDict)
    demographics['population reproductive age'] = WRAageDistribution
    # PW age distribution
    PWageDistribution = splitSpreadsheetWithTwoIndexCols(demographicsSheet, "Age distribution pregnant")
    mappingDict = {'Values': PWages}
    PWageDistribution = mapAgeKeys(PWageDistribution, mappingDict)
    # malaria exposure
    fracExposedMalaria = demographics['fraction at risk of malaria']

    ### DEMOGRAPHIC PROJECTIONS
    projectionsSheet = pd.read_excel(location, sheetname='Demographic projections', index_col=[0])
    projectionsDict = readSheetWithOneIndexCol(projectionsSheet)
    projectedBirths = projectionsDict['number of births']
    projectedWRApop = projectionsDict['total WRA']
    projectedWRApopByWrongAge = {age: projectionsDict[age] for age in projectionsDict.keys() if age.startswith('women')}
    # map to correct keys by string operations
    projectedWRApopByAge = {}
    for ageName in projectedWRApopByWrongAge.keys():
        newAgeName = ageName.partition(' ')[2]
        newAgeName = "WRA: " + newAgeName
        projectedWRApopByAge[newAgeName] = projectedWRApopByWrongAge[ageName]
    projectedPWpop = projectionsDict['pregnant women']
    # general population size
    projectedGeneralPop = projectionsDict['total population']

    ### CAUSES OF DEATH
    causesOfDeathSheet = pd.read_excel(location, sheetname='Causes of death', index_col=[0])
    causeOfDeathDist = readSheetWithOneIndexCol(causesOfDeathSheet)
    causeOfDeathDist = stratifyPopIntoAgeGroups(causeOfDeathDist, ['maternal'], PWages, 'maternal')
    causesOfDeathList = list(causesOfDeathSheet.index)

    ### INCIDENCE OF CONDITIONS
    incidencesSheet = pd.read_excel(location, sheetname='Incidence of conditions', index_col=[0])
    incidences = readSheetWithOneIndexCol(incidencesSheet, scaleFactor=12.) #WARNING HACK should multiply by timestep within code
    conditionsList = list(incidencesSheet.index)

    ### PREVALENCE OF ANEMIA
    # done by anemia type: anemic, not anemic, iron deficiency anemia, severe
    anemiaPrevalenceSheet = readSheet(location, 'Prevalence of anemia', [0,1])
    anemiaTypes = list(anemiaPrevalenceSheet.index.levels[0])
    ageNames = list(anemiaPrevalenceSheet.index.levels[1])
    ageNames = [age for age in ageNames if age != 'All'] # remove 'All'
    anemiaPrevalence = {}
    for colName in anemiaPrevalenceSheet:
        anemiaPrevalence[colName] = {}
        column = anemiaPrevalenceSheet[colName]
        for ageName in ageNames:
            anemiaPrevalence[colName][ageName] = {}
            for anemiaType in anemiaTypes:
                try:
                    if anemiaType == 'Fraction anemia that is severe': # assume uniformly distributed across ages
                        anemiaPrevalence[colName][ageName][anemiaType] = column[anemiaType]['All']
                    else:
                        anemiaPrevalence[colName][ageName][anemiaType] = column[anemiaType][ageName]
                except KeyError:
                    pass
            # no anemia
            anemiaPrevalence[colName][ageName]['not anemic'] = 1. - anemiaPrevalence[colName][ageName]['All anemia']
    # convert age groups to those used in model
    mappingDict = {"Children": ages, "WRA not pregnant": WRAages, "Pregnant women": PWages}
    anemiaDistribution = mapAgeKeys(anemiaPrevalence, mappingDict)
    #rename
    for ageName in ages + WRAages + PWages:
        anemiaThisAge = anemiaDistribution[ageName]
        anemiaThisAge['anemic'] = anemiaThisAge.pop('All anemia')
    # TODO: These are fake values b/c spredsheet has blank
    anemiaDistribution["<1 month"]['anemic'] = .1
    anemiaDistribution["<1 month"]['not anemic'] = .9
    anemiaDistribution["1-5 months"]['anemic'] = .1
    anemiaDistribution["1-5 months"]['not anemic'] = .9

    ### DISTRIBUTIONS
    distributionsSheet = readSheet(location, 'Distributions', [0,1])
    stuntingDistribution = splitSpreadsheetWithTwoIndexCols(distributionsSheet, 'Stunting', scaleFactor=100.)
    wastingDistribution = splitSpreadsheetWithTwoIndexCols(distributionsSheet, 'Wasting', scaleFactor=100.)
    breastfeedingDistribution = splitSpreadsheetWithTwoIndexCols(distributionsSheet, 'Breastfeeding', scaleFactor=100.)
    
    ### DISTRIBUTIONS BIRTHS
    birthDistSheet = readSheet(location, 'Distributions births', [0,1])
    ageOrderDist = splitSpreadsheetWithTwoIndexCols(birthDistSheet, "Birth age order")
    ageOrderDist = ageOrderDist['Fraction']
    intervalDist = splitSpreadsheetWithTwoIndexCols(birthDistSheet, "Birth intervals")
    intervalDist = intervalDist['Fraction']
    

    ### BIRTH OUTCOMES AND RISKS
    birthOutcomesSheet = readSheet(location, 'Birth outcomes & risks', [0,1])
    # distribution
    birthOutcomeDistribution = splitSpreadsheetWithTwoIndexCols(birthOutcomesSheet, "Distribution")
    ORstuntingBirthOutcome = {}
    ORwastingBirthOutcome = {}
    ORwastingBirthOutcome['SAM'] = {}
    ORwastingBirthOutcome['MAM'] = {}
    birthOutcomeDist = {}
    for birthOutcome in birthOutcomeDistribution.keys():
        ORstuntingBirthOutcome[birthOutcome] = birthOutcomeDistribution[birthOutcome]['OR stunting']
        ORwastingBirthOutcome['SAM'][birthOutcome] = birthOutcomeDistribution[birthOutcome]['OR SAM']
        ORwastingBirthOutcome['MAM'][birthOutcome] = birthOutcomeDistribution[birthOutcome]['OR MAM']
        birthOutcomeDist[birthOutcome] = birthOutcomeDistribution[birthOutcome]["Fraction of births"]

    # RR of death by birth outcome
    RRdeathByBirthOutcome = splitSpreadsheetWithTwoIndexCols(birthOutcomesSheet, "RR of death", rowList=causesOfDeathList, switchKeys=True)
    
    # RR bo by birth age order
    RRageOrder = splitSpreadsheetWithTwoIndexCols(birthOutcomesSheet, "RR age order", rowList=ageOrderDist.keys(), switchKeys=True)
    
    # RR bo by birth age order
    RRinterval = splitSpreadsheetWithTwoIndexCols(birthOutcomesSheet, "RR interval", rowList=intervalDist.keys(), switchKeys=True)

    ### RELATIVE RISKS
    RRsheet = readSheet(location, 'Relative risks', [0,1,2])
    RRdeathStunting = readRelativeRisks(RRsheet, 'Stunting', stuntingList, causesOfDeathList)
    RRdeathWasting = readRelativeRisks(RRsheet, 'Wasting', wastingList, causesOfDeathList)
    RRdeathBreastfeeding = readRelativeRisks(RRsheet, 'Breastfeeding', breastfeedingList, causesOfDeathList)
    # child diarrhea
    RRsheet = pd.read_excel(location, sheetname='Relative risks', index_col=[0,1,2])
    childDia = RRsheet.loc['RR child diarrhea'].dropna(axis=1, how = 'all') # drop maternal
    childDia = childDia.loc['Diarrhea incidence'].dropna() # remove rows with NaN
    RRdiarrhea = {}
    for ageName in childDia:
        column = childDia[ageName]
        RRdiarrhea[ageName] = {}
        for breastfeedingCat in breastfeedingList:
            RRdiarrhea[ageName][breastfeedingCat] = column[breastfeedingCat]
    # maternal anemia
    RRsheet = readSheet(location, 'Relative risks', [0,1,2])
    maternalAnemia = RRsheet.loc['Maternal anemia - death risk']
    RRdeathMaternal = {}
    column = maternalAnemia['maternal']
    for cause in causesOfDeathList:
        RRdeathMaternal[cause] = {}
        for anemiaStatus in anemiaList:
            try:
                RRdeathMaternal[cause][anemiaStatus] = column[cause][anemiaStatus]
            except KeyError: # if cause not in sheet, RR=1
                RRdeathMaternal[cause][anemiaStatus] = 1
    RRdeathMaternalAnemia = {age: RRdeathMaternal for age in PWages}
    # women of reproductive age, assume no direct impact of interventions (RR=1). Also no data on children (RR=1) # TODO: probably need to update children.
    RRdeathChildrenWRanemia = {age: {cause: {status: 1. for status in anemiaList} for cause in causesOfDeathList} for age in WRAages + ages}
    # combine all groups into single dictionary
    RRdeathMaternalAnemia.update(RRdeathChildrenWRanemia)
    RRdeathAnemia = RRdeathMaternalAnemia

    ### ODDS RATIOS
    # stunting
    ORsheet = readSheet(location, 'Odds ratios', [0,1])
    # progression
    ORstuntingProgression = dict(ORsheet.loc['OR stunting progression and condition','Stunting progression'])
    del ORstuntingProgression['<1 month'] # not applicable to <1 month
    # by condition
    ORstuntingDia = dict(ORsheet.loc['OR stunting progression and condition','Diarrhea'])
    ORstuntingCondition = {age:{condition: ORstuntingDia[age] for condition in ['Diarrhea']} for age in ages}

    # TODO: we are removing food security group stuff, this can probably go
    # ORstuntingComplementaryFeeding = {}
    # interventionsHere = ORsheet.loc['OR stunting by intervention'].index
    # foodSecurityGroups = []
    # for age in ages:
    #     ORstuntingComplementaryFeeding[age] = {}
    #     for intervention in interventionsHere:
    #         if "Complementary" in intervention and 'iron' not in intervention:
    #             ORstuntingComplementaryFeeding[age][intervention] = ORsheet[age]['OR stunting by intervention'][intervention]
    #             if intervention not in foodSecurityGroups:
    #                 foodSecurityGroups += [intervention]
    # wasting by intervention
    wastingInterventionSheet = readSheet(location, 'Interventions wasting', [0,1])
    ORwastingIntervention = {}
    ORwastingIntervention['SAM'] = splitSpreadsheetWithTwoIndexCols(wastingInterventionSheet, "OR SAM by intervention", rowList=interventionCompleteList)
    ORwastingIntervention['MAM'] = splitSpreadsheetWithTwoIndexCols(wastingInterventionSheet, "OR MAM by intervention", rowList=interventionCompleteList)
    # wasting by condition
    ORwastingCondition = {}
    ORwastingCondition['SAM'] = splitSpreadsheetWithTwoIndexCols(ORsheet, 'OR SAM by condition', rowList=conditionsList)
    ORwastingCondition['MAM'] = splitSpreadsheetWithTwoIndexCols(ORsheet, 'OR MAM by condition', rowList=conditionsList)

    # APPROPRIATE BREASTFEEDING
    breastfeedingSheet = pd.read_excel(location, sheetname='Appropriate breastfeeding')
    ageAppropriateBreastfeeding = dict(breastfeedingSheet.iloc[0])


    # INTERVENTIONS BIRTH OUTCOMES
    interventionsBirthOutcomeSheet = pd.read_excel(location, sheetname='Interventions birth outcomes', index_col=[0,1])
    interventionsBirthOutcome = {}
    for intervention in interventionCompleteList:
        interventionsBirthOutcome[intervention] = {}
        for birthOutcome in birthOutcomes:
            column = interventionsBirthOutcomeSheet[birthOutcome]
            interventionsBirthOutcome[intervention][birthOutcome] = {}
            for value in ['effectiveness', 'affected fraction']:
                try:
                    interventionsBirthOutcome[intervention][birthOutcome][value] = column[intervention][value]
                except KeyError:
                    interventionsBirthOutcome[intervention][birthOutcome][value] = 0.
                    
    # INTERVENTIONS BIRTH AGE
    sheet = pd.read_excel(location, sheetname='Interventions birth age', index_col=[0,1])
    interventionsBirthAge = {}
    for intervention in interventionCompleteList:
        interventionsBirthAge[intervention] = {}
        for birthAge in ageOrderDist.keys():
            if 'Less than 18' in birthAge:
                column = sheet[birthAge]
                interventionsBirthAge[intervention][birthAge] = {}
                for value in ['effectiveness', 'affected fraction']:
                    try:
                        interventionsBirthAge[intervention][birthAge][value] = column[intervention][value]
                    except KeyError:
                        interventionsBirthAge[intervention][birthAge][value] = 0.                

    ### INTERVENTIONS ANEMIA
    # relative risks
    interventionsAnemiaSheet = readSheet(location, 'Interventions anemia', [0,1])
    # remove interventions from RR if we have OR
    interventionsOR = list(interventionsAnemiaSheet.loc["Odds Ratios"].index)
    interventionsRR = [intervention for intervention in interventionCompleteList if intervention not in interventionsOR]
    RRanemiaIntervention = splitSpreadsheetWithTwoIndexCols(interventionsAnemiaSheet, 'Relative Risks', rowList=interventionsRR)
    # odds ratios
    ORanemiaIntervention = splitSpreadsheetWithTwoIndexCols(interventionsAnemiaSheet, 'Odds Ratios', rowList=interventionsOR)

    # INTERVENTIONS AFFECTED FRACTION AND EFFECTIVENESS
    # children
    # warning: currently this applied to all population groups (no tabs for them yet)
    interventionsForChildren = pd.read_excel(location, sheetname='Interventions for children', index_col=[0, 1, 2])
    affectedFraction = readInterventionsByPopulationTabs(interventionsForChildren, 'Affected fraction', interventionCompleteList, allPops, causesOfDeathList + ['Severe diarrhea', 'SAM', 'MAM']) # TODO: warning: severe diarrhea is not listed in 'causes of death' and so causes issues
    effectivenessMortality = readInterventionsByPopulationTabs(interventionsForChildren, 'Effectiveness mortality', interventionCompleteList, allPops, causesOfDeathList)
    effectivenessIncidence = readInterventionsByPopulationTabs(interventionsForChildren, 'Effectiveness incidence', interventionCompleteList, ages, conditionsList) # children only

    # TODO: not currently available in spreadsheet. Need to decide on location
    ORanemiaCondition = {age:{condition:1. for condition in conditionsList} for age in ages}
    fracSevereDia = 0.2 # made up value
    fracSAMtoMAM = 0.1 # fictional
    fracMAMtoSAM = 0.9 # from Jakub

    # FAMILY PLANNING
    sheet = pd.read_excel(location, sheetname='Interventions family planning')
    effectivenessFP = dict(zip(sheet.Method, sheet.Effectiveness))
    distributionFP = dict(zip(sheet.Method, sheet.Distribution))


    spreadsheetData = Data(causesOfDeathList, conditionsList, interventionList, interventionCompleteList,
                           demographics, projectedBirths, rawMortality,
                           causeOfDeathDist, RRdeathAnemia, RRdeathStunting,
                           RRdeathWasting, RRdeathBreastfeeding, RRdeathByBirthOutcome,
                           stuntingDistribution, wastingDistribution, breastfeedingDistribution,
                           incidences, RRdiarrhea, ORstuntingCondition, birthOutcomeDist,
                           ORstuntingProgression, ORstuntingBirthOutcome, ORstuntingIntervention,
                           RRanemiaIntervention, ORanemiaIntervention,
                           ORappropriatebfIntervention, ageAppropriateBreastfeeding, coverage,
                           costSaturation, targetPopulation, affectedFraction,
                           effectivenessMortality, effectivenessIncidence, interventionsBirthOutcome,
                           anemiaDistribution, projectedWRApop, projectedWRApopByAge, projectedPWpop, projectedGeneralPop,
                           PWageDistribution, fracExposedMalaria, ORanemiaCondition, fracSevereDia,
                           ORwastingCondition, ORwastingIntervention, ORwastingBirthOutcome,
                           fracSAMtoMAM, fracMAMtoSAM, effectivenessFP, distributionFP, IYCFtargetPop, IYCFnames, ageOrderDist,
                           intervalDist, RRageOrder, RRinterval, interventionsBirthAge)

    return spreadsheetData

