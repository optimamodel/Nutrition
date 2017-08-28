# -*- coding: utf-8 -*-
"""
Created on Fri Feb 26 15:57:07 2016

@author: ruth
"""
import pandas as pd

class Data:
    def __init__(self, causesOfDeath, conditions, interventionList, 
                 demographics, projectedBirths, rawMortality, causeOfDeathDist, RRdeathAnemia,
                 RRdeathStunting, RRdeathWasting, RRdeathBreastfeeding, 
                 RRdeathByBirthOutcome, stuntingDistribution, wastingDistribution,
                 breastfeedingDistribution, incidences, RRdiarrhea, ORstuntingCondition,
                 birthOutcomeDist, ORstuntingProgression, ORstuntingBirthOutcome,
                 ORstuntingIntervention, RRanemiaIntervention, ORanemiaIntervention,
                 ORappropriatebfIntervention,
                 ageAppropriateBreastfeeding, coverage, costSaturation,
                 targetPopulation, affectedFraction, effectivenessMortality,
                 effectivenessIncidence, interventionsBirthOutcome, foodSecurityGroups,
                 ORstuntingComplementaryFeeding, anemiaDistribution,
                 projectedWRApop, projectedWRApopByAge, projectedPWpop,
                 PWageDistribution, fracAnemicNotPoor,
                 fracAnemicPoor, fracAnemicExposedMalaria, fracExposedMalaria, ORanemiaCondition, fracSevereDia):

        self.causesOfDeath = causesOfDeath
        self.conditions = conditions
        self.interventionList = interventionList
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
        self.birthOutcomeDist = birthOutcomeDist
        self.ORstuntingIntervention = ORstuntingIntervention
        self.RRanemiaIntervention = RRanemiaIntervention
        self.ORanemiaIntervention = ORanemiaIntervention
        self.ORappropriatebfIntervention = ORappropriatebfIntervention
        self.ageAppropriateBreastfeeding = ageAppropriateBreastfeeding
        self.coverage = coverage
        self.costSaturation = costSaturation
        self.targetPopulation = targetPopulation
        self.affectedFraction = affectedFraction
        self.effectivenessMortality = effectivenessMortality
        self.effectivenessIncidence = effectivenessIncidence
        self.interventionsBirthOutcome = interventionsBirthOutcome
        self.foodSecurityGroups = foodSecurityGroups
        self.ORstuntingComplementaryFeeding = ORstuntingComplementaryFeeding
        self.anemiaDistribution = anemiaDistribution
        self.projectedWRApop = projectedWRApop
        self.projectedWRApopByAge = projectedWRApopByAge
        self.projectedPWpop = projectedPWpop
        self.PWageDistribution = PWageDistribution
        self.fracAnemicNotPoor = fracAnemicNotPoor
        self.fracAnemicPoor = fracAnemicPoor
        self.fracAnemicExposedMalaria = fracAnemicExposedMalaria
        self.fracExposedMalaria = fracExposedMalaria
        self.ORanemiaCondition = ORanemiaCondition
        self.fracSevereDia = fracSevereDia

def readSheetWithOneIndexCol(sheet, scaleFactor=1.):
    resultDict = {}
    for columnName in sheet:
        resultDict[columnName] = sheet[columnName] / scaleFactor
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
            newAgeGroups = {age:subDict for age in listOfAgeGroups}
            dictToUpdate[key].update(newAgeGroups)
    return dictToUpdate

def readSpreadsheet(fileName, keyList):
    location = fileName
    ages = keyList['ages']
    birthOutcomes = keyList['birthOutcomes']
    wastingList = keyList['wastingList']
    stuntingList = keyList['stuntingList']
    breastfeedingList = keyList['breastfeedingList']
    allPops = keyList['allPops']
    anemiaList = keyList['anemiaList']
    PWages = ["PW: 15-19 years", "PW: 20-29 years", "PW: 30-39 years", "PW: 40-49 years"]
    WRAages = ['WRA: 15-19 years', 'WRA: 20-29 years', 'WRA: 30-39 years', 'WRA: 40-49 years']

    ### INTERVENTIONS COST AND COVERAGE
    interventionsSheet = pd.read_excel(location, sheetname = 'Interventions cost and coverage', index_col=0)
    interventionList = list(interventionsSheet.index)
    coverage = dict(interventionsSheet["Baseline coverage"])
    costSaturation = interventionsSheet[["Saturation coverage", "Unit cost"]].to_dict(orient='index')

    ### BASELINE YEAR DEMOGRAPHICS
    demographicsSheet = pd.read_excel(location, sheetname='Baseline year demographics', index_col=[0, 1])
    demographicsSheet = demographicsSheet.dropna(how='all')
    # population
    population = splitSpreadsheetWithTwoIndexCols(demographicsSheet, "Current year")
    populationDict = population['Values']
    # mortality
    mortality = splitSpreadsheetWithTwoIndexCols(demographicsSheet, "Mortality")
    rawMortality = mortality['Values']
    # food
    food = splitSpreadsheetWithTwoIndexCols(demographicsSheet, "Food")
    foodDemographicsDict = food['Values']
    # join into demographics dict
    populationDict.update(foodDemographicsDict)
    demographics = populationDict
    # WRA age distribution
    WRAageDistribution = splitSpreadsheetWithTwoIndexCols(demographicsSheet, "Women of reproductive age")
    mappingDict = {"Values": WRAages} # make age bands consistent
    WRAageDistribution = mapAgeKeys(WRAageDistribution, mappingDict)
    demographics['population reproductive age'] = WRAageDistribution
    # PW age distribution
    PWageDistribution = splitSpreadsheetWithTwoIndexCols(demographicsSheet, "Age distribution pregnant")

    ### DEMOGRAPHIC PROJECTIONS
    projectionsSheet = pd.read_excel(location, sheetname='Demographic projections', index_col=[0])
    projectionsDict = readSheetWithOneIndexCol(projectionsSheet)
    projectedBirths = projectionsDict['number of births']
    projectedWRApop = projectionsDict['total WRA']
    projectedWRApopByAge = {age: projectionsDict[age] for age in projectionsDict.keys() if age.startswith('women')}
    projectedPWpop = projectionsDict['pregnant women']

    ### CAUSES OF DEATH
    causesOfDeathSheet = pd.read_excel(location, sheetname='Causes of death', index_col=[0])
    causeOfDeathDist = readSheetWithOneIndexCol(causesOfDeathSheet)
    causesOfDeathList = list(causesOfDeathSheet.index)

    ### INCIDENCE OF CONDITIONS
    incidencesSheet = pd.read_excel(location, sheetname='Incidence of conditions', index_col=[0])
    incidences = readSheetWithOneIndexCol(incidencesSheet, scaleFactor=12.) #WARNING HACK should multiply by timestep within code
    conditionsList = list(incidencesSheet.index)

    ### PREVALENCE OF ANEMIA
    # done by anemia type: anemic, not anemic, iron deficiency anemia, severe
    anemiaPrevalenceSheet = pd.read_excel(location, sheetname='Prevalence of anemia', index_col=[0,1])
    anemiaPrevalenceSheet = anemiaPrevalenceSheet.dropna(how='all')
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
            anemiaPrevalence[colName][ageName]['No anemia'] = 1. - anemiaPrevalence[colName][ageName]['All anemia']
    # convert age groups to those used in model
    mappingDict = {"Children": ages, "WRA not pregnant": WRAages, "Pregnant women": PWages}
    anemiaDistribution = mapAgeKeys(anemiaPrevalence, mappingDict)


    ### DISTRIBUTIONS
    distributionsSheet = pd.read_excel(location, sheetname='Distributions', index_col=[0,1])
    distributionsSheet = distributionsSheet.dropna()
    stuntingDistribution = splitSpreadsheetWithTwoIndexCols(distributionsSheet, 'Stunting', scaleFactor=100.)
    wastingDistribution = splitSpreadsheetWithTwoIndexCols(distributionsSheet, 'Wasting', scaleFactor=100.)
    breastfeedingDistribution = splitSpreadsheetWithTwoIndexCols(distributionsSheet, 'Breastfeeding', scaleFactor=100.)

    ### BIRTH OUTCOMES AND RISKS
    birthOutcomesSheet = pd.read_excel(location, sheetname='Birth outcomes & risks', index_col=[0,1])
    birthOutcomesSheet = birthOutcomesSheet.dropna()
    # distribution
    birthOutcomeDistribution = splitSpreadsheetWithTwoIndexCols(birthOutcomesSheet, "Distribution")
    ORstuntingBirthOutcome = {}
    birthOutcomeDist = {}
    for birthOutcome in birthOutcomeDistribution.keys():
        ORstuntingBirthOutcome[birthOutcome] = birthOutcomeDistribution[birthOutcome]['OR stunting']
        birthOutcomeDist[birthOutcome] = birthOutcomeDistribution[birthOutcome]["Fraction of births"]

    # RR of death by birth outcome
    RRdeathByBirthOutcome = splitSpreadsheetWithTwoIndexCols(birthOutcomesSheet, "RR of death", rowList=causesOfDeathList)

    ### RELATIVE RISKS # TODO: now that we have new types of anemia, do the RR treat those who are only severely anemic??
    RRsheet = pd.read_excel(location, sheetname='Relative risks', index_col=[0,1,2])
    RRsheet = RRsheet.dropna()
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
    RRsheet = pd.read_excel(location, sheetname='Relative risks', index_col=[0,1,2])
    maternalAnemia = RRsheet.loc['Maternal anemia - death risk']
    RRdeathMaternal = {}
    column = maternalAnemia['maternal']
    for cause in causesOfDeathList:
        RRdeathMaternal[cause] = {}
        for anemiaStatus in anemiaList:
            try:
                RRdeathMaternal[cause][anemiaStatus] = column[cause][anemiaStatus]
            except KeyError: # if cause not in shet, RR=1
                RRdeathMaternal[cause][anemiaStatus] = 1
    RRdeathMaternalAnemia = {age: RRdeathMaternal for age in PWages}
    # women of reproductive age, assume no direct impact of interventions (RR=1)
    RRdeathWRAanemia = {age: {cause: {status: 1. for status in anemiaList} for cause in causesOfDeathList} for age in WRAages}
    # combine all groups into single dictionary
    # TODO: need children
    RRdeathMaternalAnemia.update(RRdeathWRAanemia)
    RRdeathAnemia = RRdeathMaternalAnemia

    # TODO: need RR/OR anemia by intervention, no longer using general population. Also account for having a mix of OR and RR for interventions



    ### ODDS RATIOS
    # stunting
    ORsheet = pd.read_excel(location, sheetname='Odds ratios', index_col=[0,1])
    ORsheet = ORsheet.dropna(axis=0, how='all') # drop rows of all NaN
    # progression
    ORstuntingProgression = dict(ORsheet.loc['OR stunting progression and condition','Stunting progression'])
    del ORstuntingProgression['<1 month'] # not applicable to <1 month
    # by condition
    ORstuntingCondition = dict(ORsheet.loc['OR stunting progression and condition','Diarrhea'])
    # by intervention
    ORstuntingIntervention = splitSpreadsheetWithTwoIndexCols(ORsheet, "OR stunting by intervention", rowList=interventionList)
    ORstuntingComplementaryFeeding = {}
    interventionsHere = ORsheet.loc['OR stunting by intervention'].index
    foodSecurityGroups = []
    for age in ages:
        ORstuntingComplementaryFeeding[age] = {}
        for intervention in interventionsHere:
            if "Complementary" in intervention:
                ORstuntingComplementaryFeeding[age][intervention] = ORsheet[age]['OR stunting by intervention'][intervention]
                foodSecurityGroups += [intervention]
    # TODO: what about prophylactic zinc supplementation? doesn't seem to be used at all (gets forgotten about)

    # correct breastfeeding
    ORappropriatebfIntervention = splitSpreadsheetWithTwoIndexCols(ORsheet, "OR for correct breastfeeding by intervention", rowList=interventionList)

    # APPROPRIATE BREASTFEEDING
    breastfeedingSheet = pd.read_excel(location, sheetname='Appropriate breastfeeding')
    ageAppropriateBreastfeeding = dict(breastfeedingSheet.iloc[0])

    # INTERVENTIONS TARGET POPULATION
    targetPopSheet = pd.read_excel(location, sheetname='Interventions target population', index_col=[0,1])
    targetPopSheet = targetPopSheet.dropna(how='all')
    # children
    targetPopulation = splitSpreadsheetWithTwoIndexCols(targetPopSheet, 'Children', switchKeys=True)
    # pregnant women
    targetPopulation.update(splitSpreadsheetWithTwoIndexCols(targetPopSheet, 'Pregnant women', switchKeys=True))
    # non-pregnant WRA
    targetPopulation.update(splitSpreadsheetWithTwoIndexCols(targetPopSheet, 'Non-pregnant WRA', switchKeys=True))
    # general pop # TODO: how do we want to handle the general pop? Not the same as current implementation in spreadsheet
    #  NO MORE GENERAL POP!
    targetPopulation.update(splitSpreadsheetWithTwoIndexCols(targetPopSheet, 'General population', switchKeys=True))

    # INTERVENTIONS BIRTH OUTCOMES
    interventionsBirthOutcomeSheet = pd.read_excel(location, sheetname='Interventions birth outcomes', index_col=[0,1])
    interventionsBirthOutcome = {}
    for intervention in interventionList:
        interventionsBirthOutcome[intervention] = {}
        for birthOutcome in birthOutcomes:
            column = interventionsBirthOutcomeSheet[birthOutcome]
            interventionsBirthOutcome[intervention][birthOutcome] = {}
            for value in ['effectiveness', 'affected fraction']:
                try:
                    interventionsBirthOutcome[intervention][birthOutcome][value] = column[intervention][value]
                except KeyError:
                    interventionsBirthOutcome[intervention][birthOutcome][value] = 0.

    # INTERVENTIONS AFFECTED FRACTION AND EFFECTIVENESS
    # children
    # warning: currently this applied to all population groups (no tabs for them yet)
    interventionsForChildren = pd.read_excel(location, sheetname='Interventions for children', index_col=[0, 1, 2])
    affectedFraction = readInterventionsByPopulationTabs(interventionsForChildren, 'Affected fraction', interventionList, allPops, causesOfDeathList)
    effectivenessMortality = readInterventionsByPopulationTabs(interventionsForChildren, 'Effectiveness mortality', interventionList, allPops, causesOfDeathList)
    effectivenessIncidence = readInterventionsByPopulationTabs(interventionsForChildren, 'Effectiveness incidence', interventionList, ages, conditionsList) # children only
    # TODO: interventions for other populations can go here...



    # TODO: not currently available in spreadsheet
    RRanemiaIntervention = {}
    ORanemiaIntervention = {}
    fracAnemicNotPoor = {}
    fracAnemicPoor = {}
    fracAnemicExposedMalaria = {}
    fracExposedMalaria = {}
    ORanemiaCondition = {}
    fracSevereDia = 0.2 # made up value

    spreadsheetData = Data(causesOfDeathList, conditionsList, interventionList, demographics,
                           projectedBirths, rawMortality, causeOfDeathDist, RRdeathAnemia, RRdeathStunting,
                           RRdeathWasting, RRdeathBreastfeeding, RRdeathByBirthOutcome,
                           stuntingDistribution, wastingDistribution, breastfeedingDistribution,
                           incidences, RRdiarrhea, ORstuntingCondition, birthOutcomeDist,
                           ORstuntingProgression, ORstuntingBirthOutcome, ORstuntingIntervention,
                           RRanemiaIntervention, ORanemiaIntervention,
                           ORappropriatebfIntervention, ageAppropriateBreastfeeding, coverage,
                           costSaturation, targetPopulation, affectedFraction,
                           effectivenessMortality, effectivenessIncidence, interventionsBirthOutcome,
                           foodSecurityGroups, ORstuntingComplementaryFeeding, anemiaDistribution,
                           projectedWRApop, projectedWRApopByAge, projectedPWpop, PWageDistribution,
                           fracAnemicNotPoor, fracAnemicPoor, fracAnemicExposedMalaria,
                           fracExposedMalaria, ORanemiaCondition, fracSevereDia)

    return spreadsheetData
                  
