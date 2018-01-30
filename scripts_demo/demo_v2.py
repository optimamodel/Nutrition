import setup
from copy import deepcopy as dcp

root = '../'
filePath = setup.getFilePath(root=root, bookDate='2017Nov', country='Bangladesh')
model = setup.setUpModel(filePath)

def runModelGivenCoverage(model, program, coverage, zeroCovs):
    thisModel = dcp(model)
    theseCovs = dcp(zeroCovs)
    thisModel.moveModelOneYear()

    if program is None:
        pass
    else:
        theseCovs[program] = coverage
        for prog in model.programInfo.programs:
            if prog.malariaTwin: # forces them to be scaled up together
                theseCovs[program + ' (malaria area)'] = coverage
    thisModel.applyNewProgramCoverages(theseCovs)



    for t in range(13):
        thisModel.moveModelOneYear()
    return thisModel

fixedProgs = ['WASH: Handwashing','WASH: Hygenic disposal', 'WASH: Improved sanitation','WASH: Improved water source',
 'WASH: Piped water', 'Long-lasting insecticide-treated bednets', 'Family Planning', 'IPTp']
coverage95 = 0.95
referenceCovs = {}
for prog, cov in model.programInfo.baselineCovs.iteritems():
    if prog in fixedProgs:
        referenceCovs[prog] = cov
    else:
        referenceCovs[prog] = 0.

outcomes = ['thrive', 'stunting_prev', 'deaths_children', 'deaths_PW',
            'total_deaths', 'anaemia_prev_PW', 'anaemia_prev_WRA', 'anaemia_prev_children',
            'wasting_prev']

# REFERENCE (ALL 0)
reference = []
reference.append('Reference')
reference.append('')
referenceModel = runModelGivenCoverage(model, None, 0, referenceCovs)
for outcome in outcomes:
    reference.append(referenceModel.getOutcome(outcome))

# 95% ONE AT A TIME
output = {}
for program in referenceCovs.iterkeys():
    if 'malaria' not in program:
        output[program] = []
        newModel = runModelGivenCoverage(model, program, coverage95, referenceCovs)
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









