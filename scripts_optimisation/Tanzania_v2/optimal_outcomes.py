# output the outcomes that correspond to the optimal outcomes
import os, sys
root = '../..'
moduleDir = os.path.join(os.path.dirname(__file__), root)
sys.path.append(moduleDir)
import play
from copy import deepcopy as dcp
import pickle
import optimisation3 as optim
import csv

regions = ['Arusha', 'Dar_es_Salaam', 'Dodoma', 'Kaskazini_Pemba', 'Kaskazini_Unguja', 'Katavi',
           'Kilimanjaro', 'Kusini_Pemba', 'Kusini_Unguja', 'Lindi', 'Manyara', 'Mara', 'Mjini_Magharibi',
           'Morogoro', 'Mtwara', 'Pwani', 'Rukwa', 'Ruvuma', 'Simiyu', 'Singida', 'Tabora', 'Tanga']

date = '2018Apr08'
# scenarios = ['optimisedCurrent', 'additionalPerCapita', 'scenario1', 'scenario3']
scenarios = ['additionalPerCapita', 'scenario1']
objective = 'healthy_children'
outcomes = ['healthy_children', 'total_stunted', 'wasting_prev', 'anaemia_prev_children', 'deaths_children',
            'neonatal_deaths', 'child_population']

# first optimised current and additional per capita
with open('optimised_outputs.csv', 'wb') as f:
    w = csv.writer(f)
    # current
    w.writerow(['Current'] + outcomes)
    for region in regions:
        thisRegion = optim.Optimisation([objective], [1], [root, 'Tanzania/regions', region, ''])
        currentOutputs = []
        allocationsDict = thisRegion.createDictionary(thisRegion.currentAllocations)
        thisModel = thisRegion.oneModelRunWithOutput(allocationsDict)
        for outcome in outcomes[:-1]:
            currentOutputs.append(thisModel.getOutcome(outcome))
        population = thisModel.children.getTotalPopulation()
        w.writerow([region] + currentOutputs + [population])
    w.writerow([])

    # first 2 scenarios
    for scenario in scenarios[:2]:
        w.writerow([scenario])
        w.writerow(['Region'] + outcomes)
        for region in regions:
            thisRegion = optim.Optimisation([objective], [1], [root, 'Tanzania/regions', region, ''])
            thisPickle = '{}/Results/Tanzania/geospatial/{}/{}/{}_{}_1.pkl'.format(root, date, scenario, region, objective)
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
    for scenario in scenarios[2:3]: # TODO: change slice when 3 is completed
        w.writerow([scenario])
        w.writerow(['Region'] + outcomes)
        for region in regions:
            thisRegion = optim.Optimisation([objective], [1], [root, 'Tanzania/regions', region, ''])
            thisPickle = '{}/Results/Tanzania/geospatial/{}/{}/Extra_32m/pickles/{}_{}_1.pkl'.format(root, date, scenario, region, objective)
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