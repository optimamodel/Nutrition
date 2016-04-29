# -*- coding: utf-8 -*-
"""
Created on Fri Feb 26 15:57:07 2016

@author: ruth
"""

class Data:
    def __init__(self, ages, causesOfDeath, totalMortality, causeOfDeathDist, RRStunting, RRWasting, RRBreastfeeding, RRdeathByBirthOutcome, stuntingDistribution, wastingDistribution, breastfeedingDistribution, incidenceDiarrhea, RRdiarrhea, ORdiarrhea, birthCircumstanceDist, timeBetweenBirthsDist, birthOutcomeDist, RRbirthOutcomeByAgeAndOrder, RRbirthOutcomeByTime, ORstuntingProgression, ORBirthOutcomeStunting, ORstuntingZinc, InterventionCoveragesCurrent):
        self.ages = ages
        self.causesOfDeath = causesOfDeath
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
        self.incidenceDiarrhea = incidenceDiarrhea
        self.RRdiarrhea = RRdiarrhea
        self.ORdiarrhea = ORdiarrhea
        self.birthCircumstanceDist = birthCircumstanceDist
        self.timeBetweenBirthsDist = timeBetweenBirthsDist
        self.birthOutcomeDist = birthOutcomeDist
        self.RRbirthOutcomeByAgeAndOrder = RRbirthOutcomeByAgeAndOrder
        self.RRbirthOutcomeByTime = RRbirthOutcomeByTime
        self.ORBirthOutcomeStunting = ORBirthOutcomeStunting
        self.ORstuntingZinc = ORstuntingZinc
        self.InterventionCoveragesCurrent = InterventionCoveragesCurrent
    

    
def getDataFromSpreadsheet(fileName,keyList):
    
    import pandas
    Location = fileName
    [ages,birthOutcomes,stuntingList,wastingList,breastfeedingList] = keyList
    
    #  READ TOTAL MORTALITY SHEET
    #  gets you:
    #  - totalMortality
    
    df = pandas.read_excel(Location, sheetname = 'total mortality')
    totalMortality = dict(zip(list(df.columns.values), df.iloc[0]/1000.))
    
    #  READ MORTALITY SHEET
    #  gets you:
    #  - ages
    #  - causesOfDeath
    #  - causeOfDeathByAge
    
    #get list of ages and causesOfDeath
    df = pandas.read_excel(Location, sheetname = 'mortality') #read this way for this task
    causesOfDeath = list(df['Cause'])
    #ages = list(df.columns.values)[1:]
    #get the nested list of causeOfDeathDist
    df = pandas.read_excel(Location, sheetname = 'mortality', index_col = 'Cause') #read this way for this task
    causeOfDeathDist = {}
    for age in ages:
        causeOfDeathDist[age] = {}
        for cause in causesOfDeath:
            causeOfDeathDist[age][cause] = df.loc[cause, age]

            
    #  READ RRStunting SHEET
    #  gets you:
    #  - RRStunting
    
    #get the list of causes for which we have relative risks
    df = pandas.read_excel(Location, sheetname = 'RRStunting', index_col = [0]) #read this way for this task
    mylist = list(df.index.values)
    myset = set(mylist)
    listCausesRRStunting = list(myset)
    #put the RR into RRStunting
    df = pandas.read_excel(Location, sheetname = 'RRStunting', index_col = [0, 1]) #read this way for this task
    
    RRStunting = {}
    for age in ages:
        RRStunting[age] = {}
        for cause in causesOfDeath:
            RRStunting[age][cause] = {}
            for stuntingCat in ['normal', 'mild', 'moderate', 'high']:
                if cause in listCausesRRStunting: #if no RR given for this cause then set to 1
                    RRStunting[age][cause][stuntingCat] = df.loc[cause][age][stuntingCat]
                else:
                    RRStunting[age][cause][stuntingCat] = 1
                   
            
    #  READ RRWasting SHEET
    #  gets you:
    #  - RRWasting
    
    #get the list of causes for which we have relative risks
    df = pandas.read_excel(Location, sheetname = 'RRWasting', index_col = [0]) #read this way for this task
    mylist = list(df.index.values)
    myset = set(mylist)
    listCausesRRWasting = list(myset)
    #put the RR into RRWasting
    df = pandas.read_excel(Location, sheetname = 'RRWasting', index_col = [0, 1]) #read this way for this task
    
    RRWasting = {}
    for age in ages:
        RRWasting[age] = {}
        for cause in causesOfDeath:
            RRWasting[age][cause] = {}
            for wastingCat in ['normal', 'mild', 'moderate', 'high']:
                if cause in listCausesRRWasting: #if no RR given for this cause then set to 1
                    RRWasting[age][cause][wastingCat] = df.loc[cause][age][wastingCat]
                else:
                    RRWasting[age][cause][wastingCat] = 1        


    #  READ RRBreastfeeding SHEET
    #  gets you:
    #  - RRBreastfeeding
    
    #get the list of causes for which we have relative risks
    df = pandas.read_excel(Location, sheetname = 'RRBreastfeeding', index_col = [0]) #read this way for this task
    mylist = list(df.index.values)
    myset = set(mylist)
    listCausesRRBreastfeeding = list(myset)
    #put the RR into RRBreastfeeding
    df = pandas.read_excel(Location, sheetname = 'RRBreastfeeding', index_col = [0, 1]) #read this way for this task
    
    RRBreastfeeding = {}
    for age in ages:
        RRBreastfeeding[age] = {}
        for cause in causesOfDeath: 
            RRBreastfeeding[age][cause] = {}
            for breastfeedingCat in ['exclusive', 'predominant', 'partial', 'none']:
                if cause in listCausesRRBreastfeeding: #if no RR given for this cause then set to 1
                    RRBreastfeeding[age][cause][breastfeedingCat] = df.loc[cause][age][breastfeedingCat]
                else:
                    RRBreastfeeding[age][cause][breastfeedingCat] = 1  

        
    #  READ RR Death by Birth Outcome SHEET
    #  gets you:
    #  - RRdeathByBirthOutcome

    #get list of causesOfDeath
    df = pandas.read_excel(Location, sheetname = 'RR Death by Birth Outcome') #read this way for this task
    causesListedHere = list(df['Cause'])
    #get the nested list of causeOfDeathDist
    df = pandas.read_excel(Location, sheetname = 'RR Death by Birth Outcome', index_col = 'Cause') #read this way for this task
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
    
    df = pandas.read_excel(Location, sheetname = 'distributions', index_col = [0, 1]) #read this way for this task
    stuntingDistribution = {}
    wastingDistribution = {}
    breastfeedingDistribution = {}
    
    #stunting
    for age in ages:
        stuntingDistribution[age] = {}
        for status in ['normal', 'mild', 'moderate', 'high']:
            stuntingDistribution[age][status] = df.loc['Stunting'][age][status] / 100.
    #wasting        
    for age in ages:
        wastingDistribution[age] = {}
        for status in ['normal', 'mild', 'moderate', 'high']:
            wastingDistribution[age][status] = df.loc['Wasting'][age][status] / 100.
    #breastfeeding  
    for age in ages:
        breastfeedingDistribution[age] = {}
        for status in ['exclusive', 'predominant', 'partial', 'none']:
            breastfeedingDistribution[age][status] = df.loc['Breastfeeding'][age][status] / 100.
            
    
    #  READ birth distribution SHEET
    #  gets you:
    #  - birthCircumstanceDist
    df = pandas.read_excel(Location, sheetname = 'birth distribution') #read this way for this task
    motherAges = list(df.columns.values)[1:]
    birthTypes = list(df['Type'])
    
    df = pandas.read_excel(Location, sheetname = 'birth distribution', index_col = [0]) #read this way for this task
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
    df = pandas.read_excel(Location, sheetname = 'RR birth by type', index_col = [0]) #read this way for this task
    mylist = list(df.index.values)
    myset = set(mylist)
    listOfOutcomes = list(myset)
    
    #put the RR into RRbirthOutcomeByAgeAndOrder
    df = pandas.read_excel(Location, sheetname = 'RR birth by type', index_col = [0, 1]) #read this way for this task
    
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
    df = pandas.read_excel(Location, sheetname = 'RR birth by time') #read this way for this task
    birthLag = list(df.columns.values)[1:]
    
    df = pandas.read_excel(Location, sheetname = 'RR birth by time', index_col = [0]) #read this way for this task
    RRbirthOutcomeByTime = {}
    for outcome in listOfOutcomes:
        RRbirthOutcomeByTime[outcome] = {}
        for time in birthLag:
            RRbirthOutcomeByTime[outcome][time] = df[time][outcome]           
            

    #  READ OR stunting progression SHEET
    #  gets you:
    #  - ORstuntingProgression
    df = pandas.read_excel(Location, sheetname = 'OR stunting progression')
    ORstuntingProgression = dict(zip(list(df.columns.values), df.iloc[0]))    

    # READ Incidence Diarrhea SHEET
    # gets you:
    # - incidenceDiarrhea
    df = pandas.read_excel(Location, sheetname = 'Incidence diarrhoea')
    incidenceDiarrhea = dict(zip(list(df.columns.values), df.iloc[0]))    

    # READ RR diarrhea SHEET
    # gets you:
    # - RRdiarrhea
    df = pandas.read_excel(Location, sheetname = 'RR diarrhoea', index_col = [0]) #read this way for this task
    RRdiarrhea = {}
    for age in ages:
        RRdiarrhea[age] = {}
        for breastfeedingCat in ['exclusive', 'predominant', 'partial', 'none']:
            RRdiarrhea[age][breastfeedingCat] = df[age][breastfeedingCat]       

    # READ OR Diarrhea SHEET
    # gets you:
    # - ORdiarrhea
    df = pandas.read_excel(Location, sheetname = 'OR stunting diarrhoea')
    ORdiarrhea = dict(zip(list(df.columns.values), df.iloc[0]))    


    # READ OR Stunting given Zinc SHEET
    # gets you:
    # - ORstuntingZinc
    df = pandas.read_excel(Location, sheetname = 'OR stunting Zinc')
    ORstuntingZinc = dict(zip(list(df.columns.values), df.iloc[0]))    


    #  READ birth outcome distribution SHEET
    #  gets you:
    #  - birthOutcomeDist (partial)
    df = pandas.read_excel(Location, sheetname = 'birth outcome distribution')
    birthOutcomeDist_partial = dict(zip(list(df.columns.values), df.iloc[0]))    
    # construct full birthOutcome distribution
    birthOutcomeDist = {}
    BOsum = 0.
    for birthOutcome in ["Pre-term SGA","Pre-term AGA","Term SGA"]:
        birthOutcomeDist[birthOutcome] = birthOutcomeDist_partial[birthOutcome]
        BOsum += birthOutcomeDist[birthOutcome]
    birthOutcomeDist["Term AGA"] = 1. - BOsum

      
    #  READ OR birth outcome stunting SHEET
    #  gets you:
    #  - ORBirthOutcomeStunting
    df = pandas.read_excel(Location, sheetname = 'OR birth outcome stunting')
    ORBirthOutcomeStunting = dict(zip(list(df.columns.values), df.iloc[0]))   



    #  READ Intervention Coverages SHEET
    #  gets you:
    #  - InterventionCoveragesCurrent

    #get list of causesOfDeath
    df = pandas.read_excel(Location, sheetname = 'Intervention coverages') #read this way for this task
    InterventionList = list(df['Intervention'])
    #get the nested list of causeOfDeathDist
    df = pandas.read_excel(Location, sheetname = 'Intervention coverages', index_col = 'Intervention') #read this way for this task
    InterventionCoveragesCurrent = {}
    for intervention in InterventionList:
        InterventionCoveragesCurrent[intervention] = df.loc[intervention, "pre-2016"]



            
    spreadsheetData = Data(ages, causesOfDeath, totalMortality, causeOfDeathDist, RRStunting, RRWasting, RRBreastfeeding, RRdeathByBirthOutcome, stuntingDistribution, wastingDistribution, breastfeedingDistribution, incidenceDiarrhea, RRdiarrhea, ORdiarrhea, birthCircumstanceDist, timeBetweenBirthsDist, birthOutcomeDist, RRbirthOutcomeByAgeAndOrder, RRbirthOutcomeByTime, ORstuntingProgression, ORBirthOutcomeStunting, ORstuntingZinc, InterventionCoveragesCurrent)

    return spreadsheetData        
                  
