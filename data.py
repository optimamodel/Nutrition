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
                 effectivenessIncidence, interventionsBirthOutcome, foodSecurityGroups,
                 ORstuntingComplementaryFeeding, anemiaDistribution,
                 projectedWRApop, projectedWRApopByAge, projectedPWpop,
                 projectedGeneralPop, PWageDistribution, fracAnemicNotPoor,
                 fracAnemicPoor, fracAnemicExposedMalaria, fracExposedMalaria, ORanemiaCondition, fracSevereDia):

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
        self.projectedGeneralPop = projectedGeneralPop
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
            newAgeGroups = {age:subDict for age in listOfAgeGroups}
            dictToUpdate[key].update(newAgeGroups)
    return dictToUpdate

def readSpreadsheet(fileName, keyList):
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

    ### INTERVENTIONS COST AND COVERAGE
    interventionsSheet = pd.read_excel(location, sheetname = 'Interventions cost and coverage', index_col=0)
    interventionList = list(interventionsSheet.index)
    interventionCompleteList =  dcp(interventionList)
    for intervention in interventionList:
        if "IFAS" and "malaria" in intervention:
            interventionCompleteList.append(intervention + " with bed nets")
    coverage = dict(interventionsSheet["Baseline coverage"])
    costSaturation = interventionsSheet[["Saturation coverage", "Unit cost"]].to_dict(orient='index')
    # add hidden intervention data to coverage and cost saturation
    hiddenInterventionList = list(set(interventionCompleteList) - set(interventionList))
    for intervention in hiddenInterventionList:
        correspondingIntervention = intervention.strip(" with bed nets")
        thisCoverage = coverage[correspondingIntervention]
        coverage.update({intervention : thisCoverage})
        thisCostSaturation = costSaturation[correspondingIntervention]
        costSaturation.update({intervention : thisCostSaturation})
    


    ### BASELINE YEAR DEMOGRAPHICS
    demographicsSheet = pd.read_excel(location, sheetname='Baseline year demographics', index_col=[0, 1])
    demographicsSheet = demographicsSheet.dropna(how='all')
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
            anemiaPrevalence[colName][ageName]['not anemic'] = 1. - anemiaPrevalence[colName][ageName]['All anemia']
    # convert age groups to those used in model
    mappingDict = {"Children": ages, "WRA not pregnant": WRAages, "Pregnant women": PWages}
    anemiaDistribution = mapAgeKeys(anemiaPrevalence, mappingDict)
    #rename
    for ageName in ages + WRAages + PWages:
        anemiaThisAge = anemiaDistribution[ageName]
        anemiaThisAge['anemic'] = anemiaThisAge.pop('All anemia')
    print "::WARNING:: fictional anemia distribution for <1 month & 1-5 months age groups"
    # TODO: These are fake values b/c spredsheet has blank
    anemiaDistribution["<1 month"]['anemic'] = .1
    anemiaDistribution["<1 month"]['not anemic'] = .9
    anemiaDistribution["1-5 months"]['anemic'] = .1
    anemiaDistribution["1-5 months"]['not anemic'] = .9

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
    RRdeathByBirthOutcome = splitSpreadsheetWithTwoIndexCols(birthOutcomesSheet, "RR of death", rowList=causesOfDeathList, switchKeys=True)

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
    # women of reproductive age, assume no direct impact of interventions (RR=1). Also no data on children (RR=1)
    RRdeathChildrenWRanemia = {age: {cause: {status: 1. for status in anemiaList} for cause in causesOfDeathList} for age in WRAages + ages}
    # combine all groups into single dictionary
    RRdeathMaternalAnemia.update(RRdeathChildrenWRanemia)
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
    ORstuntingDia = dict(ORsheet.loc['OR stunting progression and condition','Diarrhea'])
    ORstuntingCondition = {age:{condition: ORstuntingDia[age] for condition in ['Diarrhea']} for age in ages}
    # by intervention
    ORstuntingIntervention = splitSpreadsheetWithTwoIndexCols(ORsheet, "OR stunting by intervention", rowList=interventionList)
    ORstuntingComplementaryFeeding = {}
    interventionsHere = ORsheet.loc['OR stunting by intervention'].index
    foodSecurityGroups = []
    for age in ages:
        ORstuntingComplementaryFeeding[age] = {}
        for intervention in interventionsHere:
            if "Complementary" in intervention and 'iron' not in intervention:
                ORstuntingComplementaryFeeding[age][intervention] = ORsheet[age]['OR stunting by intervention'][intervention]
                if intervention not in foodSecurityGroups:
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
    # general pop
    #  NO MORE GENERAL POP!
    targetPopulation.update(splitSpreadsheetWithTwoIndexCols(targetPopSheet, 'General population', switchKeys=True))
    # change PW & WRA to age groups
    targetPopulation = stratifyPopIntoAgeGroups(targetPopulation, interventionList, WRAages, 'Non-pregnant WRA', keyLevel=1)
    targetPopulation = stratifyPopIntoAgeGroups(targetPopulation, interventionList, PWages, 'Pregnant women', keyLevel=1)

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

    ### INTERVENTIONS ANEMIA
    # relative risks
    interventionsAnemiaSheet = pd.read_excel(location, sheetname='Interventions anemia', index_col=[0,1])
    interventionsAnemiaSheet = interventionsAnemiaSheet.dropna(how='all')
    # remove interventions from RR if we have OR
    interventionsOR = list(interventionsAnemiaSheet.loc["Odds Ratios"].index)
    interventionsRR = [intervention for intervention in interventionList if intervention not in interventionsOR]
    RRanemiaIntervention = splitSpreadsheetWithTwoIndexCols(interventionsAnemiaSheet, 'Relative Risks', rowList=interventionsRR)
    # odds ratios
    ORanemiaIntervention = splitSpreadsheetWithTwoIndexCols(interventionsAnemiaSheet, 'Odds Ratios', rowList=interventionsOR)

    # INTERVENTIONS AFFECTED FRACTION AND EFFECTIVENESS
    # children
    # warning: currently this applied to all population groups (no tabs for them yet)
    interventionsForChildren = pd.read_excel(location, sheetname='Interventions for children', index_col=[0, 1, 2])
    affectedFraction = readInterventionsByPopulationTabs(interventionsForChildren, 'Affected fraction', interventionList, allPops, causesOfDeathList + ['Severe diarrhea']) # TODO: warning: severe diarrhea is not listed in 'causes of death' and so causes issues
    effectivenessMortality = readInterventionsByPopulationTabs(interventionsForChildren, 'Effectiveness mortality', interventionList, allPops, causesOfDeathList)
    effectivenessIncidence = readInterventionsByPopulationTabs(interventionsForChildren, 'Effectiveness incidence', interventionList, ages, conditionsList) # children only


    # TODO: not currently available in spreadsheet
    print "::WARNING:: fractions pertaining to anemia/malaria and ORanemiaCondition are fictional."
    fracAnemicNotPoor = {age:0.5 for age in ages + WRAages + PWages}
    fracAnemicPoor = {age:0.5 for age in ages + WRAages + PWages}
    fracAnemicExposedMalaria = {age:0.5 for age in ages + WRAages + PWages}
    fracExposedMalaria = demographics['fraction at risk of malaria']
    ORanemiaCondition = {age:{condition:1. for condition in conditionsList} for age in ages}
    fracSevereDia = 0.2 # made up value

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
                           foodSecurityGroups, ORstuntingComplementaryFeeding, anemiaDistribution,
                           projectedWRApop, projectedWRApopByAge, projectedPWpop, projectedGeneralPop,
                           PWageDistribution, fracAnemicNotPoor, fracAnemicPoor, fracAnemicExposedMalaria,
                           fracExposedMalaria, ORanemiaCondition, fracSevereDia)

    return spreadsheetData
                  
