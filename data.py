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
                 projectedReproductiveAge, fracAnemicNotPoor, fracAnemicPoor, 
                 fracAnemicExposedMalaria, fracExposedMalaria, ORanemiaCondition):

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
        self.projectedReproductiveAge = projectedReproductiveAge
        self.fracAnemicNotPoor = fracAnemicNotPoor
        self.fracAnemicPoor = fracAnemicPoor
        self.fracAnemicExposedMalaria = fracAnemicExposedMalaria
        self.fracExposedMalaria = fracExposedMalaria
        self.ORanemiaCondition = ORanemiaCondition

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



def readSpreadsheet(fileName, keyList):
    location = fileName
    ages = keyList['ages']
    birthOutcomes = keyList['birthOutcomes']
    wastingList = keyList['wastingList']
    stuntingList = keyList['stuntingList']
    breastfeedingList = keyList['breastfeedingList']
    allPops = keyList['allPops']
    anemiaList = keyList['anemiaList']


    ### INTERVENTIONS COST AND COVERAGE
    # TODO: not complete in spreadsheet therefore some spaces wll be NaN.
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

    ### DEMOGRAPHIC PROJECTIONS
    projectionsSheet = pd.read_excel(location, sheetname='Demographic projections', index_col=[0])
    projectionsDict = readSheetWithOneIndexCol(projectionsSheet)
    projectedBirths = projectionsDict['number of births']
    projectedReproductiveAge = projectionsDict['total WRA']

    ### CAUSES OF DEATH
    causesOfDeathSheet = pd.read_excel(location, sheetname='Causes of death', index_col=[0])
    causeOfDeathDist = readSheetWithOneIndexCol(causesOfDeathSheet)
    causesOfDeathList = list(causesOfDeathSheet.index)

    ### INCIDENCE OF CONDITIONS
    # TODO: may need to divide by 12
    incidencesSheet = pd.read_excel(location, sheetname='Incidence of conditions', index_col=[0])
    incidences = readSheetWithOneIndexCol(incidencesSheet, scaleFactor=12.) #WARNING HACK should multiply by timestep within code
    conditionsList = list(incidencesSheet.index)

    ### PREVALENCE OF ANEMIA
    # done by anemia type
    anemiaPrevalenceSheet = pd.read_excel(location, sheetname='Prevalence of anemia', index_col=[0,1])
    anemiaPrevalenceSheet = anemiaPrevalenceSheet.dropna(how='all')
    anemiaTypes = anemiaPrevalenceSheet.index.levels[0]
    ageNames = anemiaPrevalenceSheet.index.levels[1]
    anemiaPrevalence = {}
    for colName in anemiaPrevalenceSheet:
        column = anemiaPrevalenceSheet[colName]
        for anemiaType in anemiaTypes:
            anemiaPrevalence[anemiaType] = {}
            for ageName in ageNames:
                try:
                    anemiaPrevalence[anemiaType][ageName] = column[anemiaType][ageName]
                except KeyError:
                    pass
    # severe
    anemiaType = 'Fraction anemia that is severe'
    anemiaPrevalence[anemiaType] = {}
    for colName in anemiaPrevalenceSheet:
        column = anemiaPrevalenceSheet[colName]
        anemiaPrevalence[anemiaType][colName] = column[anemiaType]['All']


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

    ### RELATIVE RISKS
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
    maternalAnemia = RRsheet.loc['Maternal anemia']
    RRdeathMaternalAnemia = {}
    column = maternalAnemia['maternal']
    for cause in causesOfDeathList:
        RRdeathMaternalAnemia[cause] = {}
        for anemiaStatus in anemiaList:
            try:
                RRdeathMaternalAnemia[cause][anemiaStatus] = column[cause][anemiaStatus]
            except KeyError: # if cause not in shet, RR=1
                RRdeathMaternalAnemia[cause][anemiaStatus] = 1
    # women of reproductive age, assume no direct impact of interventions (RR=1)
    RRdeathWRAanemia = {cause: 1. for cause in causesOfDeathList}
    # combine all groups into single dictionary
    # TODO: need children
    RRdeathAnemia = RRdeathMaternalAnemia.update(RRdeathWRAanemia)


    # TODO: need RR/OR anemia by intervention, don't forget to use general population. Also account for having a mix of OR and RR for interventions



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
                           projectedReproductiveAge, fracAnemicNotPoor, fracAnemicPoor, fracAnemicExposedMalaria,
                           fracExposedMalaria, ORanemiaCondition)

    return spreadsheetData
                  
