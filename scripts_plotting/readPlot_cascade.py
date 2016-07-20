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
root = '../../Results2016Jun/%s'%(country)


# NATIONAL
version = 'v5'
national = {}
for objective in ['deaths','stunting']:
    national[objective] = {}
    for multiple in cascadeMultiples:
        filename = '%s/%s/%s/%s_cascade_%s_%s_%s.pkl'%(root, objective, version, country, objective, version, str(multiple))
        infile = open(filename, 'rb')
        allocation = pickle.load(infile)
        national[objective][multiple] = allocation
        infile.close()
    # plot
    plotalloccascade(national[objective])



# GEOSPATIAL
version = 'v3'
numRegions = 7
geospatial = {}
for iReg in range(numRegions):
    region = 'region%s'%(iReg)
    geospatial[region] = {}
    for objective in ['deaths','stunting']:
        geospatial[region][objective] = {}
        for multiple in cascadeMultiples:
            filename = '%s/%s/geospatial/%s/%s_cascade_%s_%s.pkl'%(root, objective, version, region, objective, str(multiple))
            infile = open(filename, 'rb')
            allocation = pickle.load(infile)
            geospatial[region][objective][multiple] = allocation
            infile.close()
        # plot
        plotalloccascade(geospatial[region][objective])
