
# coding: utf-8

# In[198]:

import pandas
import numpy
Location = r'InputForCode.xlsx'


# In[199]:

#  READ TOTAL MORTALITY SHEET
#  gets you:
#  - totalMortalityByAge

df = pandas.read_excel(Location, sheetname = 'total mortality')
totalMortalityByAge = list(df.iloc[0])


# In[200]:

#  READ MORTALITY SHEET
#  gets you:
#  - ages
#  - causesOfDeath
#  - casueOfDeathByAge

#get list of ages and causesOfDeath
df = pandas.read_excel(Location, sheetname = 'mortality') #read this way for this task
causesOfDeath = list(df['Cause'])
ages = list(df.columns.values)[1:]
#get the nested list of causeOfDeathByAge
df = pandas.read_excel(Location, sheetname = 'mortality', index_col = 'Cause') #read this way for this task
causeOfDeathByAge = {}
for cause in causesOfDeath:
    causeOfDeathByAge[cause] = {}
    for age in ages:
        causeOfDeathByAge[cause][age] = df.loc[cause, age]


# In[201]:

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
for cause in causesOfDeath:
    RRStunting[cause] = {}
    for stuntingStatus in ['normal', 'mild', 'moderate', 'high']:
        RRStunting[cause][stuntingStatus] = {}
        for age in ages:
            if cause in listCausesRRStunting: #if no RR given for this cause then set to 1
                RRStunting[cause][stuntingStatus][age] = df.loc[cause][age][stuntingStatus]
            else:
                RRStunting[cause][stuntingStatus][age] = 1


# In[202]:

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
for cause in causesOfDeath:
    RRWasting[cause] = {}
    for wastingStatus in ['normal', 'mild', 'moderate', 'high']:
        RRWasting[cause][wastingStatus] = {}
        for age in ages:
            if cause in listCausesRRWasting: #if no RR given for this cause then set to 1
                RRWasting[cause][wastingStatus][age] = df.loc[cause][age][wastingStatus]
            else:
                RRWasting[cause][wastingStatus][age] = 1


# In[203]:

#  READ RRBreastFeeding SHEET
#  gets you:
#  - RRBreastFeeding

#get the list of causes for which we have relative risks
df = pandas.read_excel(Location, sheetname = 'RRBreastFeeding', index_col = [0]) #read this way for this task
mylist = list(df.index.values)
myset = set(mylist)
listCausesRRBreastFeeding = list(myset)
#put the RR into RRBreastFeeding
df = pandas.read_excel(Location, sheetname = 'RRBreastFeeding', index_col = [0, 1]) #read this way for this task

RRBreastFeeding = {}
for cause in causesOfDeath:
    RRBreastFeeding[cause] = {}
    for breastFeedingStatus in ['exclusive', 'predominant', 'partial', 'none']:
        RRBreastFeeding[cause][breastFeedingStatus] = {}
        for age in ages:
            if cause in listCausesRRBreastFeeding: #if no RR given for this cause then set to 1
                RRBreastFeeding[cause][breastFeedingStatus][age] = df.loc[cause][age][breastFeedingStatus]
            else:
                RRBreastFeeding[cause][breastFeedingStatus][age] = 1


# In[204]:

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
for status in ['normal', 'mild', 'moderate', 'high']:
    stuntingDistribution[status] = {}
    for age in ages:
        stuntingDistribution[status][age] = df.loc['Stunting'][age][status]
#wasting        
for status in ['normal', 'mild', 'moderate', 'high']:
    wastingDistribution[status] = {}
    for age in ages:
        wastingDistribution[status][age] = df.loc['Wasting'][age][status]        
#breast feeding       
for status in ['exclusive', 'predominant', 'partial', 'none']:
    breastfeedingDistribution[status] = {}
    for age in ages:
        breastfeedingDistribution[status][age] = df.loc['Breast Feeding'][age][status]
              
        


# In[221]:

#  READ birth distribution SHEET
#  gets you:
#  - birthCircumstanceDist

df = pandas.read_excel(Location, sheetname = 'birth distribution') #read this way for this task
motherAges = list(df.columns.values)[1:]
birthTypes = list(df['Type'])

df = pandas.read_excel(Location, sheetname = 'birth distribution', index_col = [0]) #read this way for this task
birthCircumstanceDist = {}
for age in motherAges:
    birthCircumstanceDist[age] = {}
    for status in birthTypes:
        birthCircumstanceDist[age][status] = df[age][status]


# In[245]:

#  READ time between births SHEET
#  gets you:
#  - timeBetweenBirthsDist

df = pandas.read_excel(Location, sheetname = 'time between births')
timeBetweenBirthsDist = dict(zip(list(df.columns.values), df.iloc[0]))


# In[267]:

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


# In[283]:

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


# In[286]:

#  READ OR stunting progression SHEET
#  gets you:
#  - ORstuntingProgression

df = pandas.read_excel(Location, sheetname = 'OR stunting progression')
ORstuntingProgression = dict(zip(list(df.columns.values), df.iloc[0]))


# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:



