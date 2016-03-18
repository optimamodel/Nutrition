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


def setUpDataAndModelObjects():
    mothers = model.FertileWomen(0.2, 2.e6)
    testData = data.getDataFromSpreadsheet('InputForCode_tests.xlsx')
    #----------------------   MAKE ALL THE BOXES     ---------------------
    listOfAgeCompartments = []
    ageRangeList  = testData.ages
    agingRateList = [1./1., 1./5., 1./6., 1./12., 1./36.] # fraction of people aging out per year
    numAgeGroups = len(ageRangeList)
    agePopSizes  = [6400, 6400, 6400, 6400, 6400]
    timespan = 5.0 # [years] running the model for this long
    numsteps = 60  # number of timesteps; determined to produce a sensible timestep
    timestep = timespan / float(numsteps)
    # Loop over all age-groups
    for age in range(numAgeGroups): 
        ageRange  = ageRangeList[age]
        agingRate = agingRateList[age]
        agePopSize = agePopSizes[age]
    # allBoxes is a dictionary rather than a list to provide to AgeCompartment
        allBoxes = {}
        for stuntingStatus in ["normal", "mild", "moderate", "high"]:
            allBoxes[stuntingStatus] = {} 
            for wastingStatus in ["normal", "mild", "moderate", "high"]:
                allBoxes[stuntingStatus][wastingStatus] = {}
                for breastfeedingStatus in ["exclusive", "predominant", "partial", "none"]:
                    thisPopSize = int(agePopSize/64.) # 100 people in each box
                    thisMortalityRate = testData.totalMortalityByAge[age] # WARNING need to distribute appropriately
                    allBoxes[stuntingStatus][wastingStatus][breastfeedingStatus] =  model.Box(stuntingStatus, wastingStatus, breastfeedingStatus, thisPopSize, thisMortalityRate)
        compartment = model.AgeCompartment(ageRange, allBoxes, agingRate)
        listOfAgeCompartments.append(compartment)
    #------------------------------------------------------------------------    
    # make a model object
    testModel = model.Model("Main model", mothers, listOfAgeCompartments, testData.ages, timestep)
    # make the constants object    
    testConstants = constants.Constants(testData, testModel)
    # set the constants in the model object
    testModel.setConstants(testConstants)
    return testData, testModel, testConstants
    

class TestsForConstantsClass(unittest.TestCase):
    def setUp(self):
        [self.testData, self.testModel, self.testConstants] = setUpDataAndModelObjects()
        
    def testGetUnderlyingMortalityByAge(self):
        for age in self.testModel.ages:
            self.assertEqual(1./6400, self.testConstants.underlyingMortalityByAge[age])
        
    def testStuntingProbabilitiesEqualExpectedWhenORis2(self):
        # for OR = 2, assuming F(a) = F(a-1) = 0.5:
        # pn = sqrt(2) - 1
        for age in ['1-5 months', '6-11 months', '12-23 months', '24-59 months']:
            self.assertAlmostEqual(self.testConstants.probStuntedIfNotPreviously[age], numpy.sqrt(2)-1)
        
    def testRealtionshipBetweenStuntingProbabilitiesWhenORis2(self):
        # this relationship between ps and pn comes from the OR definition
        # ps = OR * pn / (1 - pn + (OR * pn)) 
        for age in ['1-5 months', '6-11 months', '12-23 months', '24-59 months']:
            ps = 2 * self.testConstants.probStuntedIfNotPreviously[age] / (1 + self.testConstants.probStuntedIfNotPreviously[age])
            self.assertAlmostEqual(self.testConstants.probStuntedIfPreviously[age], ps)
                
    @unittest.skip("write test once quartic is solved")            
    def testGetBaselineBirthOutcome(self):
        # need to write tests for this once quartic equation is solved
         self.assertTrue(False)
         
 
class TestsForModelClass(unittest.TestCase):
    def setUp(self):
        [self.testData, self.testModel, self.testConstants] = setUpDataAndModelObjects()
        
    def testApplyMortalityOneBox(self):
        # deaths = popsize * mortality * timestep
        #popsize = 100, mortality = 1, timestep = 1/12
        self.testModel.applyMortality()
        popSize = self.testModel.listOfAgeCompartments[0].dictOfBoxes['high']['mild']['none'].populationSize
        cumulativeDeaths = self.testModel.listOfAgeCompartments[0].dictOfBoxes['high']['mild']['none'].cumulativeDeaths
        self.assertAlmostEqual(100./12., cumulativeDeaths)
        self.assertAlmostEqual(100. - (100./12.), popSize)
        
    def testApplyMortalityBySummingAllBoxes(self):
        self.testModel.applyMortality()
        for ageGroup in range(0, len(self.testModel.listOfAgeCompartments)):
            sumPopSize = 0.
            sumCumulativeDeaths = 0.
            for stuntingStatus in ["normal", "mild", "moderate", "high"]:
                for wastingStatus in ["normal", "mild", "moderate", "high"]:
                    for breastfeedingStatus in ["exclusive", "predominant", "partial", "none"]:
                        sumPopSize += self.testModel.listOfAgeCompartments[ageGroup].dictOfBoxes[stuntingStatus][wastingStatus][breastfeedingStatus].populationSize
                        sumCumulativeDeaths += self.testModel.listOfAgeCompartments[ageGroup].dictOfBoxes[stuntingStatus][wastingStatus][breastfeedingStatus].cumulativeDeaths
            self.assertAlmostEqual(64. * (100./12.), sumCumulativeDeaths)
            self.assertAlmostEqual(64. * (100. - (100./12.)), sumPopSize)
            
    def testApplyAgingForNewbornsOnly(self):
        self.testModel.applyAging()
        self.assertEqual(100. - int(100./12.), self.testModel.listOfAgeCompartments[0].dictOfBoxes['mild']['high']['predominant'].populationSize)
        
    def testApplyAgingForIntegerProbabilities(self):
        # sum aging out age[0] should equal sum aging in age[1]   
        # set integer probabilities so that there is no movement between stunting statuses
        self.testModel.constants.probStuntedIfNotPreviously['1-5 months'] = 0
        self.testModel.constants.probStuntedIfPreviously['1-5 months'] = 1
        sumAgeingOutAge0 = 64. * int(100. * (1./12))
        sumAgeingOutAge1 = 64. * int(100. * (1./5) * (1./12))
        self.testModel.applyAging()
        sumPopAge1 = 0
        for stuntingStatus in ["normal", "mild", "moderate", "high"]:
                for wastingStatus in ["normal", "mild", "moderate", "high"]:
                    for breastfeedingStatus in ["exclusive", "predominant", "partial", "none"]:
                        sumPopAge1 += self.testModel.listOfAgeCompartments[1].dictOfBoxes[stuntingStatus][wastingStatus][breastfeedingStatus].populationSize 
        self.assertEqual(sumPopAge1, (64 * 100) - sumAgeingOutAge1 + sumAgeingOutAge0)    

    @unittest.skip("talk to Mud about this")
    def testApplyAgingForNonIntegerProbabilities(self):
        # need to write this test
        # sum aging out age[0] should equal sum aging in age[1]
         self.assertTrue(False)
         
    @unittest.skip("need to translate birth outcome to stunting after quartic solved")     
    def testApplyBirths(self):
        # need to write this test
        self.assertTrue(False)
         
    
# this needs to be here for the tests to run automatically    
if __name__ == '__main__':
    unittest.main()    