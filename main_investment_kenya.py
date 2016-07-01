# -*- coding: utf-8 -*-
"""
Created on Wed Jun 01 2016

@author: madhurakilledar
"""
from __future__ import division

import data as dataCode
import helper as helper
import output as output
from copy import deepcopy as dcp
import pickle as pickle
import costcov
from numpy import array

country = 'Kenya'
startYear = 2016

helper = helper.Helper()
costCov = costcov.Costcov()
ages = ["<1 month", "1-5 months", "6-11 months", "12-23 months", "24-59 months"]
birthOutcomes = ["Pre-term SGA", "Pre-term AGA", "Term SGA", "Term AGA"]
wastingList = ["normal", "mild", "moderate", "high"]
stuntingList = ["normal", "mild", "moderate", "high"]
breastfeedingList = ["exclusive", "predominant", "partial", "none"]
keyList = [ages, birthOutcomes, wastingList, stuntingList, breastfeedingList]

dataFilename = 'InputForCode_%s.xlsx'%(country)
spreadsheetData = dataCode.getDataFromSpreadsheet(dataFilename, keyList)
mothers = helper.makePregnantWomen(spreadsheetData)
mothers['annualPercentPopGrowth'] = 0.03
ageGroupSpans = [1., 5., 6., 12., 36.] # number of months in each age group
agingRateList = [1./1., 1./5., 1./6., 1./12., 1./36.] # fraction of people aging out per MONTH
numAgeGroups = len(ages)
agePopSizes  = helper.makeAgePopSizes(numAgeGroups, ageGroupSpans, spreadsheetData)

timestep = 1./12. 
numsteps = 180
timespan = timestep * float(numsteps)

for intervention in spreadsheetData.interventionList:
    print "Baseline coverage of %s = %g"%(intervention,spreadsheetData.interventionCoveragesCurrent[intervention])

plotData = []
run = 0

#------------------------------------------------------------------------    
# DEFAULT RUN WITH NO CHANGES TO INTERVENTIONS
nametag = "Baseline"
pickleFilename = '%s_Default.pkl'%(country)
plotcolor = 'grey'

print "\n"+nametag
model, constants, params = helper.setupModelConstantsParameters(nametag, mothers, timestep, agingRateList, agePopSizes, keyList, spreadsheetData)

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
# INTERVENTION
investmentIncrease = 1.e6  # 1 million BDT per intervention per year for the full 14 years
title = '%s: 2015-2030 \n Scale up intervention by %i million BDT per year'%(country,investmentIncrease/1e6)
print title

for ichoose in range(len(spreadsheetData.interventionList)):
    chosenIntervention = spreadsheetData.interventionList[ichoose]
    nametag = chosenIntervention
    pickleFilename = '%s_Intervention%i_Invest.pkl'%(country,ichoose)
    plotcolor = (1.0-0.13*run, 1.0-0.3*abs(run-4), 0.0+0.13*run)
    print "\n %s: increase investment by BDT %g"%(nametag,investmentIncrease)

    modelX, constants, params = helper.setupModelConstantsParameters(nametag, mothers, timestep, agingRateList, agePopSizes, keyList, spreadsheetData)

    # file to dump objects into at each time step
    outfile = open(pickleFilename, 'wb')
    modelX.moveOneTimeStep()
    pickle.dump(modelX, outfile)

    # initialise
    newCoverages={}
    for intervention in spreadsheetData.interventionList:
        newCoverages[intervention] = spreadsheetData.interventionCoveragesCurrent[intervention]
    # allocation of funding
    investment = array([investmentIncrease])
    # calculate coverage (%)
    targetPopSize = {}
    targetPopSize[chosenIntervention] = 0.
    for iAge in range(numAgeGroups):
        ageName = ages[iAge]
        targetPopSize[chosenIntervention] += spreadsheetData.interventionTargetPop[chosenIntervention][ageName] * modelX.listOfAgeCompartments[iAge].getTotalPopulation()
    targetPopSize[chosenIntervention] +=     spreadsheetData.interventionTargetPop[chosenIntervention]['pregnant women'] * modelX.fertileWomen.populationSize
    costCovParams = {}
    costCovParams['unitcost']   = array([dcp(spreadsheetData.interventionCostCoverage[chosenIntervention]["unit cost"])])
    costCovParams['saturation'] = array([dcp(spreadsheetData.interventionCostCoverage[chosenIntervention]["saturation coverage"])])
    additionalPeopleCovered   = costCov.function(investment, costCovParams, targetPopSize[chosenIntervention]) # function from HIV
    additionalFractionCovered = additionalPeopleCovered / targetPopSize[chosenIntervention]
    print "additional coverage: %g"%(additionalFractionCovered)
    newCoverages[chosenIntervention] += additionalFractionCovered
    print "new coverage: %g"%(newCoverages[chosenIntervention])
    # scale up intervention
    modelX.updateCoverages(newCoverages)

    # Run model
    for t in range(numsteps-1):
        modelX.moveOneTimeStep()
        pickle.dump(modelX, outfile)
    outfile.close()    

    # collect output, make graphs etc.
    infile = open(pickleFilename, 'rb')
    modelXList = []
    while 1:
        try:
            modelXList.append(pickle.load(infile))
        except (EOFError):
            break
    infile.close()

    plotData.append({})
    plotData[run]["modelList"] = modelXList
    plotData[run]["tag"] = nametag
    plotData[run]["color"] = plotcolor
    run += 1


#------------------------------------------------------------------------    

filenamePrefix = '%s_fixedInvest'%(country)

output.getCombinedPlots(run, plotData, startYear=startYear-1, filenamePrefix=filenamePrefix, save=True)
output.getCompareDeathsAverted(run, plotData, scalePercent=0.1, filenamePrefix=filenamePrefix, title=title, save=True)
output.getU5StuntingCasesAverted(run, plotData, scalePercent=0.5, filenamePrefix=filenamePrefix, title=title, save=True)
output.getA5StuntingCasesAverted(run, plotData, scalePercent=0.5, filenamePrefix=filenamePrefix, title=title, save=True)



