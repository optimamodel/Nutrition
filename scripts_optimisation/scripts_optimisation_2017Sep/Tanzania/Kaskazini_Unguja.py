# -*- coding: utf-8 -*-
"""
Created on Mon Oct 16 12:44:38 2017
Script to zero out the breastfeeding promotion spending for the Kaskazini Ungaja region in the thrive analysis
@author: ruth
"""
rootpath = '../../..'
import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)
import optimisation
import csv
import pickle

regionName = 'Kaskazini_Unguja'
optimise = 'thrive'
country = 'Tanzania'
date = '2017Sep'
spreadsheetDate = '2017Sep'
costCurveType = 'standard'
numModelSteps = 180
spreadsheet = rootpath + '/input_spreadsheets/' + country + '/' + spreadsheetDate + '/regions/InputForCode_' + regionName + '.xlsx'
resultsFileStem = rootpath + '/Results/' + date + '/' + optimise + '/geospatialProgNotFixed/'
GAFile = 'GA_progNotFixed'      

outfilename = regionName + '.csv'  
header1 = ['region', 'thrive', 'deaths', 'stunting prev']  
with open(outfilename, "wb") as f:
    writer = csv.writer(f)
    writer.writerow(header1)
    thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps, 'dummy', resultsFileStem, costCurveType)    
    filename = '%s%s_%s.pkl'%(resultsFileStem, GAFile, regionName)
    infile = open(filename, 'rb')
    thisSpending = pickle.load(infile)
    thisSpending['Breastfeeding promotion'] = 0.0
    infile.close()        
    modelList = thisOptimisation.oneModelRunWithOutput(thisSpending)    
    row =[regionName, modelList[numModelSteps-1].getOutcome('thrive'), modelList[numModelSteps-1].getOutcome('deaths'), modelList[numModelSteps-1].getOutcome('stunting prev')]
    writer.writerow(row)