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
        self.numModelSteps = self.projectData.numYears * 12
        self.haveFixedProgCosts = False
        if self.projectData.analysisType == 'fixedCosts':
            self.haveFixedProgCosts = True
        self.resultsFileStem = 'ResultsTest/'+self.projectData.date+'/'+self.projectData.optimise+'/'+self.projectData.analysisType+'/'+self.projectData.spendingConstraints+'/'+self.projectData.country    
        
    def runCascade(self):
        import optimisation      
        thisOptimisation = optimisation.Optimisation(self.projectData.dataSpreadsheetName, self.numModelSteps, self.projectData.optimise, self.resultsFileStem)
        cascadeValues = [1.0, 2.0]  # REMOVE this once cascade read from csv is fixed
        numCores = len(cascadeValues)
        thisOptimisation.performParallelCascadeOptimisation(self.projectData.MCSampleSize, cascadeValues, numCores, self.haveFixedProgCosts)
        # modify above function to return the cascade dictionaries and store in self.results
        # self.results['cascade'] = return value
        
    def runSingleOptimisation(self):
        import optimisation      
        thisOptimisation = optimisation.Optimisation(self.projectData.dataSpreadsheetName, self.numModelSteps, self.projectData.optimise, self.resultsFileStem)
        thisOptimisation.performSingleOptimisation(self.projectData.MCSampleSize)
        # modify above function to return the cascade dictionaries and store in self.results
        # self.results['single optimisation'] = return value
        
    def runSingleOptimisationCustomBudget(self, customBudget):
        import optimisation      
        thisOptimisation = optimisation.Optimisation(self.projectData.dataSpreadsheetName, self.numModelSteps, self.projectData.optimise, self.resultsFileStem)
        thisOptimisation.performSingleOptimisationForGivenTotalBudget(self.projectData.MCSampleSize, customBudget, "custom_budget_$"+customBudget, self.haveFixedProgCosts)
        # modify above function to return the cascade dictionaries and store in self.results
        # self.results['custom budget'] = {}
        # self.results['custom budget']['budget'] = customBudget
        # self.results['custom budget']['allocation'] = return value
        
    def outputProjectResults(self):
        #output everything in results to csv, including info about the project
        
        
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
        
        self.readProjectDataFromSpreadsheet()
        
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
        self.cascade = values['cascade multiples'].split()
        self.extraMoney = values['extra money']
        self.MCSampleSize = values['MCSampleSize']
        self.geoMCSampleSize = values['geoMCSampleSize']
        self.reRunMCSampleSize = values['reRunMCSampleSize']
        # read the data from data spreasdsheet into data object
        self.dataFromSpreadsheet = data.readSpreadsheet(self.dataSpreadsheetName, helper.keyList)
        
            
        
        
        