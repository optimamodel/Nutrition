# -*- coding: utf-8 -*-
"""
Created on Mon Oct 16 13:22:22 2017

@author: ruth
"""

import pchip
import pickle
import optimisation
from scipy import interpolate
import numpy as np


regionNameList = ['Arusha', 'Dar_es_Salaam', 'Dodoma', 'Geita', 'Iringa', 'Kagera',
                  'Kaskazini_Pemba', 'Kaskazini_Unguja', 'Katavi', 'Kigoma', 'Kilimanjaro',
                  'Kusini_Pemba', 'Kusini_Unguja', 'Lindi', 'Manyara', 'Mara', 'Mbeya',
                  'Mjini_Magharibi', 'Morogoro', 'Mtwara', 'Mwanza', 'Njombe', 'Pwani',
                  'Rukwa', 'Ruvuma', 'Shinyanga', 'Simiyu', 'Singida', 'Tabora', 'Tanga']

# STEP 1: GET BOCS AND SAVE THEM IN A PKL FILE
optimise = 'thrive'
filename = 'Tanzania_BOCs_' + optimise +'.pkl'
#country = 'Tanzania'
#date = '2017Sep'
#spreadsheetDate = '2017Sep'
#numModelSteps = 180
#cascadeValues = [0.0, 0.1, 0.2, 0.4, 0.8, 1.0, 1.1, 1.25, 1.5, 1.7, 2.0, 3., 4., 5., 6., 8., 10., 15.0, 20.0, 50.0, 100.0, 200.0, 400.0, 600.0, 'extreme']
#costCurveType = 'standard'
#GAFile = 'GA_progNotFixed'
#
#resultsFileStem = 'Results/' + date + '/' + optimise + '/geospatialProgNotFixed/'
#spreadsheetFileStem = 'input_spreadsheets/' + country + '/' + spreadsheetDate + '/regions/InputForCode_'
#spreadsheetList = []
#for regionName in regionNameList:
#    spreadsheet = spreadsheetFileStem + regionName + '.xlsx'
#    spreadsheetList.append(spreadsheet)
#
#
#geospatialOptimisation = optimisation.GeospatialOptimisation(spreadsheetList, regionNameList, numModelSteps, cascadeValues, optimise, resultsFileStem, costCurveType)
#geospatialOptimisation.outputRegionalBOCsFile(filename)

# STEP 2: USE BOCS TO CHECK PCHIP INTERPOLATION                  
infile = open(filename, 'rb')
regionalBOCs = pickle.load(infile)
valueList = range(0, 37000000, 10000)
lines = {}

for regionName in regionNameList:
    x = regionalBOCs[regionName]['spending']
    y = regionalBOCs[regionName]['outcome']
    # using pchip    
    slopes = pchip.pchip_slopes(x, y, monotone=True)
    outcome = pchip.pchip_eval(x, y, slopes, valueList, deriv = False) 
    lines[regionName] = outcome
        
colourList = ['r','b','k','m','c']        
subList = [regionNameList[0:5], regionNameList[5:10], regionNameList[10:15], regionNameList[15:20], regionNameList[20:25], regionNameList[25:30]]        
        
import matplotlib.pyplot as plt
for thisList in subList:
    i = 0
    for regionName in thisList:
        plt.plot(valueList, lines[regionName], label = regionName, color = colourList[i] )
        plt.plot(regionalBOCs[regionName]['spending'], regionalBOCs[regionName]['outcome'], marker = 'o', linestyle = 'None', markerfacecolor = colourList[i])
        i += 1
    plt.ylabel('number thriving')
    plt.xlabel('spending $')
    #plt.legend()
    plt.xlim([0,2e6])
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=5, fontsize=10, frameon=False)
    plt.show()          
  
  
  
  
  
#  Look at just one
import matplotlib.pyplot as plt
regionName = 'Arusha'
x = regionalBOCs[regionName]['spending']
y = regionalBOCs[regionName]['outcome'] 
#x = x[:20]
#y = y[:20]

# using scipy interpolate
f = interpolate.interp1d(x, y, kind = 'linear')
ynew = f(valueList)
scipy1 = ynew
    
# using numpy (linear piecewise)
numpy1 = np.interp(valueList, x, y)

# scipy pchip
#f = interpolate.PchipInterpolator(x,y)
#scipy2 = f(valueList)

# old pchip
slopes = pchip.pchip_slopes(x, y, monotone=True)
outcome = pchip.pchip_eval(x, y, slopes, valueList, deriv = False)

plt.plot(regionalBOCs[regionName]['spending'], regionalBOCs[regionName]['outcome'], marker = 'o', linestyle = 'None')
#plt.plot(valueList, scipy1, label = 'scipy interp1d') #, marker = 'o', linestyle = 'None')
#plt.plot(valueList, numpy1, label = 'numpy interp') # , marker = 'o', linestyle = 'None')
#plt.plot(valueList, scipy2, label = 'scipy pchip') # , marker = 'o', linestyle = 'None')
#plt.plot(valueList, outcome, label = 'old pchip') # , marker = 'o', linestyle = 'None')

plt.ylabel('number thriving')
plt.xlabel('spending $')
plt.xlim([0,40e6])
plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=5, fontsize=10, frameon=False)
plt.show()     


