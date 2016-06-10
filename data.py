# -*- coding: utf-8 -*-
"""
Created on Fri Feb 26 15:57:07 2016

@author: ruth
"""

class Data:
    def __init__(self, ages, causesOfDeath, conditions, interventionList, demographics, projectedBirths, totalMortality, causeOfDeathDist, RRStunting, RRWasting, RRBreastfeeding, RRdeathByBirthOutcome, stuntingDistribution, wastingDistribution, breastfeedingDistribution, incidences, RRdiarrhea, ORstuntingCondition, birthOutcomeDist, ORstuntingProgression, ORstuntingBirthOutcome, ORstuntingIntervention, ORappropriatebfIntervention, ageAppropriateBreastfeeding, interventionCoveragesCurrent, interventionCostCoverage, interventionTargetPop, interventionAffectedFraction, interventionMortalityEffectiveness, interventionIncidenceEffectiveness, interventionsMaternal, complementsList, ORstuntingComplementaryFeeding):
        self.ages = ages
        self.causesOfDeath = causesOfDeath
        self.conditions = conditions
        self.interventionList = interventionList
        self.demographics = demographics
        self.projectedBirths = projectedBirths
        self.totalMortality = totalMortality
        self.causeOfDeathDist = causeOfDeathDist
        self.stuntingDistribution = stuntingDistribution
        self.wastingDistribution = wastingDistribution
        self.breastfeedingDistribution = breastfeedingDistribution
        self.RRStunting = RRStunting
        self.RRWasting = RRWasting
        self.RRBreastfeeding = RRBreastfeeding
        self.RRdeathByBirthOutcome = RRdeathByBirthOutcome
        self.ORstuntingProgression = ORstuntingProgression
        self.incidences = incidences
        self.RRdiarrhea = RRdiarrhea
        self.ORstuntingCondition = ORstuntingCondition
        #self.birthCircumstanceDist = birthCircumstanceDist
        #self.timeBetweenBirthsDist = timeBetweenBirthsDist
        #self.RRbirthOutcomeByAgeAndOrder = RRbirthOutcomeByAgeAndOrder
        #self.RRbirthOutcomeByTime = RRbirthOutcomeByTime
        self.ORstuntingBirthOutcome = ORstuntingBirthOutcome
        self.birthOutcomeDist = birthOutcomeDist
        self.ORstuntingIntervention = ORstuntingIntervention
        self.ORappropriatebfIntervention = ORappropriatebfIntervention
        self.ageAppropriateBreastfeeding = ageAppropriateBreastfeeding
        self.interventionCoveragesCurrent = interventionCoveragesCurrent
        self.interventionCostCoverage = interventionCostCoverage
        self.interventionTargetPop = interventionTargetPop
        self.interventionAffectedFraction = interventionAffectedFraction
        self.interventionMortalityEffectiveness = interventionMortalityEffectiveness
        self.interventionIncidenceEffectiveness = interventionIncidenceEffectiveness
        self.interventionsMaternal = interventionsMaternal
        self.complementsList = complementsList
        self.ORstuntingComplementaryFeeding = ORstuntingComplementaryFeeding
    

    
def getDataFromSpreadsheet(fileName, keyList):
    
    import pandas
    Location = fileName
    [ages, birthOutcomes, stuntingList, wastingList, breastfeedingList] = keyList
    
    
    # GET ALL LISTS

    #get list of ages and causesOfDeath
    df = pandas.read_excel(Location, sheetname = 'mortality')
    causesOfDeath = list(df['Cause'])

    #get list of interventions
    df = pandas.read_excel(Location, sheetname = 'Interventions coverages')
    interventionList = list(df['Intervention'])

    #get list of projection years
    df = pandas.read_excel(Location, sheetname = 'projected births')
    projectionYearList = list(df['year'])

    allPops = ages[:]
    allPops.append('pregnant women')
    

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


    #  READ TOTAL MORTALITY SHEET
    #  gets you:
    #  - totalMortality

    df = pandas.read_excel(Location, sheetname = 'total mortality')
    totalMortality = dict(zip(list(df.columns.values), df.iloc[0]))


    #  READ MORTALITY SHEET
    #  gets you:
    #  - ages
    #  - causesOfDeath
    #  - causeOfDeathByAge

    #get the nested list of causeOfDeathDist
    df = pandas.read_excel(Location, sheetname = 'mortality', index_col = 'Cause')
    causeOfDeathDist = {}
    for age in ages:
        causeOfDeathDist[age] = {}
        for cause in causesOfDeath:
            causeOfDeathDist[age][cause] = df.loc[cause, age]

            
    #  READ RRStunting SHEET
    #  gets you:
    #  - RRStunting
    
    #get the list of causes for which we have relative risks
    df = pandas.read_excel(Location, sheetname = 'RRStunting', index_col = [0])
    mylist = list(df.index.values)
    myset = set(mylist)
    listCausesRRStunting = list(myset)
    #put the RR into RRStunting
    df = pandas.read_excel(Location, sheetname = 'RRStunting', index_col = [0, 1])
    
    RRStunting = {}
    for age in ages:
        RRStunting[age] = {}
        for cause in causesOfDeath:
            RRStunting[age][cause] = {}
            for stuntingCat in stuntingList:
                if cause in listCausesRRStunting: #if no RR given for this cause then set to 1
                    RRStunting[age][cause][stuntingCat] = df.loc[cause][age][stuntingCat]
                else:
                    RRStunting[age][cause][stuntingCat] = 1
                   
            
    #  READ RRWasting SHEET
    #  gets you:
    #  - RRWasting
    
    #get the list of causes for which we have relative risks
    df = pandas.read_excel(Location, sheetname = 'RRWasting', index_col = [0])
    mylist = list(df.index.values)
    myset = set(mylist)
    listCausesRRWasting = list(myset)
    #put the RR into RRWasting
    df = pandas.read_excel(Location, sheetname = 'RRWasting', index_col = [0, 1])
    
    RRWasting = {}
    for age in ages:
        RRWasting[age] = {}
        for cause in causesOfDeath:
            RRWasting[age][cause] = {}
            for wastingCat in wastingList:
                if cause in listCausesRRWasting: #if no RR given for this cause then set to 1
                    RRWasting[age][cause][wastingCat] = df.loc[cause][age][wastingCat]
                else:
                    RRWasting[age][cause][wastingCat] = 1        


    #  READ RRBreastfeeding SHEET
    #  gets you:
    #  - RRBreastfeeding
    
    #get the list of causes for which we have relative risks
    df = pandas.read_excel(Location, sheetname = 'RRBreastfeeding', index_col = [0])
    mylist = list(df.index.values)
    myset = set(mylist)
    listCausesRRBreastfeeding = list(myset)
    #put the RR into RRBreastfeeding
    df = pandas.read_excel(Location, sheetname = 'RRBreastfeeding', index_col = [0, 1])
    
    RRBreastfeeding = {}
    for age in ages:
        RRBreastfeeding[age] = {}
        for cause in causesOfDeath: 
            RRBreastfeeding[age][cause] = {}
            for breastfeedingCat in breastfeedingList:
                if cause in listCausesRRBreastfeeding: #if no RR given for this cause then set to 1
                    RRBreastfeeding[age][cause][breastfeedingCat] = df.loc[cause][age][breastfeedingCat]
                else:
                    RRBreastfeeding[age][cause][breastfeedingCat] = 1  

        
    #  READ RR Death by Birth Outcome SHEET
    #  gets you:
    #  - RRdeathByBirthOutcome

    #get list of causesOfDeath
    df = pandas.read_excel(Location, sheetname = 'RR Death by Birth Outcome')
    causesListedHere = list(df['Cause'])
    #get the nested list of causeOfDeathDist
    df = pandas.read_excel(Location, sheetname = 'RR Death by Birth Outcome', index_col = 'Cause')
    RRdeathByBirthOutcome = {}
    for cause in causesOfDeath:
        RRdeathByBirthOutcome[cause] = {}
        if cause in causesListedHere:
            for birthoutcome in birthOutcomes:
                RRdeathByBirthOutcome[cause][birthoutcome] = df.loc[cause, birthoutcome]
        else:
            for birthoutcome in birthOutcomes:
                RRdeathByBirthOutcome[cause][birthoutcome] = 1.


    #  READ distributions SHEET
    #  gets you:
    #  - stuntingDistribution
    #  - wastingDistribution
    #  - breastfeedingDistribution
    
    df = pandas.read_excel(Location, sheetname = 'distributions', index_col = [0, 1])
    stuntingDistribution = {}
    wastingDistribution = {}
    breastfeedingDistribution = {}
    
    #stunting
    for age in ages:
        stuntingDistribution[age] = {}
        for status in stuntingList:
            stuntingDistribution[age][status] = df.loc['Stunting'][age][status] / 100.
    #wasting        
    for age in ages:
        wastingDistribution[age] = {}
        for status in wastingList:
            wastingDistribution[age][status] = df.loc['Wasting'][age][status] / 100.
    #breastfeeding  
    for age in ages:
        breastfeedingDistribution[age] = {}
        for status in breastfeedingList:
            breastfeedingDistribution[age][status] = df.loc['Breastfeeding'][age][status] / 100.
            
    
    """
    #  READ birth distribution SHEET
    #  gets you:
    #  - birthCircumstanceDist
    df = pandas.read_excel(Location, sheetname = 'birth distribution')
    motherAges = list(df.columns.values)[1:]
    birthTypes = list(df['Type'])
    
    df = pandas.read_excel(Location, sheetname = 'birth distribution', index_col = [0])
    birthCircumstanceDist = {}
    for maternalAge in motherAges:
        birthCircumstanceDist[maternalAge] = {}
        for status in birthTypes:
            birthCircumstanceDist[maternalAge][status] = df[maternalAge][status]
    
    #  READ time between births SHEET
    #  gets you:
    #  - timeBetweenBirthsDist
    df = pandas.read_excel(Location, sheetname = 'time between births')
    timeBetweenBirthsDist = dict(zip(list(df.columns.values), df.iloc[0]))
    

    #  READ RR birth by type SHEET
    #  gets you:
    #  - RRbirthOutcomeByAgeAndOrder
    
    #get the list of outcomes for which we have relative risks
    df = pandas.read_excel(Location, sheetname = 'RR birth by type', index_col = [0])
    mylist = list(df.index.values)
    myset = set(mylist)
    listOfOutcomes = list(myset)
    
    #put the RR into RRbirthOutcomeByAgeAndOrder
    df = pandas.read_excel(Location, sheetname = 'RR birth by type', index_col = [0, 1])
    
    RRbirthOutcomeByAgeAndOrder = {}
    for outcome in listOfOutcomes:
        RRbirthOutcomeByAgeAndOrder[outcome] = {}
        for age in motherAges:
            RRbirthOutcomeByAgeAndOrder[outcome][age] = {}
            for status in ['first', 'second or third', 'greater than third']:    
                RRbirthOutcomeByAgeAndOrder[outcome][age][status] = df.loc[outcome][age][status]

                
    #  READ RR birth by time SHEET
    #  gets you:
    #  - RRbirthOutcomeByTime
    df = pandas.read_excel(Location, sheetname = 'RR birth by time')
    birthLag = list(df.columns.values)[1:]
    
    df = pandas.read_excel(Location, sheetname = 'RR birth by time', index_col = [0])
    RRbirthOutcomeByTime = {}
    for outcome in listOfOutcomes:
        RRbirthOutcomeByTime[outcome] = {}
        for time in birthLag:
            RRbirthOutcomeByTime[outcome][time] = df[time][outcome]           
    """


    #  READ OR stunting progression SHEET
    #  gets you:
    #  - ORstuntingProgression
    df = pandas.read_excel(Location, sheetname = 'OR stunting progression')
    ORstuntingProgression = dict(zip(list(df.columns.values), df.iloc[0]))    


    # READ Incidence of conditions SHEET
    # gets you:
    # - incidences
    df = pandas.read_excel(Location, sheetname = 'Incidence of conditions')
    conditions = list(df['Condition'])
    df = pandas.read_excel(Location, sheetname = 'Incidence of conditions', index_col = 'Condition')
    incidences = {}
    for age in ages:
        incidences[age] = {}
        for condition in conditions:
            incidences[age][condition] = df.loc[condition, age]


    # READ RR diarrhea SHEET
    # gets you:
    # - RRdiarrhea
    df = pandas.read_excel(Location, sheetname = 'RR diarrhoea', index_col = [0])
    RRdiarrhea = {}
    for age in ages:
        RRdiarrhea[age] = {}
        for breastfeedingCat in breastfeedingList:
            RRdiarrhea[age][breastfeedingCat] = df[age][breastfeedingCat]       

    # READ OR Diarrhea SHEET
    # gets you:
    # - ORstuntingCondition
    df = pandas.read_excel(Location, sheetname = 'OR stunting by condition')
    conditionsHere = list(df['Condition'])
    df = pandas.read_excel(Location, sheetname = 'OR stunting by condition', index_col = 'Condition')
    ORstuntingCondition = {}
    for age in ages:
        ORstuntingCondition[age] = {}
        for condition in conditions:
            ORstuntingCondition[age][condition] = 1.
        for condition in conditionsHere:
            ORstuntingCondition[age][condition] = df.loc[condition, age]
    #ORstuntingCondition = dict(zip(list(df.columns.values), df.iloc[0]))    


    # READ OR Stunting given Intervention Coverage SHEET
    # gets you:
    # - ORstuntingIntervention
    df = pandas.read_excel(Location, sheetname = 'OR stunting by intervention')
    interventionsHere = list(df['Intervention'])
    df = pandas.read_excel(Location, sheetname = 'OR stunting by intervention', index_col = 'Intervention')
    ORstuntingIntervention = {}
    for age in ages:
        ORstuntingIntervention[age] = {}
        for intervention in interventionList:
            ORstuntingIntervention[age][intervention] = 1.
        for intervention in interventionsHere:
            ORstuntingIntervention[age][intervention] = df.loc[intervention, age]


    # READ OR Appropriate Breastfeeding given OR Appropriate Breastfeeding SHEET
    # gets you:
    # - ORappropriatebfIntervention
    df = pandas.read_excel(Location, sheetname = 'OR appropriateBF by interv')
    interventionsHere = list(df['Intervention'])
    df = pandas.read_excel(Location, sheetname = 'OR appropriateBF by interv', index_col = 'Intervention')
    ORappropriatebfIntervention = {}
    for age in ages:
        ORappropriatebfIntervention[age] = {}
        for intervention in interventionList:
            ORappropriatebfIntervention[age][intervention] = 1.
        for intervention in interventionsHere:
            ORappropriatebfIntervention[age][intervention] = df.loc[intervention, age]
            

    #  READ Appropriate Breastfeeding Practice SHEET
    #  gets you:
    #  - ageAppropriateBreastfeeding
    df = pandas.read_excel(Location, sheetname = 'Appropriate breastfeeding')
    ageAppropriateBreastfeeding = dict(zip(list(df.columns.values), df.iloc[0]))    



    #  READ birth outcome distribution SHEET
    #  gets you:
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
    #  gets you:
    #  - ORstuntingBirthOutcome
    df = pandas.read_excel(Location, sheetname = 'OR stunting by birth outcome')
    ORstuntingBirthOutcome = dict(zip(list(df.columns.values), df.iloc[0]))   



    #  READ Current Intervention Coverages SHEET
    #  gets you:
    #  - InterventionCoveragesCurrent
    #  - InterventionCostCoverage

    #get the nested list of causeOfDeathDist
    df = pandas.read_excel(Location, sheetname = 'Interventions coverages', index_col = 'Intervention')
    interventionCoveragesCurrent = {}
    interventionCostCoverage = {}
    costinfoList = ["unit cost","saturation coverage"]
    for intervention in interventionList:
        interventionCoveragesCurrent[intervention] = df.loc[intervention, "baseline coverage"]
        interventionCostCoverage[intervention] = {}
        for costinfo in costinfoList:
            interventionCostCoverage[intervention][costinfo] = df.loc[intervention, costinfo]
        

    # READ Intervention Target Population Matrix SHEET
    # gets you:
    # - interventionTargetPop
    df = pandas.read_excel(Location, sheetname = 'Interventions target population', index_col = 'Intervention')
    interventionTargetPop = {}
    for intervention in interventionList:
        interventionTargetPop[intervention] = {}
        for pop in allPops:
            interventionTargetPop[intervention][pop] = df.loc[intervention, pop]

    
    # READ Interventions maternal SHEET
    # gets you:
    # - interventionsMaternal
    #get the list of interventions
    df = pandas.read_excel(Location, sheetname = 'Interventions maternal', index_col = [0]) 
    mylist = list(df.index.values)
    myset = set(mylist)
    interventionsHere = list(myset)
    #do the rest
    df = pandas.read_excel(Location, sheetname = 'Interventions maternal', index_col = [0, 1]) 
    interventionsMaternal = {}
    # initialise
    for intervention in interventionList:
        interventionsMaternal[intervention] = {}
        for outcome in birthOutcomes:
            interventionsMaternal[intervention][outcome] = {}
            for value in ['effectiveness', 'affected fraction']:
                interventionsMaternal[intervention][outcome][value] = 0.
    # complete # WARNING allowing for all causes of death, but completing according to condition
    for intervention in interventionsHere:
        for outcome in birthOutcomes:
            for value in ['effectiveness', 'affected fraction']:
                interventionsMaternal[intervention][outcome][value] = df.loc[intervention][outcome][value]



    # READ Interventions affected fraction SHEET
    # gets you:
    # - interventionAffectedFraction
    #get the list of interventions
    df = pandas.read_excel(Location, sheetname = 'Interventions affected fraction', index_col = [0])
    mylist = list(df.index.values)
    myset = set(mylist)
    interventionsHere = list(myset)
    #do the rest
    df = pandas.read_excel(Location, sheetname = 'Interventions affected fraction', index_col = [0, 1])
    interventionAffectedFraction = {}
    # initialise
    for intervention in interventionList:
        interventionAffectedFraction[intervention] = {}
        for age in ages:
            interventionAffectedFraction[intervention][age] = {}
            for cause in causesOfDeath:
                interventionAffectedFraction[intervention][age][cause] = 0.
    # complete # WARNING allowing for all causes of death, but completing according to condition
    for intervention in interventionsHere:
        for age in ages:
            conditionsHere = df.loc[intervention][age].keys()
            for condition in conditionsHere:    
                interventionAffectedFraction[intervention][age][condition] = df.loc[intervention][age][condition]

                
    # READ Interventions mortality effectiveness SHEET
    # gets you:
    # - interventionMortalityEffectiveness
    #get the list of interventions
    df = pandas.read_excel(Location, sheetname = 'Interventions mortality eff', index_col = [0])
    mylist = list(df.index.values)
    myset = set(mylist)
    interventionsHere = list(myset)
    #do the rest
    df = pandas.read_excel(Location, sheetname = 'Interventions mortality eff', index_col = [0, 1])
    interventionMortalityEffectiveness = {}
    # initialise
    for intervention in interventionList:
        interventionMortalityEffectiveness[intervention] = {}
        for age in ages:
            interventionMortalityEffectiveness[intervention][age] = {}
            for cause in causesOfDeath:
                interventionMortalityEffectiveness[intervention][age][cause] = 0.
    # complete
    for intervention in interventionsHere:
        for age in ages:
            causesHere = df.loc[intervention][age].keys()
            for cause in causesHere:    
                interventionMortalityEffectiveness[intervention][age][cause] = df.loc[intervention][age][cause]


    # READ Interventions incidence effectiveness SHEET
    # gets you:
    # - interventionIncidenceEffectiveness
    #get the list of interventions
    df = pandas.read_excel(Location, sheetname = 'Interventions incidence eff', index_col = [0])
    mylist = list(df.index.values)
    myset = set(mylist)
    interventionsHere = list(myset)
    #do the rest
    df = pandas.read_excel(Location, sheetname = 'Interventions incidence eff', index_col = [0, 1])
    interventionIncidenceEffectiveness = {}
    # initialise
    for intervention in interventionList:
        interventionIncidenceEffectiveness[intervention] = {}
        for age in ages:
            interventionIncidenceEffectiveness[intervention][age] = {}
            for condition in conditions:
                interventionIncidenceEffectiveness[intervention][age][condition] = 0.
    # complete
    for intervention in interventionsHere:
        for age in ages:
            conditionsHere = df.loc[intervention][age].keys()
            for condition in conditionsHere:    
                interventionIncidenceEffectiveness[intervention][age][condition] = df.loc[intervention][age][condition]



    # READ OR stunting for complements SHEET
    # gets you:
    # - ORstuntingComplementaryFeeding
    df = pandas.read_excel(Location, sheetname = 'OR stunting for complements') 
    complementsList = list(df['Complements group'])
    df = pandas.read_excel(Location, sheetname = 'OR stunting for complements', index_col = 'Complements group') 
    ORstuntingComplementaryFeeding = {}
    for age in ages:
        ORstuntingComplementaryFeeding[age] = {}
        for group in complementsList:
            ORstuntingComplementaryFeeding[age][group] = df.loc[group, age]    
    
            
    spreadsheetData = Data(ages, causesOfDeath, conditions, interventionList, demographics, projectedBirths, totalMortality, causeOfDeathDist, RRStunting, RRWasting, RRBreastfeeding, RRdeathByBirthOutcome, stuntingDistribution, wastingDistribution, breastfeedingDistribution, incidences, RRdiarrhea, ORstuntingCondition, birthOutcomeDist, ORstuntingProgression, ORstuntingBirthOutcome, ORstuntingIntervention, ORappropriatebfIntervention, ageAppropriateBreastfeeding, interventionCoveragesCurrent, interventionCostCoverage, interventionTargetPop, interventionAffectedFraction, interventionMortalityEffectiveness, interventionIncidenceEffectiveness, interventionsMaternal, complementsList, ORstuntingComplementaryFeeding)

    return spreadsheetData        
                  
