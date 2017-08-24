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
    RRdiarrhea = {}
    for ageName in ages:
        RRdiarrhea[ageName] = {}
        for breastfeedingCat in breastfeedingList:
            RRdiarrhea[ageName][breastfeedingCat] = df[ageName][breastfeedingCat]

    # READ OR stunting by condition SHEET
    # sets:
    # - ORstuntingCondition
    df = pandas.read_excel(Location, sheetname = 'OR stunting by condition')
    conditionsHere = list(df['Condition'])
    df = pandas.read_excel(Location, sheetname = 'OR stunting by condition', index_col = 'Condition')
    ORstuntingCondition = {}
    for ageName in ages:
        ORstuntingCondition[ageName] = {}
        for condition in conditions:
            ORstuntingCondition[ageName][condition] = 1.
        for condition in conditionsHere:
            ORstuntingCondition[ageName][condition] = df.loc[condition, ageName]

    # READ OR anemia by condition SHEET
    # sets:
    # - ORanemiaCondition
    df = pandas.read_excel(Location, sheetname = 'OR anemia by condition')
    conditionsHere = list(df['Condition'])
    df = pandas.read_excel(Location, sheetname = 'OR anemia by condition', index_col = 'Condition')
    ORanemiaCondition = {}
    for ageName in ages:
        ORanemiaCondition[ageName] = {}
        for condition in conditions:
            ORanemiaCondition[ageName][condition] = 1.
        for condition in conditionsHere:
            ORanemiaCondition[ageName][condition] = df.loc[condition, ageName]

    # READ OR Stunting given Intervention Coverage SHEET
    # sets:
    # - ORstuntingIntervention
    df = pandas.read_excel(Location, sheetname = 'OR stunting by intervention')
    interventionsHere = list(df['Intervention'])
    df = pandas.read_excel(Location, sheetname = 'OR stunting by intervention', index_col = 'Intervention')
    ORstuntingIntervention = {}
    for ageName in ages:
        ORstuntingIntervention[ageName] = {}
        for intervention in interventionList:
            ORstuntingIntervention[ageName][intervention] = 1.
        for intervention in interventionsHere:
            ORstuntingIntervention[ageName][intervention] = df.loc[intervention, ageName]

    # READ RR anemic by intervention sheet
    # sets for all interventions
    # sets:
    # - RRanemiaIntervention
    df = pandas.read_excel(Location, sheetname = 'RR anemic by intervention')
    interventionsRR = list(df['Intervention'])
    df = pandas.read_excel(Location, sheetname='RR anemic by intervention', index_col = 'Intervention')
    RRanemiaIntervention = {}
    for pop in allPops + ['general population']:
        RRanemiaIntervention[pop] = {}
        for intervention in interventionList:
            RRanemiaIntervention[pop][intervention] = 1.
        for intervention in interventionsRR:
            RRanemiaIntervention[pop][intervention] = df.loc[intervention, pop]

    # READ OR anemic by intervention sheet
    # checks in the interventionsOR list to keep track
    # sets:
    # - ORanemiaIntervention
    df = pandas.read_excel(Location, sheetname = 'OR anemic by intervention')
    interventionsOR = list(df['Intervention'])
    df = pandas.read_excel(Location, sheetname='OR anemic by intervention', index_col = 'Intervention')
    ORanemiaIntervention = {}
    for pop in allPops + ['general population']:
        ORanemiaIntervention[pop] = {}
        for intervention in interventionList:
            if intervention in interventionsOR:
                # remove if OR instead of RR
                del RRanemiaIntervention[pop][intervention]
                ORanemiaIntervention[pop][intervention] = df.loc[intervention, pop]




    # READ OR Appropriate Breastfeeding given OR Appropriate Breastfeeding SHEET
    # sets:
    # - ORappropriatebfIntervention
    df = pandas.read_excel(Location, sheetname = 'OR correctBF by interventn')
    interventionsHere = list(df['Intervention'])
    df = pandas.read_excel(Location, sheetname = 'OR correctBF by interventn', index_col = 'Intervention')
    ORappropriatebfIntervention = {}
    for ageName in ages:
        ORappropriatebfIntervention[ageName] = {}
        for intervention in interventionList:
            ORappropriatebfIntervention[ageName][intervention] = 1.
        for intervention in interventionsHere:
            ORappropriatebfIntervention[ageName][intervention] = df.loc[intervention, ageName]

    #  READ Appropriate Breastfeeding Practice SHEET
    #  sets:
    #  - ageAppropriateBreastfeeding
    df = pandas.read_excel(Location, sheetname = 'Appropriate breastfeeding')
    ageAppropriateBreastfeeding = dict(zip(list(df.columns.values), df.iloc[0]))

    #  READ birth outcome distribution SHEET
    #  sets:
    #  - birthOutcomeDist (partial)
    df = pandas.read_excel(Location, sheetname = 'birth outcome distribution')
    birthOutcomeDist_partial = dict(zip(list(df.columns.values), df.iloc[0]))
    # construct full birthOutcome distribution
    birthOutcomeDist = {}
    BOsum = 0.
    for birthOutcome in ["Pre-term SGA", "Pre-term AGA", "Term SGA"]:
        birthOutcomeDist[birthOutcome] = birthOutcomeDist_partial[birthOutcome]
        BOsum += birthOutcomeDist[birthOutcome]
    birthOutcomeDist["Term AGA"] = 1. - BOsum

    #  READ OR birth outcome stunting SHEET
    #  sets:
    #  - ORstuntingBirthOutcome
    df = pandas.read_excel(Location, sheetname = 'OR stunting by birth outcome')
    ORstuntingBirthOutcome = dict(zip(list(df.columns.values), df.iloc[0]))

    #  READ Current Intervention Coverages SHEET
    #  sets:
    #  - coverage
    #  - costSaturation
    df = pandas.read_excel(Location, sheetname = 'Interventions cost and coverage', index_col = 'Intervention')
    coverage = {}
    costSaturation = {}
    costinfoList = ["unit cost","saturation coverage"]
    for intervention in interventionList:
        coverage[intervention] = df.loc[intervention, "baseline coverage"]
        costSaturation[intervention] = {}
        for costinfo in costinfoList:
            costSaturation[intervention][costinfo] = df.loc[intervention, costinfo]

    # READ Intervention Target Population Matrix SHEET
    # sets:
    # - targetPopulation
    df = pandas.read_excel(Location, sheetname = 'Interventions target population', index_col = 'Intervention')
    targetPopulation = {}
    for intervention in interventionList:
        targetPopulation[intervention] = {}
        for pop in allPops + ['general population']:
            targetPopulation[intervention][pop] = df.loc[intervention, pop]

    # READ Interventions birth outcome SHEET
    # sets:
    # - interventionsBirthOutcome
    df = pandas.read_excel(Location, sheetname = 'Interventions birth outcome', index_col = [0])
    #get the list of interventions
    mylist = list(df.index.values)
    myset = set(mylist)
    interventionsHere = list(myset)
    #do the rest
    df = pandas.read_excel(Location, sheetname = 'Interventions birth outcome', index_col = [0, 1])
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
                  
