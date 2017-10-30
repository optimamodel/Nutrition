# -*- coding: utf-8 -*-
"""
Created on Mon Oct 30 17:18:21 2017

@author: Nick
"""
import data
from copy import deepcopy as dcp
import helper
import pandas as pd
helper = helper.Helper()

regionNameList = ['Arusha', 'Dar_es_Salaam', 'Dodoma', 'Geita', 'Iringa', 'Kagera',
                  'Kaskazini_Pemba', 'Kaskazini_Unguja', 'Katavi', 'Kigoma', 'Kilimanjaro',
                  'Kusini_Pemba', 'Kusini_Unguja', 'Lindi', 'Manyara', 'Mara', 'Mbeya',
                  'Mjini_Magharibi', 'Morogoro', 'Mtwara', 'Mwanza', 'Njombe', 'Pwani',
                  'Rukwa', 'Ruvuma', 'Shinyanga', 'Simiyu', 'Singida', 'Tabora', 'Tanga']

numModelSteps = 60 # 5 years so that the model runs all the way through

pop_1 = []
pop_1_5 = []
pop_6_11 = []
pop_12_23 = []
pop_24_59 = []
percentlist = []
U5_init = []

for region in range(len(regionNameList)):
    spreadsheet = 'C:/Users/Nick/Desktop/Nutrition/input_spreadsheets/Tanzania/2017Sep/regions/' + 'InputForCode_' + regionNameList[region] + '.xlsx'   
    spreadsheetData = data.readSpreadsheet(spreadsheet, helper.keyList)

    model, derived, params = helper.setupModelDerivedParameters(spreadsheetData)
    modelList = [] 
    timestepsPre = 12
    for t in range(timestepsPre):
        model.moveOneTimeStep()  
        modelThisTimeStep = dcp(model)
        modelList.append(modelThisTimeStep)
        
    stepFinal = numModelSteps-1   
    for t in range(numModelSteps):
        model.moveOneTimeStep()  
        modelThisTimeStep = dcp(model)
        modelList.append(modelThisTimeStep)
    
    pop_1.append(modelList[stepFinal].listOfAgeCompartments[0].getTotalPopulation())
    pop_1_5.append(modelList[stepFinal].listOfAgeCompartments[1].getTotalPopulation())
    pop_6_11.append(modelList[stepFinal].listOfAgeCompartments[2].getTotalPopulation())
    pop_12_23.append(modelList[stepFinal].listOfAgeCompartments[3].getTotalPopulation())
    pop_24_59.append(modelList[stepFinal].listOfAgeCompartments[4].getTotalPopulation())
    print ((pop_1[len(pop_1)-1] + pop_1_5[len(pop_1_5)-1] + pop_6_11[len(pop_6_11)-1] + pop_12_23[len(pop_12_23)-1]) / ((pop_1[len(pop_1)-1] + pop_1_5[len(pop_1_5)-1] + pop_6_11[len(pop_6_11)-1] + pop_12_23[len(pop_12_23)-1] + pop_24_59[len(pop_24_59)-1])))
    percentlist.append((pop_1[len(pop_1)-1] + pop_1_5[len(pop_1_5)-1] + pop_6_11[len(pop_6_11)-1] + pop_12_23[len(pop_12_23)-1]) / ((pop_1[len(pop_1)-1] + pop_1_5[len(pop_1_5)-1] + pop_6_11[len(pop_6_11)-1] + pop_12_23[len(pop_12_23)-1] + pop_24_59[len(pop_24_59)-1])))
    U5_init.append(pop_1[0] + pop_1_5[0] + pop_6_11[0] + pop_12_23[0] + pop_24_59[0])

export = pd.DataFrame(regionNameList)
export['population < 1 month'] = pd.DataFrame(pop_1)
export['population 1-5 month'] = pd.DataFrame(pop_1_5)
export['population 6-11 month'] = pd.DataFrame(pop_6_11)
export['population 12-23 month'] = pd.DataFrame(pop_12_23)
export['population 23-59 month'] = pd.DataFrame(pop_24_59)
export['percent of U5 < 23 months'] = pd.DataFrame(percentlist)
export['U5 total'] = pd.DataFrame(U5_init) 

writer = pd.ExcelWriter('C:/Users/Nick/Desktop/Nutrition/percentages0to23.xlsx', engine='xlsxwriter')
export.to_excel(writer, sheet_name='output')
writer.save()