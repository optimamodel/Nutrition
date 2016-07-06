# -*- coding: utf-8 -*-
"""
Created on Mon Jun 27 11:24:16 2016

@author: ruth
"""
import pickle as pickle
cascadeValues = [0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 4.0] 

# BANGLADESH DEATHS
cascade_deaths = []
for cascade in cascadeValues:
    filename = '../Results2016Jun/Bangladesh/deaths/v5/Bangladesh_cascade_deaths_v5_'+str(cascade)+'.pkl'
    infile = open(filename, 'rb')
    thisDict = {cascade:pickle.load(infile)}
    cascade_deaths.append(thisDict)
    infile.close()


# BANGLADESH STUNTING
cascade_stunting = []
for cascade in cascadeValues:
    filename = '../Results2016Jun/Bangladesh/stunting/v5/Bangladesh_cascade_stunting_v5_'+str(cascade)+'.pkl'
    infile = open(filename, 'rb')
    thisDict = {cascade:pickle.load(infile)}
    cascade_stunting.append(thisDict)
    infile.close()
    
    
# GEOSPATIAL DEATHS
geospatialDeaths = []
for region in range(0,7):
    deaths = []
    for cascade in cascadeValues:
        filename = '../Results2016Jun/Bangladesh/deaths/geospatial/v3/region'+str(region)+'_cascade_deaths_'+str(cascade)+'.pkl'
        infile = open(filename, 'rb')
        thisDict = {cascade:pickle.load(infile)}
        deaths.append(thisDict)
        infile.close()    
        
    thisRegionDict = {'region '+str(region):deaths}
    geospatialDeaths.append(thisRegionDict)
    
    
    
# GEOSPATIAL STUNTING
geospatialStunting = []
for region in range(0,7):
    stunting = []
    for cascade in cascadeValues:
        filename = '../Results2016Jun/Bangladesh/stunting/geospatial/v3/region'+str(region)+'_cascade_stunting_'+str(cascade)+'.pkl'
        infile = open(filename, 'rb')
        thisDict = {cascade:pickle.load(infile)}
        stunting.append(thisDict)
        infile.close()    
        
    thisRegionDict = {'region '+str(region):stunting}
    geospatialStunting.append(thisRegionDict)    
    
    