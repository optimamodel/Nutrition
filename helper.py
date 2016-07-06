# -*- coding: utf-8 -*-
"""
Created on Mon Feb 29 11:35:02 2016

@author: madhura
"""
from copy import deepcopy as dcp

class Helper:

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


    def makeAgePopSizes(self, numAgeGroups, ageGroupSpans, spreadsheetData):
        agePopSizes = [0.]*numAgeGroups
        numGroupsInYear = 3
        numMonthsInYear = sum(ageGroupSpans[:numGroupsInYear])
        numPopEachMonth = spreadsheetData.demographics['number of live births'] / numMonthsInYear
        for i in range(numGroupsInYear):
            agePopSizes[i] = numPopEachMonth * ageGroupSpans[i]
        numMonthsOlder = sum(ageGroupSpans) - numMonthsInYear
        numPopOlder = spreadsheetData.demographics['population U5'] - spreadsheetData.demographics['number of live births']
        numPopEachMonthOlder = numPopOlder / numMonthsOlder
        for i in range(numGroupsInYear,numAgeGroups):
            agePopSizes[i] = numPopEachMonthOlder * ageGroupSpans[i]
        return agePopSizes


    def makePregnantWomen(self, spreadsheetData):
        import model as modelCode        
        annualPregnancies = dcp(spreadsheetData.demographics['number of pregnant women'])
        annualBirths      = dcp(spreadsheetData.demographics['number of live births'])
        populationSize = annualPregnancies
        birthRate   = annualBirths / annualPregnancies
        projectedBirths   = dcp(spreadsheetData.projectedBirths)
        baseBirths = projectedBirths[0]
        numYears   = len(projectedBirths)-1
        annualPercentPopGrowth = (projectedBirths[numYears]-baseBirths)/float(numYears)/float(baseBirths)
        pregnantWomen = modelCode.FertileWomen(birthRate, populationSize, annualPercentPopGrowth)        
        return pregnantWomen


    def makeBoxes(self, thisAgePopSize, ageName, keyList, spreadsheetData):
        import model as modelCode
        allBoxes = {}
        ages, birthOutcomes, wastingList, stuntingList, breastfeedingList = keyList
        for stuntingCat in stuntingList:
            allBoxes[stuntingCat] = {} 
            for wastingCat in wastingList:
                allBoxes[stuntingCat][wastingCat] = {}
                for breastfeedingCat in breastfeedingList:
                    thisPopSize = thisAgePopSize * spreadsheetData.stuntingDistribution[ageName][stuntingCat] * spreadsheetData.wastingDistribution[ageName][wastingCat] * spreadsheetData.breastfeedingDistribution[ageName][breastfeedingCat]   # Assuming independent
                    allBoxes[stuntingCat][wastingCat][breastfeedingCat] =  modelCode.Box(thisPopSize)
        return allBoxes


    def makeAgeCompartments(self, agingRateList, agePopSizes, keyList, spreadsheetData):
        import model as modelCode
        ages, birthOutcomes, wastingList, stuntingList, breastfeedingList = keyList
        numAgeGroups = len(ages)
        listOfAgeCompartments = []
        for iAge in range(numAgeGroups): # Loop over all age-groups
            ageName  = ages[iAge]
            agingRate = agingRateList[iAge]
            agePopSize = agePopSizes[iAge]
            thisAgeBoxes = self.makeBoxes(agePopSize, ageName, keyList, spreadsheetData)
            compartment = modelCode.AgeCompartment(ageName, thisAgeBoxes, agingRate, keyList)
            listOfAgeCompartments.append(compartment)
        return listOfAgeCompartments         

        
    def setupModelConstantsParameters(self, nametag, mothers, timestep, agingRateList, agePopSizes, keyList, spreadsheetData):
        import model as modelCode
        import constants as constantsCode
        import parameters as parametersCode        
        # gaussianise stunting in *data*
        ages = keyList[0]        
        for iAge in range(len(ages)):
            ageName = ages[iAge]
            probStunting = spreadsheetData.stuntingDistribution[ageName]['high'] + spreadsheetData.stuntingDistribution[ageName]['moderate']
            spreadsheetData.stuntingDistribution[ageName] = self.restratify(probStunting)
        listOfAgeCompartments = self.makeAgeCompartments(agingRateList, agePopSizes, keyList, spreadsheetData)
        pregnantWomen = self.makePregnantWomen(spreadsheetData)
        model = modelCode.Model(nametag, pregnantWomen, listOfAgeCompartments, keyList, timestep)
        constants = constantsCode.Constants(spreadsheetData, model, keyList)
        model.setConstants(constants)
        parameters = parametersCode.Params(spreadsheetData, constants, keyList)
        model.setParams(parameters)
        model.updateMortalityRate()
        return model, constants, parameters
                
                
        
        
        
        
        
        
        
        
        
        
        
        
        
