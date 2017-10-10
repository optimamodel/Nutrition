import os, sys

rootpath = '..'
moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)
import optimisation
import data
import helper
thisHelper = helper.Helper()
import csv

country = 'Tanzania'
date = '2017Sep'
spreadsheetDate = '2017Sep'
numModelSteps = 180

outcomeOfInterestList = ['thrive', 'deaths']
optimiseList = ['deaths', 'thrive']
cascadeValues = [0.0, 0.1, 0.2, 0.4, 0.8, 1.0, 1.1, 1.25, 1.5, 1.7, 2.0, 'extreme']
costCurveType = 'standard'
GAFile = 'GA_progNotFixed'
regionNameList = ['Arusha', 'Dar_es_Salaam', 'Dodoma', 'Geita', 'Iringa', 'Kagera',
                  'Kaskazini_Pemba', 'Kaskazini_Unguja', 'Katavi', 'Kigoma', 'Kilimanjaro',
                  'Kusini_Pemba', 'Kusini_Unguja', 'Lindi', 'Manyara', 'Mara', 'Mbeya',
                  'Mjini_Magharibi', 'Morogoro', 'Mtwara', 'Mwanza', 'Njombe', 'Pwani',
                  'Rukwa', 'Ruvuma', 'Shinyanga', 'Simiyu', 'Singida', 'Tabora', 'Tanga']

spreadsheetFileStem = rootpath + '/input_spreadsheets/' + country + '/' + spreadsheetDate + '/regions/InputForCode_'
spreadsheetList = []
for regionName in regionNameList:
    spreadsheet = spreadsheetFileStem + regionName + '.xlsx'
    spreadsheetList.append(spreadsheet)


for optimise in optimiseList:
    resultsFileStem = rootpath + '/Results/' + date + '/' + optimise + '/geospatialProgNotFixed/'
    geospatialOptimisation = optimisation.GeospatialOptimisation(spreadsheetList, regionNameList, numModelSteps, cascadeValues, optimise, resultsFileStem, costCurveType)
    geospatialOptimisation.outputRegionalCurrentSpendingToCSV()
    geospatialOptimisation.outputRegionalPostGAOptimisedSpendingToCSV(GAFile)
    geospatialOptimisation.outputTradeOffCurves()
    for outcome in outcomeOfInterestList:
        geospatialOptimisation.outputRegionalCascadesAndOutcomeToCSV(outcome)
        
        
# get outcomes for current spending and zero spending
spreadsheetData = data.readSpreadsheet(spreadsheetList[0], thisHelper.keyList)        
zeroSpending = {}    
for i in range(0, len(spreadsheetData.interventionList)):
    intervention = spreadsheetData.interventionList[i]
    zeroSpending[intervention] = 0.        
    
outfilename = 'zero_spending.csv'  
header1 = ['region', 'thrive', 'deaths', 'stunting prev']  
with open(outfilename, "wb") as f:
    writer = csv.writer(f)
    writer.writerow(header1)
    for region in range(len(regionNameList)):
        regionName = regionNameList[region]
        spreadsheet = spreadsheetList[region]
        thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, 'dummy', resultsFileStem, costCurveType)    
        modelList = thisOptimisation.oneModelRunWithOutput(zeroSpending)    
        row =[regionName, modelList[numModelSteps-1].getOutcome('thrive'), modelList[numModelSteps-1].getOutcome('deaths'), modelList[numModelSteps-1].getOutcome('stunting prev')]
        writer.writerow(row)

outfilename = 'current_spending.csv'  
header1 = ['region', 'thrive', 'deaths', 'stunting prev']  
with open(outfilename, "wb") as f:
    writer = csv.writer(f)
    writer.writerow(header1)
    for region in range(len(regionNameList)):
        regionName = regionNameList[region]
        spreadsheet = spreadsheetList[region]
        thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, 'dummy', resultsFileStem, costCurveType)    
        thisSpending = thisOptimisation.getInitialAllocationDictionary()        
        modelList = thisOptimisation.oneModelRunWithOutput(thisSpending)    
        row =[regionName, modelList[numModelSteps-1].getOutcome('thrive'), modelList[numModelSteps-1].getOutcome('deaths'), modelList[numModelSteps-1].getOutcome('stunting prev')]
        writer.writerow(row)
