import setup
from copy import deepcopy as dcp

root = '../'
filePath = setup.getFilePath(root=root, bookDate='2017Nov', country='Bangladesh')[0]
model = setup.setUpModel(filePath, adjustCoverage=False) # already run a year

fixedProgs = model.constants.referencePrograms
coverage95 = 0.95

referenceCovs = {}
for prog in model.programInfo.programs:
    if prog.name in fixedProgs:
        cov = prog.restrictedBaselineCov
        referenceCovs[prog.name] = cov
    else:
        referenceCovs[prog.name] = 0

outcomes = ['thrive', 'stunting_prev', 'deaths_children', 'deaths_PW',
            'total_deaths', 'anaemia_prev_PW', 'anaemia_prev_WRA', 'anaemia_prev_children',
            'wasting_prev']

# REFERENCE (ALL 0)
reference = []
reference.append('Reference')
reference.append('')
refModel = dcp(model)
refModel.runSimulationGivenCoverage(referenceCovs, True)
for outcome in outcomes:
    reference.append(refModel.getOutcome(outcome))

# 95% ONE AT A TIME
output = {}
# TODO: does not scale-up malaria area simultaneously
for programName in model.constants.programList:
    if 'malaria' not in programName:
        output[programName] = []
        newModel = dcp(model)
        newCov = dcp(referenceCovs)
        newCov[programName] = 0.95
        newCov[programName + ' (malaria area)'] = 0.95
        newModel.runSimulationGivenCoverage(newCov, True)
        unrestrictedCov = 0
        for prog in newModel.programInfo.programs:
            if prog.name == programName or prog.name == programName + ' (malaria area)':
                unrestrictedCov += prog.annualCoverage[newModel.constants.simulationYears[0]]
        output[programName].append(unrestrictedCov)
        for outcome in outcomes:
            output[programName].append(newModel.getOutcome(outcome))

header = ['scenario', 'unrestricted_cov'] + outcomes
import csv
with open('demo_v2_timecov.csv', 'wb') as f:
    w = csv.writer(f)
    w.writerow(header)
    w.writerow(reference)
    for program, outcomes in sorted(output.iteritems()):
        w.writerow([program] + outcomes)








#
