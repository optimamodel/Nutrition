# scale-up wasting treatment coverage by increments, look at relative reduction in SAM prev as well as mortality
# compare with ref case

import setup
from copy import deepcopy as dcp
import csv

filePath = setup.getFilePath('../', '2017Nov', 'Bangladesh')[0]
model = setup.setUpModel(filePath)

refCovs = {prog.name:prog.unrestrictedBaselineCov for prog in model.programInfo.programs if prog.name in model.programInfo.referencePrograms}
refCovs.update({prog.name:0 for prog in model.programInfo.programs if prog.name not in model.programInfo.referencePrograms})

wastingTreatments = ['Treatment of SAM', 'Treatment of MAM']
increments = [0, 0.2, 0.4, 0.6, 0.8]
outcomes = ['SAM_prev', 'deaths_children']

output = {}
output['reference'] = {}
# refCase
refModel = dcp(model)
refModel.runSimulationGivenCoverage(refCovs, True)
output['reference']['ref'] = []
for outcome in outcomes:
    output['reference']['ref'].append(refModel.getOutcome(outcome))

for treatment in wastingTreatments:
    output[treatment] = {}
    for increment in increments:
        output[treatment][increment] = []
        thisCov = dcp(refCovs)
        thisModel = dcp(model)
        thisCov[treatment] = increment
        thisModel.runSimulationGivenCoverage(thisCov, True)
        for outcome in outcomes:
            output[treatment][increment].append(thisModel.getOutcome(outcome))

header = ['scenario', 'cov'] + outcomes
with open('wastingTreatments.csv', 'wb') as f:
    w = csv.writer(f)
    w.writerow(header)
    for program, covOutcomes in sorted(output.iteritems()):
        w.writerow([program])
        for cov, outcomes in sorted(covOutcomes.iteritems()):
            w.writerow(['',cov] + outcomes)










