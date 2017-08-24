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
    interventionsBirthOutcome = {}
    # initialise
    for intervention in interventionList:
        interventionsBirthOutcome[intervention] = {}
        for outcome in birthOutcomes:
            interventionsBirthOutcome[intervention][outcome] = {}
            for value in ['effectiveness', 'affected fraction']:
                interventionsBirthOutcome[intervention][outcome][value] = 0.
    # complete # WARNING allowing for all causes of death, but completing according to condition
    for intervention in interventionsHere:
        for outcome in birthOutcomes:
            for value in ['effectiveness', 'affected fraction']:
                interventionsBirthOutcome[intervention][outcome][value] = df.loc[intervention][outcome][value]
    # READ Interventions affected fraction SHEET
    # sets:
    # - affectedFraction
    df = pandas.read_excel(Location, sheetname = 'Interventions affected fraction', index_col = [0])
    #get the list of interventions
    mylist = list(df.index.values)
    myset = set(mylist)
    interventionsHere = list(myset)
    #do the rest
    df = pandas.read_excel(Location, sheetname = 'Interventions affected fraction', index_col = [0, 1])
    affectedFraction = {}
    # initialise
    for intervention in interventionList:
        affectedFraction[intervention] = {}
        for pop in allPops:
            affectedFraction[intervention][pop] = {}
            for cause in causesOfDeath:
                affectedFraction[intervention][pop][cause] = 0.
    # complete # WARNING allowing for all causes of death, but completing according to condition
    for intervention in interventionsHere:
        for pop in allPops:
            conditionsHere = df.loc[intervention][pop].keys()
            for condition in conditionsHere:
                affectedFraction[intervention][pop][condition] = df.loc[intervention][pop][condition]

    # READ Interventions mortality effectiveness SHEET
    # sets:
    # - effectivenessMortality
    df = pandas.read_excel(Location, sheetname = 'Interventions mortality eff', index_col = [0])
    #get the list of interventions
    mylist = list(df.index.values)
    myset = set(mylist)
    interventionsHere = list(myset)
    #do the rest
    df = pandas.read_excel(Location, sheetname = 'Interventions mortality eff', index_col = [0, 1])
    effectivenessMortality = {}
    # initialise
    for intervention in interventionList:
        effectivenessMortality[intervention] = {}
        for pop in allPops:
            effectivenessMortality[intervention][pop] = {}
            for cause in causesOfDeath:
                effectivenessMortality[intervention][pop][cause] = 0.

    # complete
    for intervention in interventionsHere:
        for pop in allPops:
            causesHere = df.loc[intervention][pop].keys()
            for cause in causesHere:
                effectivenessMortality[intervention][pop][cause] = df.loc[intervention][pop][cause]

    # READ Interventions incidence effectiveness SHEET
    # sets
    # - effectivenessIncidence
    df = pandas.read_excel(Location, sheetname = 'Interventions incidence eff', index_col = [0])
    #get the list of interventions
    mylist = list(df.index.values)
    myset = set(mylist)
    interventionsHere = list(myset)
    #do the rest
    df = pandas.read_excel(Location, sheetname = 'Interventions incidence eff', index_col = [0, 1])
    effectivenessIncidence = {}
    # initialise
    for intervention in interventionList:
        effectivenessIncidence[intervention] = {}
        for ageName in ages:
            effectivenessIncidence[intervention][ageName] = {}
            for condition in conditions:
                effectivenessIncidence[intervention][ageName][condition] = 0.
    # complete
    for intervention in interventionsHere:
        for ageName in ages:
            conditionsHere = df.loc[intervention][ageName].keys()
            for condition in conditionsHere:
                effectivenessIncidence[intervention][ageName][condition] = df.loc[intervention][ageName][condition]

    # READ OR stunting for complements SHEET
    # sets:
    # - ORstuntingComplementaryFeeding
    df = pandas.read_excel(Location, sheetname = 'OR stunting by compfeeding')
    foodSecurityGroups = list(df['Food security & education'])
    df = pandas.read_excel(Location, sheetname = 'OR stunting by compfeeding', index_col = 'Food security & education')
    ORstuntingComplementaryFeeding = {}
    for ageName in ages:
        ORstuntingComplementaryFeeding[ageName] = {}
        for group in foodSecurityGroups:
            ORstuntingComplementaryFeeding[ageName][group] = df.loc[group, ageName]

    # READ fraction anemic not poor SHEET
    df = pandas.read_excel(Location, sheetname = 'Frac anemic not poor')
    fracAnemicNotPoor = dict(zip(list(df.columns.values), df.iloc[0]))

    # READ fraction anemic poor SHEET
    df = pandas.read_excel(Location, sheetname = 'Frac anemic poor')
    fracAnemicPoor = dict(zip(list(df.columns.values), df.iloc[0]))    
    
    # READ fraction anemic exposed to malaria SHEET
    df = pandas.read_excel(Location, sheetname = 'Frac anemic exposed malaria')
    fracAnemicExposedMalaria = dict(zip(list(df.columns.values), df.iloc[0]))
    
    # READ fraction exposed to malaria SHEET
    df = pandas.read_excel(Location, sheetname = 'Frac exposed malaria')
    fracExposedMalaria = dict(zip(list(df.columns.values), df.iloc[0]))

    spreadsheetData = Data(causesOfDeath, conditions, interventionList, demographics,
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
                  
