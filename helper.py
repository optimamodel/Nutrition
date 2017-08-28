#-*- coding: utf-8 -*-
"""
Created on Mon Feb 29 11:35:02 2016

@author: madhura
"""
from copy import deepcopy as dcp

class Helper:
    def __init__(self):
        self.keyList = {}
        self.keyList['timestep'] = 1./12. 
        self.keyList['ages'] = ["<1 month", "1-5 months", "6-11 months", "12-23 months", "24-59 months"]
        self.keyList['birthOutcomes'] = ["Pre-term SGA", "Pre-term AGA", "Term SGA", "Term AGA"]
        self.keyList['wastingList'] = ["normal", "mild", "moderate", "high"]
        self.keyList['stuntingList'] = ["normal", "mild", "moderate", "high"]
        self.keyList['breastfeedingList'] = ["exclusive", "predominant", "partial", "none"]
        self.keyList['anemiaList'] = ["anemic", "not anemic"] # TODO: may need to change these b/c we have different anemia categories now
        self.keyList['ageGroupSpans'] = [1., 5., 6., 12., 36.] # number of months in each age group
        self.keyList['agingRates'] = [1./1., 1./5., 1./6., 1./12., 1./36.]
        self.keyList['reproductiveAges'] = ['WRA: 15-19 years', 'WRA: 20-29 years', 'WRA: 30-39 years', 'WRA: 40-49 years']
        self.keyList['reproductiveAgingRates'] = [1./5., 1./10., 1./10., 1./10.] # this is in years
        self.keyList['stuntedList'] = ["moderate", "high"]
        self.keyList['lifeExpectancy'] = 83.5
        self.keyList['pregnantWomenAges'] = ["PW: 15-19 years", "PW: 20-29 years", "PW: 30-39 years", "PW: 40-49 years"]
        self.keyList['pregnantWomenAgeSpans'] = [5./35., 10./35., 10./35., 10./35.]
        self.keyList['allPops'] = dcp(self.keyList['ages'])
        self.keyList['allPops'] += self.keyList['pregnantWomenAges'] + self.keyList['reproductiveAges']

    # Going from binary stunting/wasting to four fractions
    # Yes refers to more than 2 standard deviations below the global mean/median
    # in our notes, fractionYes = alpha
    def restratify(self, fractionYes):
        from scipy.stats import norm
        invCDFalpha = norm.ppf(fractionYes)
        fractionHigh     = norm.cdf(invCDFalpha - 1.)
        fractionModerate = fractionYes - norm.cdf(invCDFalpha - 1.)
        fractionMild     = norm.cdf(invCDFalpha + 1.) - fractionYes
        fractionNormal   = 1. - norm.cdf(invCDFalpha + 1.)
        restratification = {}
        restratification["normal"] = fractionNormal
        restratification["mild"] = fractionMild
        restratification["moderate"] = fractionModerate
        restratification["high"] = fractionHigh
        return restratification
        
    def sumStuntedComponents(self, thingToSum):
        sumStuntedComponents = 0
        for stuntingCat in self.keyList['stuntedList']:
            sumStuntedComponents += thingToSum[stuntingCat]  
        return sumStuntedComponents    
                   


    def makeAgePopSizes(self, inputData):
        numAgeGroups = len(self.keyList['ages'])        
        agePopSizes = [0.]*numAgeGroups
        numGroupsInYear = 3
        numMonthsInYear = sum(self.keyList['ageGroupSpans'][:numGroupsInYear])
        numPopEachMonth = inputData.demographics['number of live births'] / numMonthsInYear
        for i in range(numGroupsInYear):
            agePopSizes[i] = numPopEachMonth * self.keyList['ageGroupSpans'][i]
        numMonthsOlder = sum(self.keyList['ageGroupSpans']) - numMonthsInYear
        numPopOlder = inputData.demographics['population U5'] - inputData.demographics['number of live births']
        numPopEachMonthOlder = numPopOlder / numMonthsOlder
        for i in range(numGroupsInYear,numAgeGroups):
            agePopSizes[i] = numPopEachMonthOlder * self.keyList['ageGroupSpans'][i]
        return agePopSizes

    def makeBoxes(self, thisAgePopSize, ageName, inputData):
        import populations 
        wastingList = self.keyList['wastingList']
        stuntingList = self.keyList['stuntingList']
        breastfeedingList = self.keyList['breastfeedingList']
        allBoxes = {}
        for stuntingCat in stuntingList:
            allBoxes[stuntingCat] = {} 
            for wastingCat in wastingList:
                allBoxes[stuntingCat][wastingCat] = {}
                for breastfeedingCat in breastfeedingList:
                    allBoxes[stuntingCat][wastingCat][breastfeedingCat] = {}
                    for anemiaStatus in self.keyList['anemiaList']:
                        thisPopSize = thisAgePopSize * inputData.stuntingDistribution[ageName][stuntingCat] * inputData.wastingDistribution[ageName][wastingCat] * \
                                      inputData.breastfeedingDistribution[ageName][breastfeedingCat] * inputData.anemiaDistribution[ageName][anemiaStatus] # Assuming independent
                        allBoxes[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus] =  populations.Box(thisPopSize)
        return allBoxes

        
    def makeReproductiveAgeBoxes(self, thisAgePopSize, ageName, inputData):
        import populations
        boxes = {}
        for status in self.keyList['anemiaList']:
             thisPopSize = thisAgePopSize * inputData.anemiaDistribution[ageName][status]
             boxes[status] = populations.Box(thisPopSize)   
        return boxes       

    def makePregnantWomenAgeBoxes(self, thisAgePopSize, ageName, inputData):
        import populations
        boxes = {}
        for anemiaStatus in self.keyList['anemiaList']:
            boxes[anemiaStatus] = {}
            thisPopSize = thisAgePopSize * inputData.anemiaDistribution[ageName][anemiaStatus]
            boxes[anemiaStatus] = populations.Box(thisPopSize)
        return boxes

    def makeAgeCompartments(self, agePopSizes, inputData):
        import populations 
        ages = self.keyList['ages']
        numAgeGroups = len(ages)
        listOfAgeCompartments = []
        for iAge in range(numAgeGroups): # Loop over all age-groups
            ageName  = ages[iAge]
            agingRate = self.keyList['agingRates'][iAge]
            agePopSize = agePopSizes[iAge]
            thisAgeBoxes = self.makeBoxes(agePopSize, ageName, inputData)
            compartment = populations.AgeCompartment(ageName, thisAgeBoxes, agingRate, self.keyList)
            listOfAgeCompartments.append(compartment)
        return listOfAgeCompartments         
        
    def makeReproductiveAgeCompartments(self, inputData):
            import populations 
            popReproductiveAge = dcp(inputData.demographics['population reproductive age'])
            ages = self.keyList['reproductiveAges']
            numAgeGroups = len(ages)
            listOfReproductiveAgeCompartments = []
            for iAge in range(numAgeGroups): 
                ageName  = ages[iAge]
                agePopSize = popReproductiveAge[ageName]
                agingRate = self.keyList['reproductiveAgingRates'][iAge] # TODO: can probably remove this
                thisAgeBoxes = self.makeReproductiveAgeBoxes(agePopSize, ageName, inputData)
                compartment = populations.ReproductiveAgeCompartment(ageName, thisAgeBoxes, agingRate, self.keyList)
                listOfReproductiveAgeCompartments.append(compartment)
            return listOfReproductiveAgeCompartments


    def makePregnantWomenAgeCompartments(self, inputData):
        import populations
        popPregnantWomen = dcp(inputData.demographics['number of pregnant women'])
        ages = self.keyList['pregnantWomenAges']
        numAgeGroups = len(ages)
        agePopSize = popPregnantWomen / numAgeGroups
        listOfPregnantWomenAgeCompartments = []
        annualBirths = dcp(inputData.demographics['number of live births'])
        birthRate = annualBirths / popPregnantWomen
        for iAge in range(numAgeGroups):
            ageName = ages[iAge]
            agingRate = self.keyList['pregnantWomenAgeSpans'][iAge]
            thisAgeBoxes = self.makePregnantWomenAgeBoxes(agePopSize, ageName, inputData)
            compartment = populations.PregnantWomenAgeCompartment(ageName, birthRate, thisAgeBoxes, agingRate, self.keyList)
            listOfPregnantWomenAgeCompartments.append(compartment)
        return listOfPregnantWomenAgeCompartments

    def setupModelDerivedParameters(self, inputData):
        import model 
        import derived 
        import parameters        
        # gaussianise stunting in *data*
        ages = self.keyList['ages']
        for iAge in range(len(ages)):
            ageName = ages[iAge]
            probStunting = self.sumStuntedComponents(inputData.stuntingDistribution[ageName])
            inputData.stuntingDistribution[ageName] = self.restratify(probStunting)
        agePopSizes = self.makeAgePopSizes(inputData)   
        listOfAgeCompartments = self.makeAgeCompartments(agePopSizes, inputData)
        listOfReproductiveAgeCompartments = self.makeReproductiveAgeCompartments(inputData)
        listOfPregnantWomenAgeCompartments = self.makePregnantWomenAgeCompartments(inputData)
        model = model.Model(listOfPregnantWomenAgeCompartments, listOfAgeCompartments, listOfReproductiveAgeCompartments, self.keyList)
        derived = derived.Derived(inputData, model, self.keyList)
        model.setDerived(derived)
        parameters = parameters.Params(inputData, derived, self.keyList)
        model.setParams(parameters)
        model.updateMortalityRate()
        return model, derived, parameters
                
                
    
    def setupModelSpecificPopsizes(self, inputData, agePopSizes):
        import model 
        import derived 
        import parameters        
        # gaussianise stunting in *data*
        ages = self.keyList['ages']
        for iAge in range(len(ages)):
            ageName = ages[iAge]
            probStunting = self.sumStuntedComponents(inputData.stuntingDistribution[ageName])
            inputData.stuntingDistribution[ageName] = self.restratify(probStunting)
        listOfAgeCompartments = self.makeAgeCompartments(agePopSizes, inputData)
        listOfPregnantWomenAgeCompartments = self.makePregnantWomenAgeCompartments(inputData)
        model = model.Model(listOfPregnantWomenAgeCompartments, listOfAgeCompartments, self.keyList)
        derived = derived.Derived(inputData, model, self.keyList)
        model.setDerived(derived)
        parameters = parameters.Params(inputData, derived, self.keyList)
        model.setParams(parameters)
        model.updateMortalityRate()
        return model, derived, parameters
        
        
        
        
        
        
        
        
        
