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
        
        