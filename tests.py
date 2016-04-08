# -*- coding: utf-8 -*-
"""
Created on Tue Mar 15 15:32:21 2016

@author: ruth
"""
import unittest
import numpy

import model as model
import data as data
import constants as constants
import parameters as parametersCode
import helper as helper


def setUpDataModelConstantsObjects():
    ages = ["<1 month","1-5 months","6-11 months","12-23 months","24-59 months"]
    birthOutcomes = ["Pre-term SGA","Pre-term AGA","Term SGA","Term AGA"]
    listOfLabels = [ages,birthOutcomes]
    testData = data.getDataFromSpreadsheet('InputForCode_tests.xlsx',listOfLabels)
    #----------------------   MAKE ALL THE BOXES     ---------------------
    mothers = model.FertileWomen(0.2, 2.e6)
    listOfAgeCompartments = []
    ageRangeList  = testData.ages
    agingRateList = [1./1., 1./5., 1./6., 1./12., 1./36.] # fraction of people aging out per MONTH
    numAgeGroups = len(ageRangeList)
    agePopSizes  = [6400, 6400, 6400, 6400, 6400]
    
    timestep = 1./12. 
    numsteps = 10  
    timespan = timestep * float(numsteps)    
    
    # Loop over all age-groups
    for age in range(numAgeGroups): 
        ageRange  = ageRangeList[age]
        agingRate = agingRateList[age]
        agePopSize = agePopSizes[age]
    # allBoxes is a dictionary rather than a list to provide to AgeCompartment
        allBoxes = {}
        for stuntingCat in ["normal", "mild", "moderate", "high"]:
            allBoxes[stuntingCat] = {} 
            for wastingCat in ["normal", "mild", "moderate", "high"]:
                allBoxes[stuntingCat][wastingCat] = {}
                for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
                    thisPopSize = int(agePopSize/64.) # 100 people in each box
                    thisMortalityRate = testData.totalMortality[ageRange] # WARNING need to distribute appropriately
                    allBoxes[stuntingCat][wastingCat][breastfeedingCat] =  model.Box(stuntingCat, wastingCat, breastfeedingCat, thisPopSize, thisMortalityRate)
        compartment = model.AgeCompartment(ageRange, allBoxes, agingRate)
        listOfAgeCompartments.append(compartment)
    #------------------------------------------------------------------------    
    # make a model object
    testModel = model.Model("Main model", mothers, listOfAgeCompartments, listOfLabels, timestep)
    # make the constants object    
    testConstants = constants.Constants(testData, testModel)
    # set the constants in the model object
    testModel.setConstants(testConstants)
    testParams = parametersCode.Params(testData)
    testModel.setParams(testParams)

    return testData, testModel, testConstants, testParams
    
    
class TestsForSetUpDataModelConstantsObjectsFunction(unittest.TestCase):
    def setUp(self):
        [self.testData, self.testModel, self.testConstants, self.testParams] = setUpDataModelConstantsObjects()
        
    def testNumberInAnAgeCompartment(self):
        sumPopAge1 = 0
        for stuntingCat in ["normal", "mild", "moderate", "high"]:
            for wastingCat in ["normal", "mild", "moderate", "high"]:
                for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
                    sumPopAge1 += self.testModel.listOfAgeCompartments[1].dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize 
        self.assertEqual(sumPopAge1, 64 * 100)     
    

class TestsForConstantsClass(unittest.TestCase):
    def setUp(self):
        [self.testData, self.testModel, self.testConstants, self.testParams] = setUpDataModelConstantsObjects()
        
    def testGetUnderlyingMortalities(self):
        # 64 compartments per age; 25/100=0.25 (distributions); 1 (cause); 1 (RR); 500/1000=0.5 (total mortality)
        # underlyingMortality = total mortality / (numCompartments * dist * dist * dist * RR * RR * RR * cause)
        # underlyingMortality = total mortality / (numBFCompartments * BFdist * RR * RR * cause) for newborns
        self.assertAlmostEqual(0.5/4./0.25, self.testConstants.underlyingMortalities["<1 month"]["Neonatal diarrhea"])
        for age in ['1-5 months', '6-11 months', '12-23 months', '24-59 months']:
            self.assertAlmostEqual((0./64.)*(1.e6), self.testConstants.underlyingMortalities[age]["Diarrhea"])
        
    def testStuntingProbabilitiesEqualExpectedWhenORis2(self):
        # for OR = 2, assuming F(a) = F(a-1) = 0.5:
        # pn = sqrt(2) - 1
        for age in ['1-5 months', '6-11 months', '12-23 months', '24-59 months']:
            self.assertAlmostEqual(self.testConstants.probStuntedIfPrevStunted["notstunted"][age], numpy.sqrt(2)-1)
        
    def testRelationshipBetweenStuntingProbabilitiesWhenORis2(self):
        # this relationship between ps and pn comes from the OR definition
        # ps = OR * pn / (1 - pn + (OR * pn)) 
        for age in ['1-5 months', '6-11 months', '12-23 months', '24-59 months']:
            ps = 2 * self.testConstants.probStuntedIfPrevStunted["notstunted"][age] / (1 + self.testConstants.probStuntedIfPrevStunted["notstunted"][age])
            self.assertAlmostEqual(self.testConstants.probStuntedIfPrevStunted["yesstunted"][age], ps)
                
    @unittest.skip("write test once quartic is solved")            
    def testGetBaselineBirthOutcome(self):
        # need to write tests for this once quartic equation is solved
         self.assertTrue(False)
         
 
class TestsForModelClass(unittest.TestCase):
    def setUp(self):
        [self.testData, self.testModel, self.testConstants, self.testParams] = setUpDataModelConstantsObjects()
        

    def testApplyMortalityOneBox(self):
        # deaths = popsize * mortality * timestep
        #popsize = 100, mortality = 0.5, timestep = 1/12
        self.testModel.applyMortality()
        popSize = self.testModel.listOfAgeCompartments[0].dictOfBoxes['high']['mild']['none'].populationSize
        cumulativeDeaths = self.testModel.listOfAgeCompartments[0].dictOfBoxes['high']['mild']['none'].cumulativeDeaths
        self.assertAlmostEqual(100.*0.5/12., cumulativeDeaths)
        self.assertAlmostEqual(100. - (100.*0.5/12.), popSize)
        
    def testApplyMortalityBySummingAllBoxes(self):
        self.testModel.applyMortality()
        for ageGroup in range(0, len(self.testModel.listOfAgeCompartments)):
            sumPopSize = 0.
            sumCumulativeDeaths = 0.
            for stuntingCat in ["normal", "mild", "moderate", "high"]:
                for wastingCat in ["normal", "mild", "moderate", "high"]:
                    for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
                        sumPopSize += self.testModel.listOfAgeCompartments[ageGroup].dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize
                        sumCumulativeDeaths += self.testModel.listOfAgeCompartments[ageGroup].dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].cumulativeDeaths
            self.assertAlmostEqual(64. * (100.*0.5/12.), sumCumulativeDeaths)
            self.assertAlmostEqual(64. * (100. - (100.*0.5/12.)), sumPopSize)
            
    def testApplyAgingForNewbornsOnly(self):
        self.testModel.applyAging()
        self.assertEqual(0., self.testModel.listOfAgeCompartments[0].dictOfBoxes['mild']['high']['predominant'].populationSize)
        
    def testApplyAging(self):
        # sum aging out age[0] should equal sum aging in age[1]   
        # calculate what we expect        
        sumAgeingOutAge0 = 64. * 100. * (1./1.) 
        sumAgeingOutAge1 = 64. * 100. * (1./5.) 
        expectedSumPopAge1 = (64 * 100) - sumAgeingOutAge1 + sumAgeingOutAge0
        # call the function to apply aging
        self.testModel.applyAging()
        # count population in age 1 after calling aging function
        sumPopAge1 = 0
        for stuntingCat in ["normal", "mild", "moderate", "high"]:
            for wastingCat in ["normal", "mild", "moderate", "high"]:
                for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
                    sumPopAge1 += self.testModel.listOfAgeCompartments[1].dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize
        self.assertAlmostEqual(sumPopAge1, expectedSumPopAge1)    

    @unittest.skip("need to translate birth outcome to stunting after quartic solved")     
    def testApplyBirths(self):
        # need to write this test
        self.assertTrue(False)
        
    def testUpdateMortalityRate(self):
        self.testModel.constants.underlyingMortalities['12-23 months']["Diarrhea"] = 1
        self.testModel.updateMortalityRate()
        updatedMortalityRate = self.testModel.listOfAgeCompartments[3].dictOfBoxes['normal']['normal']['none'].mortalityRate
        self.assertEqual(1., updatedMortalityRate)
         
         
class TestsForHelperClass(unittest.TestCase):
    def setUp(self):
        self.helper = helper.Helper()
             
    def testRestratifyWhenFractionYesIsHalf(self):
        # if FractionYes = 0.5 then (symmetric normal) distribution is centred at global mean -2 SD
        # therefore we expect moderate = normal and mild = high
        stratification = self.helper.restratify(0.5)
        self.assertEqual(stratification['moderate'], stratification['mild'])
        self.assertEqual(stratification['normal'], stratification['high'])
    
# this needs to be here for the tests to run automatically    
if __name__ == '__main__':
    unittest.main()    
