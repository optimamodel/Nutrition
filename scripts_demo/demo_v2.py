import setup
from copy import deepcopy as dcp

root = '../'
filePath = setup.getFilePath(root=root, bookDate='2017Nov', country='Bangladesh')
model = setup.setUpModel(filePath)

def runModelGivenCoverage(model, program, coverage, zeroCovs):
    """ Runs the model with program set at coverage, the rest at 0"""
    # TODO: currently not accounting for threshold dependencies
    thisModel = dcp(model)
    theseCovs = dcp(zeroCovs)
    thisModel.moveModelOneYear()

    if program is None:
        pass
    else:
        theseCovs[program] = coverage
    thisModel.applyNewProgramCoverages(theseCovs)

    for t in range(13):
        thisModel.moveModelOneYear()
    return thisModel


coverage95 = 0.95
zeroCovs = {prog: 0 for prog in model.programInfo.baselineCovs}
outcomes = ['thrive', 'stunting_prev', 'deaths_children', 'deaths_PW',
            'total_deaths', 'anaemia_prev_PW', 'anaemia_prev_WRA', 'anaemia_prev_children',
            'wasting_prev']

# REFERENCE (ALL 0)
reference = []
reference.append('Reference')
reference.append('all_zero')
referenceModel = runModelGivenCoverage(model, None, 0, zeroCovs)
for outcome in outcomes:
    reference.append(referenceModel.getOutcome(outcome))

# 95% ONE AT A TIME
output = {}
for program in zeroCovs.iterkeys():
    output[program] = []
    newModel = runModelGivenCoverage(model, program, coverage95, zeroCovs)
    for prog in newModel.programInfo.programs:  # get unres coverage
        if prog.name == program:
            resCov = prog.proposedCoverageFrac
    output[program].append(resCov)
    for outcome in outcomes:
        output[program].append(newModel.getOutcome(outcome))

header = ['scenario', 'unrestricted_cov'] + outcomes
import csv
with open('demo_v2_newCovDef.csv', 'wb') as f:
    w = csv.writer(f)
    w.writerow(header)
    w.writerow(reference)
    for program, outcomes in sorted(output.iteritems()):
        w.writerow([program] + outcomes)









