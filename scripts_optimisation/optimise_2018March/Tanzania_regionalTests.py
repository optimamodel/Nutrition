# producing table of outputs for each region to test sensibility of results
import play
from copy import deepcopy as dcp
import csv

root = '../..'

regions = ['Arusha', 'Dar_es_Salaam', 'Dodoma', 'Kaskazini_Pemba', 'Kaskazini_Unguja', 'Katavi',
           'Kilimanjaro', 'Kusini_Pemba', 'Kusini_Unguja', 'Lindi', 'Manyara', 'Mara', 'Mjini_Magharibi',
           'Morogoro', 'Mtwara', 'Pwani', 'Rukwa', 'Ruvuma', 'Simiyu', 'Singida', 'Tabora', 'Tanga']

outcomes = ['healthy_children', 'thrive', 'stunting_prev', 'neonatal_deaths', 'deaths_children', 'deaths_PW',
            'total_deaths', 'mortality_rate', 'anaemia_prev_PW', 'anaemia_prev_WRA', 'anaemia_prev_children',
            'wasting_prev', 'SAM_prev', 'MAM_prev']
filename = 'demo_v2_TanzaniaRegions.csv'

with open(filename, 'wb') as f:
    pass

for region in regions:
    print " "
    print region
    filePath = play.getFilePath(root=root, country='Tanzania/regions', name=region)
    model = play.setUpModel(filePath, adjustCoverage=False, numYears=6) # already run a year

    fixedProgs = model.constants.referencePrograms
    coverage95 = 0.95
    allMalariaArea = True

    referenceCovs = {}
    for prog in model.programInfo.programs:
        if prog.name in fixedProgs:
            cov = prog.restrictedBaselineCov
            referenceCovs[prog.name] = cov
        else:
            referenceCovs[prog.name] = 0

    suffix = ' (malaria area)'

    # REFERENCE (ALL 0)
    reference = []
    reference.append('Reference')
    reference.append('')
    refModel = dcp(model)
    refModel.runSimulationGivenCoverage(referenceCovs, True)
    for outcome in outcomes:
        reference.append(refModel.getOutcome(outcome))
    print " "

    # 95% ONE AT A TIME
    output = {}
    for programName in model.constants.programList:
        if allMalariaArea:  # to deal with case when malaria area is 100% and cannot include those programs outside a malaria area
            output[programName] = []
            newModel = dcp(model)
            newCov = dcp(referenceCovs)
            newCov[programName] = 0.95
            newModel.runSimulationGivenCoverage(newCov, True)
            unrestrictedCov = 0
            for prog in newModel.programInfo.programs:
                if prog.name == programName:
                    unrestrictedCov += prog.annualCoverage[newModel.constants.simulationYears[0]]
            output[programName].append(unrestrictedCov)
            for outcome in outcomes:
                output[programName].append(newModel.getOutcome(outcome))
        elif 'malaria' not in programName:
            output[programName] = []
            newModel = dcp(model)
            newCov = dcp(referenceCovs)
            newCov[programName] = 0.95
            newCov[programName + suffix] = 0.95
            newModel.runSimulationGivenCoverage(newCov, True)
            unrestrictedCov = 0
            for prog in newModel.programInfo.programs:
                if prog.name == programName or prog.name == programName + suffix:
                    unrestrictedCov += prog.annualCoverage[newModel.constants.simulationYears[0]]
            output[programName].append(unrestrictedCov)
            for outcome in outcomes:
                output[programName].append(newModel.getOutcome(outcome))

    header = ['scenario', 'unrestricted_cov'] + outcomes

    with open(filename, 'a') as f:
        w = csv.writer(f)
        w.writerow([region])
        w.writerow(header)
        w.writerow(reference)
        for program, results in sorted(output.iteritems()):
            w.writerow([program] + results)
        w.writerow([])






