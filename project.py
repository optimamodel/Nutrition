# -*- coding: utf-8 -*-
"""
Created on Wed Nov 16 13:50:35 2016

@author: ruth
"""

class Project:
    def __init__(self, projectName, projectDescription):
        self.projectName = projectName
        self.projectDescription = projectDescription
        self.analylsisType = None
        self.analysisTypeList = ['noConstraints', 'fixedCosts']
        self.dataSpreadsheets = {}
        self.results = {}
        
    def setProjectDescription(self, projectDescription):
        self.projectDescription = projectDescription
        
    def setAnalysisType(self, analysisType):
        if (analysisType in self.analysisTypeList):
            self.analylsisType = analysisType
        else:
            print "analysis type " + analysisType + " is not supported"
            
    def setDataSpreadsheetNational(self, dataSpreadsheetNational):
        self.dataSpreadsheets['national'] = dataSpreadsheetNational
        
    def setDataSpreadsheetGeospatial(self, dataSpreadsheetGeospatial):
        self.dataSpreadsheets['national'] = dataSpreadsheetGeospatial    
        
        
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
        self.cascade = values['cascade multiples']
        self.extraMoney = values['extra money']
        self.MCSampleSize = values['MCSampleSize']
        self.geoMCSampleSize = values['geoMCSampleSize']
        self.reRunMCSampleSize = values['reRunMCSampleSize']
        # read the data from data spreasdsheet into data object
        self.dataFromSpreadsheet = data.readSpreadsheet(self.dataSpreadsheetName, helper.keyList)
        
            
        
        
        