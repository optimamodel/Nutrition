# -*- coding: utf-8 -*-
"""
Created on Tue Mar 15 15:32:21 2016

@author: ruth
"""
import unittest
import numpy

import data as data
import helper as helper


def setUpDataModelConstantsParameters():
    ages = ["<1 month", "1-5 months", "6-11 months", "12-23 months", "24-59 months"]
    birthOutcomes = ["Pre-term SGA", "Pre-term AGA", "Term SGA", "Term AGA"]
    wastingList = ["normal", "mild", "moderate", "high"]
    stuntingList = ["normal", "mild", "moderate", "high"]
    breastfeedingList = ["exclusive", "predominant", "partial", "none"]
    keyList = [ages, birthOutcomes, wastingList, stuntingList, breastfeedingList]
    testData = data.getDataFromSpreadsheet('InputForCode_tests.xlsx', keyList)
    mothers = {'birthRate':0.9, 'populationSize':2.e6}
    agingRateList = [1./1., 1./5., 1./6., 1./12., 1./36.] # fraction of people aging out per MONTH
    agePopSizes  = [6400, 6400, 6400, 6400, 6400]
    timestep = 1./12. 

    helperTests = helper.Helper()
    testModel, testConstants, testParams = helperTests.setupModelConstantsParameters('tests', mothers, timestep, agingRateList, agePopSizes, keyList, testData)
    return testData, testModel, testConstants, testParams, keyList
    
    
class TestsForsetUpDataModelConstantsParameters(unittest.TestCase):
    def setUp(self):
        [self.testData, self.testModel, self.testConstants, self.testParams, self.keyList] = setUpDataModelConstantsParameters()
        
    def testNumberInAnAgeCompartment(self):
        sumPopAge1 = 0
        for stuntingCat in ["normal", "mild", "moderate", "high"]:
            for wastingCat in ["normal", "mild", "moderate", "high"]:
                for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
                    sumPopAge1 += self.testModel.listOfAgeCompartments[1].dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize 
        self.assertEqual(sumPopAge1, 64 * 100)     
    

class TestsForConstantsClass(unittest.TestCase):
    def setUp(self):
        [self.testData, self.testModel, self.testConstants, self.testParams, self.keyList] = setUpDataModelConstantsParameters()
        
    def testGetUnderlyingMortalities(self):
        # 64 compartments per age; 25/100=0.25 (distributions); 1 (cause); 1 (RR); 500/1000=0.5 for newborn otherwise 0.0 (total mortality) 
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
           
    def testDiarrheaRiskSum(self):
        riskSum = self.testConstants.getDiarrheaRiskSum('24-59 months', self.testData.breastfeedingDistribution)        
        self.assertEqual(1., riskSum)
        
    def testGetZa(self):
        # Za = incidence / riskSum; riskSum = 1
        incidence = {'<1 month':1, '1-5 months':1, '6-11 months':1, '12-23 months':1, '24-59 months':1}
        Za = self.testConstants.getZa(incidence, self.testData.breastfeedingDistribution)
        self.assertEqual(incidence, Za)   

    def testGetAOGivenZa(self):
        # for neonatal:  OR = 1.04, RR = 1, alpha = 1, set Z = 1
        # AO[0] = OR ^ (RR * Z * alpha)
        z = {'<1 month':1, '1-5 months':1, '6-11 months':1, '12-23 months':1, '24-59 months':1}
        AO = self.testConstants.getAOGivenZa(z) 
        self.assertEqual(AO['<1 month'], 1.04)
           
    @unittest.skip("write test once quartic is solved")            
    def testGetBaselineBirthOutcome(self):
        # need to write tests for this once quartic equation is solved
         self.assertTrue(False)
         
 
class TestsForModelClass(unittest.TestCase):
    def setUp(self):
        [self.testData, self.testModel, self.testConstants, self.testParams, self.keyList] = setUpDataModelConstantsParameters()
        

    def testApplyMortalityOneBox(self):
        # deaths = popsize * mortality * timestep
        #popsize = 100, mortality = 0.5, timestep = 1/12
        self.testModel.applyMortality()
        popSize = self.testModel.listOfAgeCompartments[0].dictOfBoxes['high']['mild']['none'].populationSize
        cumulativeDeaths = self.testModel.listOfAgeCompartments[0].dictOfBoxes['high']['mild']['none'].cumulativeDeaths
        self.assertAlmostEqual(100.*0.5/12., cumulativeDeaths)
        self.assertAlmostEqual(100. - (100.*0.5/12.), popSize)
    
    @unittest.skip("underlying mortalites all set to zero except for neonatals")
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
        expectedMortalityRate = 1. 
        self.assertEqual(expectedMortalityRate, updatedMortalityRate)
         
         
class TestsForHelperClass(unittest.TestCase):
    def setUp(self):
        self.helper = helper.Helper()
        [self.testData, self.testModel, self.testConstants, self.testParams, self.keyList] = setUpDataModelConstantsParameters()
        self.agingRateList = [1./1., 1./5., 1./6., 1./12., 1./36.] 
        self.agePopSizes  = [6400, 6400, 6400, 6400, 6400]             
             
    def testRestratifyWhenFractionYesIsHalf(self):
        # if FractionYes = 0.5 then (symmetric normal) distribution is centred at global mean -2 SD
        # therefore we expect moderate = normal and mild = high
        stratification = self.helper.restratify(0.5)
        self.assertEqual(stratification['moderate'], stratification['mild'])
        self.assertEqual(stratification['normal'], stratification['high'])
        
    def testMakeBoxes(self):
        # 0.25 * 0.25 * 0.25 * 6400 = 100
        boxes = self.helper.makeBoxes(6400, '6-11 months', self.keyList, self.testData)   
        self.assertEqual(100, boxes['normal']['normal']['none'].populationSize)

    def testMakeAgeCompartment(self):
        listOfAgeCompartments = self.helper.makeAgeCompartments(self.agingRateList, self.agePopSizes, self.keyList, self.testData)        
        self.assertAlmostEqual(5, len(listOfAgeCompartments))
        self.assertAlmostEqual(100, listOfAgeCompartments[2].dictOfBoxes['normal']['normal']['none'].populationSize)
        
    def testSetUpModelConstantsParameters(self):
        self.assertEqual(self.testConstants.initialStuntingTrend, self.testModel.constants.initialStuntingTrend)
        self.assertEqual(self.testParams.stuntingDistribution['1-5 months'], self.testModel.params.stuntingDistribution['1-5 months'])
    
# this needs to be here for the tests to run automatically    
if __name__ == '__main__':
    unittest.main()    
