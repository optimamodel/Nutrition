# -*- coding: utf-8 -*-
"""
Created on Tue Jul 11 23:44:51 2017

@author: ruth
"""
import os, sys
rootpath = '..'
moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)

import data
import helper
import numpy as np
import matplotlib.pyplot as plt 

thisHelper = helper.Helper()
spreadsheet = rootpath + '/input_spreadsheets/Bangladesh/2016Oct/InputForCode_Bangladesh.xlsx'
thisData=data.readSpreadsheet(spreadsheet, thisHelper.keyList)
m, d, p = thisHelper.setupModelDerivedParameters(thisData)
coEffs = d.getComplementaryFeedingQuarticCoefficients(p.stuntingDistribution, p.coverage)

x = np.arange(-1, 1, 0.1)
y = {}

for age in thisHelper.keyList['ages']:
    y[age] = []
    for val in x:
        a = coEffs[age][0]
        b = coEffs[age][1]
        c = coEffs[age][2]
        d = coEffs[age][3]
        e = coEffs[age][4]
        function = a*x*x*x*x + b*x*x*x +c*x*x + d*x + e
        y[age].append(function)
        plt.plot(x,y[age].tolist())
        plt.title(str(age))
        plt.show()
    
    

