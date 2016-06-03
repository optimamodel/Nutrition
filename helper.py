# -*- coding: utf-8 -*-
"""
Created on Mon Feb 29 11:35:02 2016

@author: madhura
"""

class Helper:
    def __init__(self):
        self.foo = 0.

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

    def makeBoxes(self, thisAgePopSize, ageGroup, keyList, spreadsheetData):
        import model as modelCode        
        allBoxes = {}
        ages, birthOutcomes, wastingList, stuntingList, breastfeedingList = keyList
        for stuntingCat in stuntingList:
            allBoxes[stuntingCat] = {} 
            for wastingCat in wastingList:
                allBoxes[stuntingCat][wastingCat] = {}
                for breastfeedingCat in breastfeedingList:
                    thisPopSize = thisAgePopSize * spreadsheetData.stuntingDistribution[ageGroup][stuntingCat] * spreadsheetData.wastingDistribution[ageGroup][wastingCat] * spreadsheetData.breastfeedingDistribution[ageGroup][breastfeedingCat]   # Assuming independent
                    thisMortalityRate = 0
                    allBoxes[stuntingCat][wastingCat][breastfeedingCat] =  modelCode.Box(stuntingCat, wastingCat, breastfeedingCat, thisPopSize, thisMortalityRate)
        return allBoxes

    def makeAgeCompartments(self, agingRateList, agePopSizes, keyList, spreadsheetData):
        import model as modelCode
        ages, birthOutcomes, wastingList, stuntingList, breastfeedingList = keyList
        numAgeGroups = len(ages)
        listOfAgeCompartments = []
        for age in range(numAgeGroups): # Loop over all age-groups
            ageGroup  = ages[age]
            agingRate = agingRateList[age]
            agePopSize = agePopSizes[age]
            thisAgeBoxes = self.makeBoxes(agePopSize, ageGroup, keyList, spreadsheetData)
            compartment = modelCode.AgeCompartment(ageGroup, thisAgeBoxes, agingRate, keyList)
            listOfAgeCompartments.append(compartment)
        return listOfAgeCompartments         
        
    def setupModelConstantsParameters(self, nametag, mothers, timestep, agingRateList, agePopSizes, keyList, spreadsheetData):
        import model as modelCode
        import constants as constantsCode
        import parameters as parametersCode        
        # gaussianise stunting in *data*
        ages = keyList[0]        
        for ageGroup in range(len(ages)):
            ageName = ages[ageGroup]
            probStunting = spreadsheetData.stuntingDistribution[ageName]['high'] + spreadsheetData.stuntingDistribution[ageName]['moderate']
            spreadsheetData.stuntingDistribution[ageName] = self.restratify(probStunting)
        listOfAgeCompartments = self.makeAgeCompartments(agingRateList, agePopSizes, keyList, spreadsheetData)
        fertileWomen = modelCode.FertileWomen(mothers['birthRate'], mothers['populationSize'])
        model = modelCode.Model(nametag, fertileWomen, listOfAgeCompartments, keyList, timestep)
        constants = constantsCode.Constants(spreadsheetData, model, keyList)
        model.setConstants(constants)
        parameters = parametersCode.Params(spreadsheetData, constants, keyList)
        model.setParams(parameters)
        model.updateMortalityRate()
        return model, constants, parameters
                
                
        
        
        
        
        
        
        
        
        
        
        
        
        