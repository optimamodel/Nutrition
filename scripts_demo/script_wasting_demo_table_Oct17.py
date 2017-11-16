rootpath = '../'

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)

import data
from copy import deepcopy as dcp
import helper
helper = helper.Helper()

date = '16_11_17'

def runModelGivenCoverage(intervention, coverage, spreadsheetData, zeroCoverages):
    interventionsCombine = ['Public provision of complementary foods with iron', 'Sprinkles', 'Multiple micronutrient supplementation', 'Iron and folic acid supplementation for pregnant women']
    numModelSteps = 14
    model, derived, params = helper.setupModelDerivedParameters(spreadsheetData)

    # run the model for one year before updating coverages
    timestepsPre = 1
    for t in range(timestepsPre):
        model.moveModelOneYear()
    # set coverage
    theseCoverages = dcp(zeroCoverages)
    theseCoverages[intervention] = coverage
    # scale up IPTp only if MMS
    if "Multiple micro" in intervention:
        theseCoverages['IPTp'] = 0.1
    # scale up bednets only if IFAS in malaria area
    if ("IFAS" in intervention) and ("malaria" in intervention):
        theseCoverages['Long-lasting insecticide-treated bednets'] = 0.1
    # scale up malaria area part of IFAS interventions also
    if 'IFAS' in intervention:
        interventionMalaria = intervention + ' (malaria area)'
        theseCoverages[interventionMalaria] = coverage
    if 'IFAS' in intervention and 'retailer' not in intervention:
        if 'poor' in intervention:
            interventionNotPoor = intervention.replace('poor', 'not poor')
            interventionNotPoorMalaria = interventionNotPoor + ' (malaria area)'
            theseCoverages[interventionNotPoor] = coverage
            theseCoverages[interventionNotPoorMalaria] = coverage
    if any(this in intervention for this in interventionsCombine):
            interventionMalaria = intervention + ' (malaria area)'
            theseCoverages[interventionMalaria] = coverage
    # update coverages after 1 year
    model.updateCoverages(theseCoverages)
    # run the model for the remaining timesteps
    for t in range(numModelSteps - timestepsPre):
        model.moveModelOneYear()
    # return outcome
    return model

spreadsheet = rootpath + 'input_spreadsheets/Bangladesh/2017Oct/InputForCode_Bangladesh.xlsx'
spreadsheetData = data.readSpreadsheet(spreadsheet, helper.keyList)

zeroCoverages = {intervention:0. for intervention in spreadsheetData.interventionList}

# set bed nets and IPTp coverage to malaria prevalence so that constraints are met for certain interventions
coverage95 = 0.95

baseline = []
baseline.append('Baseline')
numModelSteps = 14
model = runModelGivenCoverage('IPTp', 0.0, spreadsheetData, zeroCoverages)
baseline.append(model.getOutcome('thrive'))
baseline.append(model.getOutcome('deaths children'))
baseline.append(model.getOutcome('deaths PW'))
baseline.append(model.getOutcome('anemia frac pregnant'))
baseline.append(model.getOutcome('anemia frac WRA'))
baseline.append(model.getOutcome('anemia frac children'))
baseline.append(model.getOutcome('wasting_prev'))
baseline.append(model.getOutcome('MAM_prev'))
baseline.append(model.getOutcome('SAM_prev'))
baseline.append(model.getOutcome('stunting prev'))

# EVERYTHING ELSE
interventionsCombine = ['Public provision of complementary foods with iron', 'Sprinkles',
                        'Multiple micronutrient supplementation',
                        'Iron and folic acid supplementation for pregnant women']
output = {}
for intervention in spreadsheetData.interventionList:
    # combining IFAS interventions in malaria and non-malaria areas, poor and not-poor
    if 'IFAS' in intervention and 'malaria area' in intervention:
        continue
    if 'IFAS' in intervention and 'retailer' not in intervention:
        if 'not poor' in intervention:
            continue
    if any(this in intervention for this in interventionsCombine) and 'malaria area' in intervention:
        continue
    output[intervention] = []
    output[intervention].append(intervention)
    model = runModelGivenCoverage(intervention, coverage95, spreadsheetData, zeroCoverages)
    output[intervention].append(model.getOutcome('thrive'))
    output[intervention].append(model.getOutcome('deaths children'))
    output[intervention].append(model.getOutcome('deaths PW'))
    output[intervention].append(model.getOutcome('anemia frac pregnant'))
    output[intervention].append(model.getOutcome('anemia frac WRA'))
    output[intervention].append(model.getOutcome('anemia frac children'))
    output[intervention].append(model.getOutcome('wasting_prev'))
    output[intervention].append(model.getOutcome('MAM_prev'))
    output[intervention].append(model.getOutcome('SAM_prev'))
    output[intervention].append(model.getOutcome('stunting prev'))
# ALL IFAS INTERVENTIONS AT 95%
allIFAS = []
allIFAS.append('all IFAS WRA')
coverage = dcp(zeroCoverages)
for intervention in spreadsheetData.interventionList:
    if 'IFAS' in intervention:
        coverage[intervention] = coverage95
model, derived, params = helper.setupModelDerivedParameters(spreadsheetData)
model.moveModelOneYear()
model.updateCoverages(coverage)
for t in range(numModelSteps - 1):
    model.moveModelOneYear()
allIFAS.append(model.getOutcome('thrive'))
allIFAS.append(model.getOutcome('deaths children'))
allIFAS.append(model.getOutcome('deaths PW'))
allIFAS.append(model.getOutcome('anemia frac pregnant'))
allIFAS.append(model.getOutcome('anemia frac WRA'))
allIFAS.append(model.getOutcome('anemia frac children'))
allIFAS.append(model.getOutcome('wasting_prev'))
allIFAS.append(model.getOutcome('MAM_prev'))
allIFAS.append(model.getOutcome('SAM_prev'))
allIFAS.append(model.getOutcome('stunting prev'))


# ALL FORTIFICATION INTERVENTIONS AT 95%
allfoodFort = []
allfoodFort.append('all food fortification')
coverage = dcp(zeroCoverages)
for intervention in spreadsheetData.interventionList:
    if 'fortification' in intervention:
        coverage[intervention] = coverage95
numModelSteps = 14
model, derived, params = helper.setupModelDerivedParameters(spreadsheetData)
model.moveModelOneYear()
model.updateCoverages(coverage)
for t in range(numModelSteps - 1):
    model.moveModelOneYear()
allfoodFort.append(model.getOutcome('thrive'))
allfoodFort.append(model.getOutcome('deaths children'))
allfoodFort.append(model.getOutcome('deaths PW'))
allfoodFort.append(model.getOutcome('anemia frac pregnant'))
allfoodFort.append(model.getOutcome('anemia frac WRA'))
allfoodFort.append(model.getOutcome('anemia frac children'))
allfoodFort.append(model.getOutcome('wasting_prev'))
allfoodFort.append(model.getOutcome('MAM_prev'))
allfoodFort.append(model.getOutcome('SAM_prev'))
allfoodFort.append(model.getOutcome('stunting prev'))

# ALL WASTING TREATMENTS
allTreatment = []
allTreatment.append('all wasting treatments')
coverage = dcp(zeroCoverages)
for intervention in spreadsheetData.interventionList:
    if 'Treatment' in intervention:
        coverage[intervention] = coverage95
numModelSteps= 14
model, _, _ = helper.setupModelDerivedParameters(spreadsheetData)
model.moveModelOneYear()
model.updateCoverages(coverage)
for t in range(numModelSteps - 1):
    model.moveModelOneYear()
allTreatment.append(model.getOutcome('thrive'))
allTreatment.append(model.getOutcome('deaths children'))
allTreatment.append(model.getOutcome('deaths PW'))
allTreatment.append(model.getOutcome('anemia frac pregnant'))
allTreatment.append(model.getOutcome('anemia frac WRA'))
allTreatment.append(model.getOutcome('anemia frac children'))
allTreatment.append(model.getOutcome('wasting_prev'))
allTreatment.append(model.getOutcome('MAM_prev'))
allTreatment.append(model.getOutcome('SAM_prev'))
allTreatment.append(model.getOutcome('stunting prev'))

# ALL IFA FORTIFICATION
allIFA = []
allIFA.append('all IFA fortification')
coverage = dcp(zeroCoverages)
for intervention in spreadsheetData.interventionList:
    if 'IFA fortification' in intervention:
        coverage[intervention] = coverage95
numModelSteps= 14
model, _, _ = helper.setupModelDerivedParameters(spreadsheetData)
model.moveModelOneYear()
model.updateCoverages(coverage)
for t in range(numModelSteps - 1):
    model.moveModelOneYear()
allIFA.append(model.getOutcome('thrive'))
allIFA.append(model.getOutcome('deaths children'))
allIFA.append(model.getOutcome('deaths PW'))
allIFA.append(model.getOutcome('anemia frac pregnant'))
allIFA.append(model.getOutcome('anemia frac WRA'))
allIFA.append(model.getOutcome('anemia frac children'))
allIFA.append(model.getOutcome('wasting_prev'))
allIFA.append(model.getOutcome('MAM_prev'))
allIFA.append(model.getOutcome('SAM_prev'))
allIFA.append(model.getOutcome('stunting prev'))

# ALL IRON FORTIFICATION
allIron = []
allIron.append('all iron fortification')
coverage = dcp(zeroCoverages)
for intervention in spreadsheetData.interventionList:
    if 'Iron fortification' in intervention:
        coverage[intervention] = coverage95
numModelSteps= 14
model, _, _ = helper.setupModelDerivedParameters(spreadsheetData)
model.moveModelOneYear()
model.updateCoverages(coverage)
for t in range(numModelSteps - 1):
    model.moveModelOneYear()
allIron.append(model.getOutcome('thrive'))
allIron.append(model.getOutcome('deaths children'))
allIron.append(model.getOutcome('deaths PW'))
allIron.append(model.getOutcome('anemia frac pregnant'))
allIron.append(model.getOutcome('anemia frac WRA'))
allIron.append(model.getOutcome('anemia frac children'))
allIron.append(model.getOutcome('wasting_prev'))
allIron.append(model.getOutcome('MAM_prev'))
allIron.append(model.getOutcome('SAM_prev'))
allIron.append(model.getOutcome('stunting prev'))

# scaling-up treatment of MAM/SAM incrementally and look at reduction in SAM prev
coverages = dcp(zeroCoverages)
coverageList = [0., 0.2, 0.4, 0.6, 0.8]

MAMtreatment = {}
SAMtreatment = {}
for covValue in coverageList:
    # MAM
    thisName = 'Treatment of MAM ' + str(covValue * 100) + '%'
    MAMmodel = runModelGivenCoverage('Treatment of MAM', covValue, spreadsheetData, zeroCoverages)
    tmp = [thisName, MAMmodel.getOutcome('thrive'), MAMmodel.getOutcome('deaths children'), MAMmodel.getOutcome('deaths PW'), MAMmodel.getOutcome('anemia frac pregnant'),
           MAMmodel.getOutcome('anemia frac WRA'), MAMmodel.getOutcome('anemia frac children'), MAMmodel.getOutcome('wasting_prev'), MAMmodel.getOutcome('MAM_prev'),
           MAMmodel.getOutcome('SAM_prev'), MAMmodel.getOutcome('stunting prev')]
    MAMtreatment[covValue] = tmp
    # SAM
    thisName = 'Treatment of SAM ' + str(covValue * 100) + '%'
    SAMmodel = runModelGivenCoverage('Treatment of SAM', covValue, spreadsheetData, zeroCoverages)
    tmp = [thisName, SAMmodel.getOutcome('thrive'), SAMmodel.getOutcome('deaths children'), SAMmodel.getOutcome('deaths PW'),
           SAMmodel.getOutcome('anemia frac pregnant'),
           SAMmodel.getOutcome('anemia frac WRA'), SAMmodel.getOutcome('anemia frac children'),
           SAMmodel.getOutcome('wasting_prev'), SAMmodel.getOutcome('MAM_prev'),
           SAMmodel.getOutcome('SAM_prev'), SAMmodel.getOutcome('stunting prev')]
    SAMtreatment[covValue] = tmp



# WRITE TO CSV
header = ['scenario', 'thrive', 'deaths children', 'deaths PW', 'anemia prev PW', 'anemia prev WRA',
          'anemia prev children', 'wasted prev children','MAM prev', 'SAM prev', 'stunting prev children']
import csv

outfilename = 'anemiaWithWasting_' + date +'.csv'
with open(outfilename, "wb") as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerow(baseline)
    for intervention in spreadsheetData.interventionList:
        if 'IFAS' in intervention and 'malaria area' in intervention:
            continue
        if 'IFAS' and 'retailer' not in intervention:
            if 'not poor' in intervention:
                continue
        if any(this in intervention for this in interventionsCombine) and 'malaria area' in intervention:
            continue
        writer.writerow(output[intervention])
    writer.writerow(allIFAS)
    writer.writerow(allfoodFort)
    writer.writerow(allTreatment)
    writer.writerow(allIFA)
    writer.writerow(allIron)
    for covValue in coverageList:
        thisMAMcov = MAMtreatment[covValue]
        thisSAMcov = SAMtreatment[covValue]
        writer.writerow(thisMAMcov)
        writer.writerow(thisSAMcov)




