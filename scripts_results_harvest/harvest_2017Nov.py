import os, sys

rootpath = '..'
moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)
import optimisation
import helper
thisHelper = helper.Helper()
import csv
import pickle

country = 'Tanzania'
date = '2017Sep'
spreadsheetDate = '2017Sep'
numModelSteps = 180
costCurveType = 'standard'
outcomeOfInterestList = ['thrive', 'deaths']
optimiseList = ['deaths', 'thrive']

## -------------- NATIONAL   -----------------
##baseline 1
#spreadsheet = rootpath+'/input_spreadsheets/'+country+'/'+spreadsheetDate+'/InputForCode_'+country+'_IYCF.xlsx'
#cascadeValues = [0.25, 0.50, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0]
#
#for optimise in optimiseList:
#    for outcomeOfInterest in outcomeOfInterestList:
#        resultsFileStem = rootpath+'/Results/'+date+'/'+optimise+'/national/'+country
#        thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, optimise, resultsFileStem, costCurveType) 
#        thisOptimisation.outputCurrentSpendingToCSV()
#        thisOptimisation.outputCascadeAndOutcomeToCSV(cascadeValues, outcomeOfInterest)
#
##baseline 2
#spreadsheet = rootpath+'/input_spreadsheets/'+country+'/'+spreadsheetDate+'/InputForCode_'+country+'_baseline2.xlsx'
#
#for optimise in optimiseList:
#    for outcomeOfInterest in outcomeOfInterestList:
#        resultsFileStem = rootpath+'/Results/'+date+'/'+optimise+'/national_baseline2/'+country
#        thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, optimise, resultsFileStem, costCurveType) 
#        thisOptimisation.outputCurrentSpendingToCSV()
#        thisOptimisation.outputCascadeAndOutcomeToCSV(cascadeValues, outcomeOfInterest)

## --------------- GEOSPATIAL ---------------- 
cascadeValues = [0.0, 0.1, 0.2, 0.4, 0.8, 1.0, 1.1, 1.25, 1.5, 1.7, 2.0, 3., 4., 5., 6., 8., 10., 15.0, 20.0, 50.0, 100.0, 'extreme']
GAFile = 'GA_progNotFixed'
regionNameList = ['Arusha', 'Dar_es_Salaam', 'Dodoma', 'Geita', 'Iringa', 'Kagera',
                  'Kaskazini_Pemba', 'Kaskazini_Unguja', 'Katavi', 'Kigoma', 'Kilimanjaro',
                  'Kusini_Pemba', 'Kusini_Unguja', 'Lindi', 'Manyara', 'Mara', 'Mbeya',
                  'Mjini_Magharibi', 'Morogoro', 'Mtwara', 'Mwanza', 'Njombe', 'Pwani',
                  'Rukwa', 'Ruvuma', 'Shinyanga', 'Simiyu', 'Singida', 'Tabora', 'Tanga']

spreadsheetFileStem = rootpath + '/input_spreadsheets/' + country + '/' + spreadsheetDate + '/regions/InputForCode_'
spreadsheetList = []
for regionName in regionNameList:
    spreadsheet = spreadsheetFileStem + regionName + '_IYCF.xlsx'
    spreadsheetList.append(spreadsheet)

# get trade off curves
for optimise in optimiseList:
    resultsFileStem = rootpath + '/Results/' + date + '/' + optimise + '/geospatialProgNotFixedIYCF/'
    BOCsFileStem = resultsFileStem + 'regionalBOCs/'
    geospatialOptimisation = optimisation.GeospatialOptimisation(spreadsheetList, regionNameList, numModelSteps, cascadeValues, optimise, resultsFileStem, costCurveType, BOCsFileStem)
    geospatialOptimisation.outputTradeOffCurves()
        
        
# get individual regions optimised spending (from the cascade)
i=0     
for optimise in optimiseList:
    resultsFileStem = rootpath + '/Results/' + date + '/' + optimise + '/geospatialProgNotFixedIYCF/'        
    outfilename = 'individual_region_optimised_spending'+optimise+'.csv'  
    with open(outfilename, "wb") as f:
        writer = csv.writer(f)
        for region in range(len(regionNameList)):
            regionName = regionNameList[region]
            spreadsheet = spreadsheetList[region]
            thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, 'dummy', resultsFileStem, costCurveType)    
            filename = '%s%s_cascade_%s_1.0.pkl'%(resultsFileStem, regionName, optimise)
            infile = open(filename, 'rb')
            thisSpending = pickle.load(infile)
            infile.close()  
            if i<1: #do this once
                writer.writerow(['region'] + [key for key in thisSpending.keys()])
            row = [regionName] + [value for value in thisSpending.values()]
            i+=1
            writer.writerow(row)                
        
# get outcomes for optimised spending
for optimise in optimiseList:
    resultsFileStem = rootpath + '/Results/' + date + '/' + optimise + '/geospatialProgNotFixedIYCF/'        
    outfilename = 'optimised_'+optimise+'_regional_output.csv'  
    header1 = ['region', 'thrive', 'deaths', 'stunting prev']  
    with open(outfilename, "wb") as f:
        writer = csv.writer(f)
        writer.writerow(header1)
        for region in range(len(regionNameList)):
            regionName = regionNameList[region]
            spreadsheet = spreadsheetList[region]
            thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, 'dummy', resultsFileStem, costCurveType)    
            filename = '%s%s_%s.pkl'%(resultsFileStem, GAFile, regionName)
            infile = open(filename, 'rb')
            thisSpending = pickle.load(infile)
            infile.close()        
            modelList = thisOptimisation.oneModelRunWithOutput(thisSpending)    
            row =[regionName, modelList[numModelSteps-1].getOutcome('thrive'), modelList[numModelSteps-1].getOutcome('deaths'), modelList[numModelSteps-1].getOutcome('stunting prev')]
            writer.writerow(row)        

# put regional optimised spending into csv  (this is post GA) 
i=0     
for optimise in optimiseList:
    resultsFileStem = rootpath + '/Results/' + date + '/' + optimise + '/geospatialProgNotFixedIYCF/'        
    outfilename = 'regional_postGA_optimised_spending'+optimise+'.csv'  
    with open(outfilename, "wb") as f:
        writer = csv.writer(f)
        for region in range(len(regionNameList)):
            regionName = regionNameList[region]
            spreadsheet = spreadsheetList[region]
            thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, 'dummy', resultsFileStem, costCurveType)    
            filename = '%s%s_%s.pkl'%(resultsFileStem, GAFile, regionName)
            infile = open(filename, 'rb')
            thisSpending = pickle.load(infile)
            infile.close()  
            if i<1: #do this once
                writer.writerow(['region'] + [key for key in thisSpending.keys()])
            row = [regionName] + [value for value in thisSpending.values()]
            i+=1
            writer.writerow(row)          
        