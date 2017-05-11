# -*- coding: utf-8 -*-
"""
Created on Thu May 11 15:47:50 2017

@author: ruth
"""

import pchip
import pickle

regionNameList = ['Barisal', 'Chittagong', 'Dhaka', 'Khulna', 'Rajshahi', 'Rangpur', 'Sylhet']
filename = 'scripts_results_harvest/regionalBOCs'
infile = open(filename, 'rb')
regionalBOCs = pickle.load(infile)
valueList = range(0, 22000000, 2000000)
lines = {}

for regionName in regionNameList:
    x = regionalBOCs[regionName]['spending']
    y = regionalBOCs[regionName]['outcome']
    slopes = pchip.pchip_slopes(x, y, monotone=True)
         
    outcome = pchip.pchip_eval(x, y, slopes, valueList, deriv = False) 
    lines[regionName] = outcome
        
        
        
import matplotlib.pyplot as plt
for regionName in regionNameList:
    plt.plot(valueList, lines[regionName], label = regionName)
plt.ylabel('number thriving')
plt.xlabel('spending $')
plt.legend()
plt.show()            