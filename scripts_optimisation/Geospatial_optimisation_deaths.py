# -*- coding: utf-8 -*-
"""
Created on Fri Jun 24 14:52:36 2016

@author: ruth
"""
import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(moduleDir)
import optimisation

numModelSteps = 180
MCSampleSize = 25
optimise = 'deaths'

spreadsheet0 = '../input_spreadsheets/Bangladesh/subregionSpreadsheets/Barisal.xlsx'
spreadsheet1 = '../input_spreadsheets/Bangladesh/subregionSpreadsheets/Chittagong.xlsx'
spreadsheet2 = '../input_spreadsheets/Bangladesh/subregionSpreadsheets/Dhaka.xlsx'
spreadsheet3 = '../input_spreadsheets/Bangladesh/subregionSpreadsheets/Khulna.xlsx'
spreadsheet4 = '../input_spreadsheets/Bangladesh/subregionSpreadsheets/Rajshahi.xlsx'
spreadsheet5 = '../input_spreadsheets/Bangladesh/subregionSpreadsheets/Rangpur.xlsx'
spreadsheet6 = '../input_spreadsheets/Bangladesh/subregionSpreadsheets/Sylhet.xlsx'
spreadsheetList = [spreadsheet0, spreadsheet1, spreadsheet2, spreadsheet3, spreadsheet4, spreadsheet5, spreadsheet6]

for i in range(0, len(spreadsheetList)):
    spreadsheet = spreadsheetList[i]
    thisOptimisation = optimisation.Optimisation(spreadsheet, numModelSteps)
    filename = 'Bangladesh_geospatial_deaths_region_'+str(i)
    thisOptimisation.performSingleOptimisation(optimise, MCSampleSize, filename)


