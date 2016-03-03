# -*- coding: utf-8 -*-
"""
Created on Fri Feb 19 12:06:58 2016

@author: ruthpearson
"""

import ListReplica as code

cause1 = code.CauseOfDeath("cause 1", 0.1)
cause2 = code.CauseOfDeath("cause 2", 0.2)
cause3 = code.CauseOfDeath("cause 3", 0.3)

listDeathCausesCompartment1 = [cause1, cause2, cause3]
listDeathCausesCompartment2 = [cause1, cause2, cause3]
listDeathCausesCompartment3 = [cause1, cause2, cause3]

conds1 = code.Conditions(30, 40)
d1 = code.Data(80, 0.2, 11, [2, 6, 7])
params1 = code.Parameters(0.1, 0.05, 0.3, 0.2)
compartment1 = code.Compartment("compartment 1", conds1, d1, params1, listDeathCausesCompartment1)

conds2 = code.Conditions(30, 40)
d2 = code.Data(80, 0.2, 11, [5, 9, 20])
params2 = code.Parameters(0.1, 0.05, 0.3, 0.2)
compartment2 = code.Compartment("compartment 2", conds2, d2, params2, listDeathCausesCompartment1)

conds3 = code.Conditions(30, 40)
d3 = code.Data(80, 0.2, 11, [10, 4, 9])
params3 = code.Parameters(0.1, 0.05, 0.3, 0.2)
compartment3 = code.Compartment("compartment 3", conds3, d3, params3, listDeathCausesCompartment1)

compartmentList = [compartment1, compartment2, compartment3]

mothers = code.FertileWomen(0.3, 0.4, 50, 80)

testModel = code.Model(mothers, compartmentList)
testModel.moveOneTimeStep()

for thing in testModel.compartmentList:
    print thing.conditions.stuntedPopulationSize
    print thing.parameters.mortalityStunted

#compartment.updateCompartment()
#print compartment.conditions.stuntedPopulationSize
