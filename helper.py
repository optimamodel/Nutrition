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
        self.keyList['wastingList'] = ["obese", "normal", "mild", "moderate", "high"]
        self.keyList['stuntingList'] = ["normal", "mild", "moderate", "high"]
        self.keyList['breastfeedingList'] = ["exclusive", "predominant", "partial", "none"]
        self.keyList['anemiaList'] = ["anemic", "not anemic"]
        self.keyList['ageGroupSpans'] = [1., 5., 6., 12., 36.] # number of months in each age group
        self.keyList['agingRates'] = [1./1., 1./5., 1./6., 1./12., 1./36.]
        self.keyList['reproductiveAges'] = ['15-19 years', '20-24 years', '25-29 years', '30-34 years', '35-39 years', '40-44 years']
        self.keyList['reproductiveAgingRates'] = [1./5., 1./5., 1./5., 1./5., 1./5., 1./5.] # this is in years
        self.keyList['stuntedList'] = ["moderate", "high"]
        self.keyList['lifeExpectancy'] = 83.5
        self.keyList['deliveryList'] = ["unassisted", "assisted at home", "essential care", "BEmOC", "CEmOC"]
        self.keyList['allPops'] = dcp(self.keyList['ages'])
        self.keyList['allPops'] += ['pregnant women'] + self.keyList['reproductiveAges']

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


    def makePregnantWomen(self, inputData):
        import model       
        annualPregnancies = dcp(inputData.demographics['number of pregnant women'])
        annualBirths      = dcp(inputData.demographics['number of live births'])
        birthRate   = annualBirths / annualPregnancies
        projectedBirths   = dcp(inputData.projectedBirths)
        baseBirths = float(projectedBirths[0])
        numYears   = len(projectedBirths)-1
        annualGrowth = (projectedBirths[numYears]-baseBirths)/float(numYears)/baseBirths
        boxes = self.makeMaternalBoxes(inputData)
        pregnantWomen = model.PregnantWomen(birthRate, annualGrowth, boxes, self.keyList)        
        return pregnantWomen


    def makeBoxes(self, thisAgePopSize, ageName, inputData):
        import model 
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
                        allBoxes[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus] =  model.Box(thisPopSize)
        return allBoxes
        
        
    def makeMaternalBoxes(self, inputData):
        import model
        annualPregnancies = dcp(inputData.demographics['number of pregnant women'])
        populationSize = annualPregnancies
        boxes = {}
        for anemiaStatus in self.keyList['anemiaList']:
            boxes[anemiaStatus] = {}
            for deliveryStatus in self.keyList['deliveryList']:
                 thisPopSize = populationSize * inputData.deliveryDistribution[deliveryStatus] * inputData.anemiaDistribution['pregnant women'][anemiaStatus]
                 boxes[anemiaStatus][deliveryStatus] = model.Box(thisPopSize)
        return boxes  
        
    def makeReproductiveAgeBoxes(self, thisAgePopSize, ageName, inputData):
        import model
        boxes = {}
        for status in self.keyList['anemiaList']:
             thisPopSize = thisAgePopSize * inputData.anemiaDistribution[ageName][status]
             boxes[status] = model.Box(thisPopSize)   
        return boxes       


    def makeAgeCompartments(self, agePopSizes, inputData):
        import model 
        ages = self.keyList['ages']
        numAgeGroups = len(ages)
        listOfAgeCompartments = []
        for iAge in range(numAgeGroups): # Loop over all age-groups
            ageName  = ages[iAge]
            agingRate = self.keyList['agingRates'][iAge]
            agePopSize = agePopSizes[iAge]
            thisAgeBoxes = self.makeBoxes(agePopSize, ageName, inputData)
            compartment = model.AgeCompartment(ageName, thisAgeBoxes, agingRate, self.keyList)
            listOfAgeCompartments.append(compartment)
        return listOfAgeCompartments         
        
    def makeReproductiveAgeCompartments(self, inputData):
            import model 
            popReproductiveAge = dcp(inputData.demographics['population reproductive age'])
            ages = self.keyList['reproductiveAges']
            numAgeGroups = len(ages)
            agePopSize = popReproductiveAge / numAgeGroups # equally distributed
            listOfReproductiveAgeCompartments = []
            for iAge in range(numAgeGroups): 
                ageName  = ages[iAge]
                agingRate = self.keyList['reproductiveAgingRates'][iAge]
                thisAgeBoxes = self.makeReproductiveAgeBoxes(agePopSize, ageName, inputData)
                compartment = model.ReproductiveAgeCompartment(ageName, thisAgeBoxes, agingRate, self.keyList)
                listOfReproductiveAgeCompartments.append(compartment)
            return listOfReproductiveAgeCompartments              
   
        
    def setupModelConstantsParameters(self, inputData):
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
        pregnantWomen = self.makePregnantWomen(inputData)
        model = model.Model(pregnantWomen, listOfAgeCompartments, listOfReproductiveAgeCompartments, self.keyList)
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
        pregnantWomen = self.makePregnantWomen(inputData)
        model = model.Model(pregnantWomen, listOfAgeCompartments, self.keyList)
        derived = derived.Derived(inputData, model, self.keyList)
        model.setDerived(derived)
        parameters = parameters.Params(inputData, derived, self.keyList)
        model.setParams(parameters)
        model.updateMortalityRate()
        return model, derived, parameters
        
        
        
        
        
        
        
        
        
