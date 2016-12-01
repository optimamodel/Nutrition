# -*- coding: utf-8 -*-
"""
Created on Wed Nov 16 13:50:35 2016

@author: ruth
"""

class Project:
    def __init__(self, projectDataSpreadsheetName):
        self.projectDataSpreadsheetName = projectDataSpreadsheetName
        self.constraintTypeList = ['noConstraints', 'fixedCosts']
        self.results = {}
        self.projectData = ProjectData(projectDataSpreadsheetName)
        # instantiate optimisation object
        import optimisation      
        self.thisOptimisation = optimisation.Optimisation(self.projectData.dataSpreadsheetName, self.projectData.numModelSteps, self.projectData.optimise, self.projectData.resultsFileStem)
        
    def runCascade(self):
        cascadeValues = [1.0, 2.0]  # REMOVE this once cascade read from csv is fixed
        numCores = len(cascadeValues)
        self.results['cascade'] = self.thisOptimisation.performParallelCascadeOptimisation(self.projectData.MCSampleSize, cascadeValues, numCores, self.projectData.haveFixedProgCosts)
         
        
    def runSingleOptimisation(self):
        self.results['single optimisation'] = self.thisOptimisation.performSingleOptimisation(self.projectData.MCSampleSize, self.projectData.haveFixedProgCosts)
         
        
    def runSingleOptimisationCustomBudget(self, customBudget):
        self.results['single optimisation budget $' + str(customBudget)] = self.thisOptimisation.performSingleOptimisationForGivenTotalBudget(self.projectData.MCSampleSize, customBudget, "custom_budget_$"+str(customBudget), self.projectData.haveFixedProgCosts)
        

        
    def outputProjectResults(self):
        #output everything in results to csv, including info about the project
        import xlwt, csv, os     
        # make folder for CSV files
        if not os.path.exists(self.projectData.resultsFileStem+'CSVs/'):
            os.makedirs(self.projectData.resultsFileStem+'CSVs/')
        # run functions to make CSV files    
        self.outputProjectOverviewCSV()        
        self.outputCascadeToCSV()
        # combine all CSV files in CSV directory into one .xls file
        csvFolder = self.projectData.resultsFileStem + 'CSVs/'
        book = xlwt.Workbook()
        for fil in os.listdir(csvFolder):
            sheet = book.add_sheet(fil[:-4])
            with open(csvFolder + fil) as filname:
                reader = csv.reader(filname)
                i = 0
                for row in reader:
                    for j, each in enumerate(row):
                        sheet.write(i, j, each)
                    i += 1
        book.save("%sResults.xls"%(self.projectData.resultsFileStem))
        
        
    def outputProjectOverviewCSV(self):
        import csv
        rows = []
        rows.append(self.projectData.projectName)
        rows.append(self.projectData.projectDescription)
        rows.append(self.projectData.projectDataSpreadsheetName)
        rows.append(self.projectData.dataSpreadsheetName)
        rows.append(' ')
        # add current spending and coverage        
        outfilename = '%s%soverview.csv'%(self.projectData.resultsFileStem, 'CSVs/')
        with open(outfilename, "wb") as f:
            writer = csv.writer(f)
            writer.writerows(rows)    
    
    def outputCascadeToCSV(self):
        import csv
        # write the cascade csv
        prognames = self.results['cascade'][self.projectData.cascade[0]].keys()            
        prognames.insert(0, 'Multiple of current budget')
        rows = []
        for i in range(len(self.projectData.cascade)):
            value = self.projectData.cascade[i]
            allocationDict = self.results['cascade'][value]               
            valarray = allocationDict.values()
            valarray.insert(0, value)
            rows.append(valarray)
        outfilename = '%s%scascade%s.csv'%(self.projectData.resultsFileStem, 'CSVs/', self.projectData.optimise)
        with open(outfilename, "wb") as f:
            writer = csv.writer(f)
            writer.writerow(prognames)
            writer.writerows(rows)
        
        
class ProjectData:
    def __init__(self, projectDataSpreadsheetName):
        self.projectDataSpreadsheetName = projectDataSpreadsheetName        
        self.projectName = None        
        self.projectDescription = None         
        self.analysisType = None
        self.spendingConstraints = None
        self.dataSpreadsheetName = None
        self.country = None
        self.date = None
        self.numYears = None
        self.optimise = None
        self.cascade = None
        self.extraMoney = None
        self.MCSampleSize = None
        self.geoMCSampleSize = None
        self.reRunMCSampleSize = None
        self.dataFromSpreadsheet = None
        # call function to read project spreadsheet into variables
        self.readProjectDataFromSpreadsheet()
        # set some derived variables
        self.numModelSteps = self.numYears * 12
        self.haveFixedProgCosts = False
        if self.spendingConstraints == 'fixedCosts':
            self.haveFixedProgCosts = True
        self.resultsFileStem = 'ResultsTest/'+self.date+'/'+self.optimise+'/'+self.analysisType+'/'+self.spendingConstraints+'/'+self.country+'/'    
        
    def readProjectDataFromSpreadsheet(self):    
        #read from csv         
        import pandas
        import data
        import helper
        helper = helper.Helper()
        Location = self.projectDataSpreadsheetName     
        df = pandas.read_excel(Location, sheetname = 'data')
        dataList = list(df['data'])
        df = pandas.read_excel(Location, sheetname = 'data', index_col = 'data')
        values = {}
        # if the values aren't nan add them to the dictionary
        for d in dataList:
            thisValue = df.loc[d, 'values']
            checkNull = pandas.isnull(thisValue)
            if checkNull:
                values[d] = None
            else:
                values[d] = thisValue
        # put the values into the class variables
        self.projectName = values['project name']        
        self.projectDescription = values['project description']         
        self.analysisType = values['analysis type']
        self.spendingConstraints = values['spending constraints']
        self.dataSpreadsheetName = values['data spreadsheet']
        self.country = values['country']
        self.date = values['date']
        self.numYears = values['number of years']
        self.optimise = values['optimise for']
        self.cascade = [1.0, 2.0]  #FIX THIS values['cascade multiples'].split()
        self.extraMoney = values['extra money']
        self.MCSampleSize = values['MCSampleSize']
        self.geoMCSampleSize = values['geoMCSampleSize']
        self.reRunMCSampleSize = values['reRunMCSampleSize']
        # read the data from data spreasdsheet into data object
        self.dataFromSpreadsheet = data.readSpreadsheet(self.dataSpreadsheetName, helper.keyList)
        
            
        
        
        