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
def readSpreadsheet(fileName, keyList):
    import pandas
    Location = fileName
    ages = keyList['ages']
    birthOutcomes = keyList['birthOutcomes']
    wastingList = keyList['wastingList']
    stuntingList = keyList['stuntingList']
    breastfeedingList = keyList['breastfeedingList']
    allPops = keyList['allPops']
    anemiaList = keyList['anemiaList']

    #get list of ages and causesOfDeath
    df = pandas.read_excel(Location, sheetname = 'causes of death')
    causesOfDeath = list(df['Cause'])
    #get list of conditions
    df = pandas.read_excel(Location, sheetname = 'Incidence of conditions')
    conditions = list(df['Condition'])
    #get list of interventions
    df = pandas.read_excel(Location, sheetname = 'Interventions cost and coverage')
    interventionList = list(df['Intervention'])

    # READ demographics SHEET
    # sets:
    # - demographics
    df = pandas.read_excel(Location, sheetname = 'demographics')
    indicatorsList = list(df['indicators'])
    df = pandas.read_excel(Location, sheetname = 'demographics', index_col = 'indicators')
    demographics = {}
    for indicator in indicatorsList:
        demographics[indicator] = df.loc[indicator,'data']

    # READ projected births SHEET
    # sets:
    # - projectedBirths
    df = pandas.read_excel(Location, sheetname = 'projected births')
    projectedBirths = list(df['number of births'])

    # READ projected reproductive age SHEET
    # sets:
    # - projectedReproductiveAge
    df = pandas.read_excel(Location, sheetname = 'projected reproductive age')
    projectedReproductiveAge = list(df['population 15-19 years old'])


    #  READ TOTAL MORTALITY SHEET
    #  sets:
    #  - rawMortality
    df = pandas.read_excel(Location, sheetname = 'mortality rates')
    rawMortality = dict(zip(list(df.columns.values), df.iloc[0]))

    #  READ MORTALITY SHEET
    #  sets:
    #  - causeOfDeathDist
    df = pandas.read_excel(Location, sheetname = 'causes of death', index_col = 'Cause')
    causeOfDeathDist = {}
    for pop in allPops:
        causeOfDeathDist[pop] = {}
        for cause in causesOfDeath:
            causeOfDeathDist[pop][cause] = df.loc[cause, pop]

    #  READ RRStunting SHEET
    #  sets:
    #  - RRdeathStunting
    df = pandas.read_excel(Location, sheetname = 'RR death by stunting', index_col = [0])
    #get the list of causes for which we have relative risks
    mylist = list(df.index.values)
    myset = set(mylist)
    listCausesRRdeathStunting = list(myset)
    #put the RR into RRdeathStunting
    df = pandas.read_excel(Location, sheetname = 'RR death by stunting', index_col = [0, 1])
    RRdeathStunting = {}
    for ageName in ages:
        RRdeathStunting[ageName] = {}
        for cause in causesOfDeath:
            RRdeathStunting[ageName][cause] = {}
            for stuntingCat in stuntingList:
                if cause in listCausesRRdeathStunting: #if no RR given for this cause then set to 1
                    RRdeathStunting[ageName][cause][stuntingCat] = df.loc[cause][ageName][stuntingCat]
                else:
                    RRdeathStunting[ageName][cause][stuntingCat] = 1

    #  READ RRWasting SHEET
    #  sets:
    #  - RRdeathWasting
    df = pandas.read_excel(Location, sheetname = 'RR death by wasting', index_col = [0])
    #get the list of causes for which we have relative risks
    mylist = list(df.index.values)
    myset = set(mylist)
    listCausesRRdeathWasting = list(myset)
    #put the RR into RRdeathWasting
    df = pandas.read_excel(Location, sheetname = 'RR death by wasting', index_col = [0, 1])
    RRdeathWasting = {}
    for ageName in ages:
        RRdeathWasting[ageName] = {}
        for cause in causesOfDeath:
            RRdeathWasting[ageName][cause] = {}
            for wastingCat in wastingList:
                if cause in listCausesRRdeathWasting: #if no RR given for this cause then set to 1
                    RRdeathWasting[ageName][cause][wastingCat] = df.loc[cause][ageName][wastingCat]
                else:
                    RRdeathWasting[ageName][cause][wastingCat] = 1

    #  READ RRBreastfeeding SHEET
    #  sets:
    #  - RRdeathBreastfeeding
    df = pandas.read_excel(Location, sheetname = 'RR death by breastfeeding', index_col = [0])
    #get the list of causes for which we have relative risks
    mylist = list(df.index.values)
    myset = set(mylist)
    listCausesRRdeathBreastfeeding = list(myset)
    #put the RR into RRdeathBreastfeeding
    df = pandas.read_excel(Location, sheetname = 'RR death by breastfeeding', index_col = [0, 1])
    RRdeathBreastfeeding = {}
    for ageName in ages:
        RRdeathBreastfeeding[ageName] = {}
        for cause in causesOfDeath:
            RRdeathBreastfeeding[ageName][cause] = {}
            for breastfeedingCat in breastfeedingList:
                if cause in listCausesRRdeathBreastfeeding: #if no RR given for this cause then set to 1
                    RRdeathBreastfeeding[ageName][cause][breastfeedingCat] = df.loc[cause][ageName][breastfeedingCat]
                else:
                    RRdeathBreastfeeding[ageName][cause][breastfeedingCat] = 1

    #  READ RR Death by Birth Outcome SHEET
    #  sets:
    #  - RRdeathByBirthOutcome
    df = pandas.read_excel(Location, sheetname = 'RR death by birth outcome')
    #get list of causesOfDeath
    causesListedHere = list(df['Cause'])
    #get the nested list of causeOfDeathDist
    df = pandas.read_excel(Location, sheetname = 'RR death by birth outcome', index_col = 'Cause')
    RRdeathByBirthOutcome = {}
    for cause in causesOfDeath:
        RRdeathByBirthOutcome[cause] = {}
        if cause in causesListedHere:
            for birthoutcome in birthOutcomes:
                RRdeathByBirthOutcome[cause][birthoutcome] = df.loc[cause, birthoutcome]
        else:
            for birthoutcome in birthOutcomes:
                RRdeathByBirthOutcome[cause][birthoutcome] = 1.

    #  READ RR Death by Anemia
    #  sets:
    #  - RRdeathByAnemia
    df = pandas.read_excel(Location, sheetname = 'RR death by anemia', index_col = [0])
    # get list of causes for which we have relative risks
    mylist = list(df.index.values)
    myset = set(mylist)
    listCausesRRdeathAnemia = list(myset)
    # put the RR into RRdeathAnemia
    df = pandas.read_excel(Location, sheetname = 'RR death by anemia', index_col = [0, 1])
    RRdeathAnemia = {}
    for ageName in allPops:
        RRdeathAnemia[ageName] = {}
        for cause in causesOfDeath:
            RRdeathAnemia[ageName][cause] = {}
            for anemiaStatus in anemiaList:
                if cause in listCausesRRdeathAnemia: #if no RR given for this cause then set to 1
                    RRdeathAnemia[ageName][cause][anemiaStatus] = df.loc[cause][ageName][anemiaStatus]
                else:
                    RRdeathAnemia[ageName][cause][anemiaStatus] = 1

    #  READ distributions SHEET
    #  sets:
    #  - stuntingDistribution
    #  - wastingDistribution
    #  - breastfeedingDistribution
    df = pandas.read_excel(Location, sheetname = 'distributions', index_col = [0, 1])
    stuntingDistribution = {}
    wastingDistribution = {}
    breastfeedingDistribution = {}
    #stunting
    for ageName in ages:
        stuntingDistribution[ageName] = {}
        for status in stuntingList:
            stuntingDistribution[ageName][status] = df.loc['Stunting'][ageName][status] / 100.
    #wasting
    for ageName in ages:
        wastingDistribution[ageName] = {}
        for status in wastingList:
            wastingDistribution[ageName][status] = df.loc['Wasting'][ageName][status] / 100.
    #breastfeeding
    for ageName in ages:
        breastfeedingDistribution[ageName] = {}
        for status in breastfeedingList:
            breastfeedingDistribution[ageName][status] = df.loc['Breastfeeding'][ageName][status] / 100.

    #  READ ANEMIA PREVALENCE SHEET
    #  sets:
    #  - anemiaDistribution
    df = pandas.read_excel(Location, sheetname = 'anemia prevalence', index_col = [0, 1])
    anemiaDistribution = {}
    for ageName in allPops + ['general population']:
        anemiaDistribution[ageName] = {}
        for status in anemiaList:
            anemiaDistribution[ageName][status] = df.loc['Anemia'][ageName][status] / 100.

    #  READ OR stunting progression SHEET
    #  sets:
    #  - ORstuntingProgression
    df = pandas.read_excel(Location, sheetname = 'OR stunting progression')
    ORstuntingProgression = dict(zip(list(df.columns.values), df.iloc[0]))

    # READ Incidence of conditions SHEET
    # sets:
    # - incidences
    df = pandas.read_excel(Location, sheetname = 'Incidence of conditions', index_col = 'Condition')
    incidences = {}
    for ageName in ages:
        incidences[ageName] = {}
        for condition in conditions:
            incidences[ageName][condition] = df.loc[condition, ageName] / 12. #WARNING HACK should multiply by timestep within code

    # READ RR diarrhea SHEET
    # sets:
    # - RRdiarrhea
    df = pandas.read_excel(Location, sheetname = 'RR diarrhoea', index_col = [0])
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
                  
