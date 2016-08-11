# -*- coding: utf-8 -*-
"""
Created on Wed June 01 2016

@author: madhurakilledar
"""
from __future__ import division
from copy import deepcopy as dcp
import pickle as pickle

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(moduleDir)
import data
import helper
import output

helper = helper.Helper()

country = 'Bangladesh'
startYear = 2016
version = '1604'

#dataFilename = '../input_spreadsheets/%s/validation/Input_%s_%i_%s_LiST.xlsx'%(country, country, startYear, version)
dataFilename = '../input_spreadsheets/%s/2016Aug02/validation/Input_%s_%i_%s_LiST.xlsx'%(country, country, startYear, version)
inputData = data.readSpreadsheet(dataFilename, helper.keyList)
numAgeGroups = len(helper.keyList['ages'])
agePopSizes = [246307.75 , 1231538.75 , 1477846.50 , 2950860.00 , 8895211.00 ] #override


numsteps = 180

for intervention in inputData.interventionList:
    print "Baseline coverage of %s = %g"%(intervention,inputData.coverage[intervention])

plotData = []
run = 0

#------------------------------------------------------------------------    
# DEFAULT RUN WITH NO CHANGES TO INTERVENTIONS
nametag = "Baseline"
pickleFilename = '%s_Default_forLiST.pkl'%(country)
plotcolor = 'grey'

print "\n"+nametag
model, derived, params = helper.setupModelSpecificPopsizes(inputData, agePopSizes)

# file to dump objects into at each time step
outfile = open(pickleFilename, 'wb')

# Run model
for t in range(numsteps):
    model.moveOneTimeStep()
    pickle.dump(model, outfile)
outfile.close()    

# collect output, make graphs etc.
infile = open(pickleFilename, 'rb')
modelList = []
while 1:
    try:
        modelList.append(pickle.load(infile))
    except (EOFError):
        break
infile.close()

plotData.append({})
plotData[run]["modelList"] = modelList
plotData[run]["tag"] = nametag
plotData[run]["color"] = plotcolor
run += 1


#------------------------------------------------------------------------    
# INCREASE COVERAGE OF COMPLEMENTARY FEEDING
scenarios = [30, 50, 70]
for icov in range(len(scenarios)):
    CFcoverage = scenarios[icov]
    nametag = "Complementary feeding: %g%% coverage"%(CFcoverage)
    pickleFilename = '%s_CompFeed_P%i.pkl'%(country,CFcoverage)
    plotcolor = (0.1, 1.0-0.2*icov, 0.1)

    print "\n"+nametag
    modelCF, derived, params = helper.setupModelSpecificPopsizes(inputData, agePopSizes)

    # file to dump objects into at each time step
    outfile = open(pickleFilename, 'wb')

    # run for a year before
    timestepsPre = 12
    for t in range(timestepsPre):
        modelCF.moveOneTimeStep()
        pickle.dump(modelCF, outfile)

    # initialise
    newCoverages={}
    for intervention in inputData.interventionList:
        newCoverages[intervention] = inputData.coverage[intervention]
    # scale up
    for intervention in ['Complementary feeding (supplementation)','Complementary feeding (education)']:
        newCoverages[intervention] = CFcoverage/100.
    modelCF.updateCoverages(newCoverages)

    # Run model
    for t in range(numsteps-timestepsPre):
        modelCF.moveOneTimeStep()
        pickle.dump(modelCF, outfile)

    # done
    outfile.close()    

    # collect output, make graphs etc.
    infile = open(pickleFilename, 'rb')
    newModelList = []
    while 1:
        try:
            newModelList.append(pickle.load(infile))
        except (EOFError):
            break
    infile.close()

    plotData.append({})
    plotData[run]["modelList"] = newModelList
    plotData[run]["tag"] = nametag
    plotData[run]["color"] = plotcolor
    run += 1


#------------------------------------------------------------------------    
# INCREASE COVERAGE OF BREASTFEEDING
scenarios = [70, 80, 90]
for icov in range(len(scenarios)):
    BFcoverage = scenarios[icov]
    nametag = "Breastfeeding promotion: %g%% coverage"%(BFcoverage)
    pickleFilename = '%s_Breastfeed_P%i.pkl'%(country,BFcoverage)
    plotcolor = (0.1, 0.1, 1.0-0.2*icov)

    print "\n"+nametag
    modelBF, derived, params = helper.setupModelSpecificPopsizes(inputData, agePopSizes)

    # file to dump objects into at each time step
    outfile = open(pickleFilename, 'wb')

    # run for a year before
    timestepsPre = 12
    for t in range(timestepsPre):
        modelBF.moveOneTimeStep()
        pickle.dump(modelBF, outfile)

    # initialise
    newCoverages={}
    for intervention in inputData.interventionList:
        newCoverages[intervention] = inputData.coverage[intervention]

    # scale up
    for intervention in ['Breastfeeding promotion (dual delivery)']:
        newCoverages[intervention] = BFcoverage/100.
    modelBF.updateCoverages(newCoverages)

    # Run model
    for t in range(numsteps-timestepsPre):
        modelBF.moveOneTimeStep()
        pickle.dump(modelBF, outfile)

    # done
    outfile.close()    

    # collect output, make graphs etc.
    infile = open(pickleFilename, 'rb')
    newModelList = []
    while 1:
        try:
            newModelList.append(pickle.load(infile))
        except (EOFError):
            break
    infile.close()

    plotData.append({})
    plotData[run]["modelList"] = newModelList
    plotData[run]["tag"] = nametag
    plotData[run]["color"] = plotcolor
    run += 1



#------------------------------------------------------------------------    
# INCREASE COVERAGE OF BREASTFEEDING AND COMPLEMENTARY FEEDING
BFcoverage = 80
CFcoverage = 30
nametag = "Scale up Breastfeeding promotion to %g%% and Complementary feeding to %g%%"%(BFcoverage,CFcoverage)
pickleFilename = '%s_BF%i_CF%i.pkl'%(country,BFcoverage,CFcoverage)
plotcolor = (0.7, 0.1, 0.1)

print "\n"+nametag
modelBC, derived, params = helper.setupModelSpecificPopsizes(inputData, agePopSizes)

# file to dump objects into at each time step
outfile = open(pickleFilename, 'wb')

# run for a year before
timestepsPre = 12
for t in range(timestepsPre):
    modelBC.moveOneTimeStep()
    pickle.dump(modelBC, outfile)

# initialise
newCoverages={}
for intervention in inputData.interventionList:
    newCoverages[intervention] = inputData.coverage[intervention]

# scale up
for intervention in ['Breastfeeding promotion (dual delivery)']:
    newCoverages[intervention] = BFcoverage/100.
for intervention in ['Complementary feeding (supplementation)','Complementary feeding (education)']:
    newCoverages[intervention] = CFcoverage/100.
modelBC.updateCoverages(newCoverages)

# Run model
for t in range(numsteps-timestepsPre):
    modelBC.moveOneTimeStep()
    pickle.dump(modelBC, outfile)

# done
outfile.close()    

# collect output, make graphs etc.
infile = open(pickleFilename, 'rb')
newModelList = []
while 1:
    try:
        newModelList.append(pickle.load(infile))
    except (EOFError):
        break
infile.close()

plotData.append({})
plotData[run]["modelList"] = newModelList
plotData[run]["tag"] = nametag
plotData[run]["color"] = plotcolor
run += 1

#------------------------------------------------------------------------    




