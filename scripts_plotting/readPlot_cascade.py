# -*- coding: utf-8 -*-
"""
Created on Tue Jul 12 2016

@author: madhurakilledar and kelseygrantham
"""
import pickle
import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(moduleDir)
from plotting import plotalloccascade

cascadeMultiples = [0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 4.0] 

country = 'Bangladesh'
version = 'Results20160718'

root = '../../%s/%s'%(country,version)
print "\n find input here : %s"%root


# NATIONAL
print country
national = {}
for objective in ['deaths','stunting']:
    national[objective] = {}
    for multiple in cascadeMultiples:
        filename = '%s/%s/national/%s_cascade_%s_%s.pkl'%(root, objective, country, objective, str(multiple))
        infile = open(filename, 'rb')
        allocation = pickle.load(infile)
        national[objective][multiple] = allocation
        infile.close()
    # plot
    plotalloccascade(national[objective])



# GEOSPATIAL
numRegions = 7
geospatial = {}
for iReg in range(numRegions):
    region = 'region%s'%(iReg)
    geospatial[region] = {}
    for objective in ['deaths','stunting']:
        geospatial[region][objective] = {}
        for multiple in cascadeMultiples:
            filename = '%s/%s/geospatial/%s_cascade_%s_%s.pkl'%(root, objective, region, objective, str(multiple))
            infile = open(filename, 'rb')
            allocation = pickle.load(infile)
            geospatial[region][objective][multiple] = allocation
            infile.close()
        # plot
        plotalloccascade(geospatial[region][objective])
