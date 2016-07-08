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
        self.keyList['ageGroupSpans'] = [1., 5., 6., 12., 36.] # number of months in each age group
        self.keyList['agingRates'] = [1./1., 1./5., 1./6., 1./12., 1./36.]
        self.keyList['stuntedList'] = ["moderate", "high"]

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
                   


    def makeAgePopSizes(self, spreadsheetData):
        numAgeGroups = len(self.keyList['ages'])        
        agePopSizes = [0.]*numAgeGroups
        numGroupsInYear = 3
        numMonthsInYear = sum(self.keyList['ageGroupSpans'][:numGroupsInYear])
        numPopEachMonth = spreadsheetData.demographics['number of live births'] / numMonthsInYear
        for i in range(numGroupsInYear):
            agePopSizes[i] = numPopEachMonth * self.keyList['ageGroupSpans'][i]
        numMonthsOlder = sum(self.keyList['ageGroupSpans']) - numMonthsInYear
        numPopOlder = spreadsheetData.demographics['population U5'] - spreadsheetData.demographics['number of live births']
        numPopEachMonthOlder = numPopOlder / numMonthsOlder
        for i in range(numGroupsInYear,numAgeGroups):
            agePopSizes[i] = numPopEachMonthOlder * self.keyList['ageGroupSpans'][i]
        return agePopSizes


    def makePregnantWomen(self, spreadsheetData):
        import model       
        annualPregnancies = dcp(spreadsheetData.demographics['number of pregnant women'])
        annualBirths      = dcp(spreadsheetData.demographics['number of live births'])
        populationSize = annualPregnancies
        birthRate   = annualBirths / annualPregnancies
        projectedBirths   = dcp(spreadsheetData.projectedBirths)
        baseBirths = float(projectedBirths[0])
        numYears   = len(projectedBirths)-1
        annualPercentPopGrowth = (projectedBirths[numYears]-baseBirths)/float(numYears)/baseBirths
        pregnantWomen = model.PregnantWomen(birthRate, populationSize, annualPercentPopGrowth)        
        return pregnantWomen


    def makeBoxes(self, thisAgePopSize, ageName, spreadsheetData):
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
                    thisPopSize = thisAgePopSize * spreadsheetData.stuntingDistribution[ageName][stuntingCat] * spreadsheetData.wastingDistribution[ageName][wastingCat] * spreadsheetData.breastfeedingDistribution[ageName][breastfeedingCat]   # Assuming independent
                    allBoxes[stuntingCat][wastingCat][breastfeedingCat] =  model.Box(thisPopSize)
        return allBoxes


    def makeAgeCompartments(self, agePopSizes, spreadsheetData):
        import model 
        ages = self.keyList['ages']
        numAgeGroups = len(ages)
        listOfAgeCompartments = []
        for iAge in range(numAgeGroups): # Loop over all age-groups
            ageName  = ages[iAge]
            agingRate = self.keyList['agingRates'][iAge]
            agePopSize = agePopSizes[iAge]
            thisAgeBoxes = self.makeBoxes(agePopSize, ageName, spreadsheetData)
            compartment = model.AgeCompartment(ageName, thisAgeBoxes, agingRate, self.keyList)
            listOfAgeCompartments.append(compartment)
        return listOfAgeCompartments         

        
    def setupModelConstantsParameters(self, spreadsheetData):
        import model 
        import derived 
        import parameters        
        # gaussianise stunting in *data*
        ages = self.keyList['ages']
        for iAge in range(len(ages)):
            ageName = ages[iAge]
            probStunting = self.sumStuntedComponents(spreadsheetData.stuntingDistribution[ageName])
            spreadsheetData.stuntingDistribution[ageName] = self.restratify(probStunting)
        agePopSizes = self.makeAgePopSizes(spreadsheetData)   
        listOfAgeCompartments = self.makeAgeCompartments(agePopSizes, spreadsheetData)
        pregnantWomen = self.makePregnantWomen(spreadsheetData)
        model = model.Model(pregnantWomen, listOfAgeCompartments, self.keyList)
        derived = derived.Derived(spreadsheetData, model, self.keyList)
        model.setDerived(derived)
        parameters = parameters.Params(spreadsheetData, derived, self.keyList)
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
        
        
        
        
        
        
        
        
        
