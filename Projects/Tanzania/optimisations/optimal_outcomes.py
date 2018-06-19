# output the outcomes that correspond to the optimal outcomes
import os, sys
root = os.pardir
moduleDir = os.path.join(os.path.dirname(__file__), root)
sys.path.append(moduleDir)
import pickle
from nutrition import optimisation as optim
import csv

regions = ['Arusha', 'Dar_es_Salaam', 'Dodoma', 'Kaskazini_Pemba', 'Kaskazini_Unguja', 'Katavi',
           'Kilimanjaro', 'Kusini_Pemba', 'Kusini_Unguja', 'Lindi', 'Manyara', 'Mara', 'Mjini_Magharibi',
           'Morogoro', 'Mtwara', 'Pwani', 'Rukwa', 'Ruvuma', 'Simiyu', 'Singida', 'Tabora', 'Tanga']

date = '2018May07'
scenarios = ['optimisedCurrent', 'additionalPerCapita', 'scenario1', 'scenario3']
objectives = ['thrive_notanaemic']
outcomes = ['thrive_notanaemic', 'healthy_children', 'thrive', 'stunting_prev', 'total_stunted', 'wasting_prev', 'anaemia_prev_children', 'deaths_children',
            'neonatal_deaths', 'child_population']

# first optimised current and additional per capita
with open('optimised_outputs.csv', 'wb') as f:
    w = csv.writer(f)
    # current
    w.writerow(['Current'] + outcomes)
    for region in regions:
        thisRegion = optim.Optimisation(['dummy'], [1], [root, 'regional', region, ''], numYears=6)
        currentOutputs = []
        allocationsDict = thisRegion.createDictionary(thisRegion.currentAllocations)
        thisModel = thisRegion.oneModelRunWithOutput(allocationsDict)
        for outcome in outcomes[:-1]:
            currentOutputs.append(thisModel.getOutcome(outcome))
        population = thisModel.children.getTotalPopulation()
        w.writerow([region] + currentOutputs + [population])
    w.writerow([])

    for objective in objectives:
        # first 2 scenarios
        for scenario in scenarios[:2]:
            w.writerow([objective])
            w.writerow([scenario])
            w.writerow(['Region'] + outcomes)
            for region in regions:
                thisRegion = optim.Optimisation([objective], [1], [root, 'regional', region, ''], numYears=6)
                thisPickle = 'results/{}/regional/{}/{}_{}_1.pkl'.format(date, scenario, region, objective)
                infile = open(thisPickle, 'rb')
                thisAllocation = pickle.load(infile)
                infile.close()
                optimalOutputs = []
                thisModel = thisRegion.oneModelRunWithOutput(thisAllocation)
                for outcome in outcomes[:-1]:
                    optimalOutputs.append(thisModel.getOutcome(outcome))
                population = thisModel.children.getTotalPopulation()
                w.writerow([region] + optimalOutputs + [population])
            w.writerow([])

        # second 2 optimisations
        for scenario in scenarios[2:]:
            w.writerow([objective])
            w.writerow([scenario])
            w.writerow(['Region'] + outcomes)
            for region in regions:
                thisRegion = optim.Optimisation([objective], [1], [root, 'regional', region, ''], numYears=6)
                thisPickle = 'results/{}/regional/{}/32m/pickles/{}_{}_1.pkl'.format(date, scenario, region, objective)
                infile = open(thisPickle, 'rb')
                thisAllocation = pickle.load(infile)
                infile.close()
                optimalOutputs = []
                thisModel = thisRegion.oneModelRunWithOutput(thisAllocation)
                for outcome in outcomes[:-1]: # last one isn't a model outcome
                    optimalOutputs.append(thisModel.getOutcome(outcome))
                population = thisModel.children.getTotalPopulation()
                w.writerow([region] + optimalOutputs + [population])
            w.writerow([])