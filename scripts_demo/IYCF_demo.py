rootpath = '../'

import os, sys
moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)

from nutrition import data
from copy import deepcopy as dcp
from old_files import helper

helper = helper.Helper()

date = '05_12_17'

# THE IYCF PACKAGE WHICH IS VERY SIMILAR TO BFP + CFE IN OLD MODEL IS:
# PW Community
# <1month Community
# 1-5 months HF
# 6-11 months HF
# 12-23 months HF
# Mass media


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



spreadsheet = rootpath + 'input_spreadsheets/Bangladesh/2017Nov/InputForCode_Bangladesh.xlsx'
spreadsheetData = data.readSpreadsheet(spreadsheet, helper.keyList)

zeroCoverages = {intervention:0. for intervention in spreadsheetData.interventionList}
outcomes = ['thrive', 'deaths children', 'deaths PW', 'anemia frac pregnant', 'anemia frac WRA', 'anemia frac children',
            'wasting_prev', 'MAM_prev', 'SAM_prev', 'stunting prev']
# baseline
# set bed nets and IPTp coverage to malaria prevalence so that constraints are met for certain interventions
coverage95 = 0.95

# EVERYTHING AT 0
baseline = []
baseline.append('Baseline')
numModelSteps = 14
model = runModelGivenCoverage('IPTp', 0.0, spreadsheetData, zeroCoverages)
for outcome in outcomes:
    baseline.append(model.getOutcome(outcome))

# Scale-up each IYCF program separately
output = {}
for program in spreadsheetData.IYCFprograms:
    model = runModelGivenCoverage(program, coverage95, spreadsheetData, zeroCoverages)
    output[program] = []
    for outcome in outcomes:
        output[program].append(model.getOutcome(outcome))

# WRITE TO CSV
header = ['scenario', 'thrive', 'deaths children', 'deaths PW', 'anemia prev PW', 'anemia prev WRA',
          'anemia prev children', 'wasted prev children','MAM prev', 'SAM prev', 'stunting prev children']
import csv
with open('IYCF.csv', 'wb') as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerow(baseline)
    for program, outcomes in output.items():
        writer.writerow([program] + outcomes)














