# -*- coding: utf-8 -*-
"""
Created on Tue Jul 12 2016

@author: madhurakilledar and kelseygrantham
"""
import pickle
cascade = [0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 4.0] 

country = 'Bangladesh'
root = '../../Results2016Jun/%s'%(country)


# convert 
# from dictionary of list of dictionaries of...arrays?
# to list of lists
# and a header
def reformat_results(results):
    from numpy import array
    increments = results.keys()
    spendingsets = results.values()
    rows = []
    for i in range(len(increments)):
        chunk = spendingsets[i]
        values = array(chunk.values()).tolist()
        valarray = [item for sublist in values for item in sublist]
        valarray.insert(0, increments[i])
        rows.append(valarray)
    rows.sort()
    prognames = spendingsets[0].keys()
    prognames.insert(0, 'Multiple')
    return prognames, rows



# NATIONAL
version = 'v5'
national = {}
for outcome in ['deaths','stunting']:
    national[outcome] = {}
    for multiple in cascade:
        filename = '%s/%s/%s/%s_cascade_%s_%s_%s.pkl'%(root, outcome, version, country, outcome, version, str(multiple))
        infile = open(filename, 'rb')
        result = pickle.load(infile)
        national[outcome][multiple] = result
        infile.close()

    prognames, rows = reformat_results(national[outcome])

    import csv
    outfilename = '%s/national_cascade_min_%s.csv'%(root, outcome)
    with open(outfilename, "wb") as f:
        writer = csv.writer(f)
        writer.writerow(prognames)
        writer.writerows(rows)



# GEOSPATIAL
version = 'v3'
numRegions = 7
geospatial = {}
for outcome in ['deaths','stunting']:
    geospatial[outcome] = {}
    for iReg in range(numRegions):
        region = 'region%s'%(iReg)
        geospatial[outcome][region] = {}
        for multiple in cascade:
            filename = '%s/%s/geospatial/%s/%s_cascade_%s_%s.pkl'%(root, outcome, version, region, outcome, str(multiple))
            infile = open(filename, 'rb')
            result = pickle.load(infile)
            geospatial[outcome][region][multiple] = result
            infile.close()

        prognames, rows = reformat_results(geospatial[outcome][region])

        import csv
        outfilename = '%s/%s_cascade_min_%s.csv'%(root, region, outcome)
        with open(outfilename, "wb") as f:
            writer = csv.writer(f)
            writer.writerow(prognames)
            writer.writerows(rows)



"""
# BANGLADESH DEATHS
cascade_deaths = []
for cascade in cascadeValues:
    filename = '../Results2016Jul/Bangladesh/deaths/v1/Bangladesh_cascade_deaths_v1_'+str(cascade)+'.pkl'
    infile = open(filename, 'rb')
    thisDict = {cascade:pickle.load(infile)}
    cascade_deaths.append(thisDict)
    infile.close()


# BANGLADESH STUNTING
cascade_stunting = []
for cascade in cascadeValues:
    filename = '../Results2016Jul/Bangladesh/stunting/v1/Bangladesh_cascade_stunting_v1_'+str(cascade)+'.pkl'
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
"""    
    
