# -*- coding: utf-8 -*-
"""
Created on Tue Jul 12 2016

@author: madhurakilledar and kelseygrantham
"""
import pickle

country = 'Bangladesh'
version = 'Results20160718'

root = '../../%s/%s'%(country,version)
print "\n find input here : %s"%root

import os
outpath = '../../%s/%s_csv'%(country,version)
print "\n find output here : %s"%outpath
if not os.path.exists(outpath):
    os.makedirs(outpath)

cascadeMultiples = [0.25, 0.50, 0.75, 1.0, 1.50, 2.0, 3.0, 4.0] 


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
national = {}
for outcome in ['deaths','stunting']:
    national[outcome] = {}
    for multiple in cascadeMultiples:
        filename = '%s/%s/national/%s_cascade_%s_%s.pkl'%(root, outcome, country, outcome, str(multiple))
        infile = open(filename, 'rb')
        allocation = pickle.load(infile)
        national[outcome][multiple] = allocation
        infile.close()

    prognames, rows = reformat_results(national[outcome])

    import csv
    outfilename = '%s/national_cascade_min%s.csv'%(outpath, outcome)
    with open(outfilename, "wb") as f:
        writer = csv.writer(f)
        writer.writerow(prognames)
        writer.writerows(rows)



# GEOSPATIAL
numRegions = 7
geospatial = {}
for outcome in ['deaths','stunting']:
    geospatial[outcome] = {}
    for iReg in range(numRegions):
        region = 'region%s'%(iReg)
        geospatial[outcome][region] = {}
        for multiple in cascadeMultiples:
            filename = '%s/%s/geospatial/%s_cascade_%s_%s.pkl'%(root, outcome, region, outcome, str(multiple))
            infile = open(filename, 'rb')
            allocation = pickle.load(infile)
            geospatial[outcome][region][multiple] = allocation
            infile.close()

        prognames, rows = reformat_results(geospatial[outcome][region])

        import csv
        outfilename = '%s/%s_cascade_min%s.csv'%(outpath, region, outcome)
        with open(outfilename, "wb") as f:
            writer = csv.writer(f)
            writer.writerow(prognames)
            writer.writerows(rows)
