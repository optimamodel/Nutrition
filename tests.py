# -*- coding: utf-8 -*-
"""
Created on Tue Mar 15 15:32:21 2016

@author: ruth
"""
import unittest
import numpy

import data as data
import helper as helper


def setupDataModelDerivedParameters():
    helperTests = helper.Helper()
    testData = data.readSpreadsheet('input_spreadsheets/InputForCode_tests.xlsx', helperTests.keyList)
    testModel, testDerived, testParams = helperTests.setupModelDerivedParameters(testData)
    return testData, testModel, testDerived, testParams, helperTests.keyList


class TestsForsetupDataModelDerivedParameters(unittest.TestCase):
    def setUp(self):
        [self.testData, self.testModel, self.testDerived, self.testParams, self.keyList] = setupDataModelDerivedParameters()
        
    def testNumberInAnAgeCompartment(self):
        sumPopAge1 = 0
        for stuntingCat in ["normal", "mild", "moderate", "high"]:
            for wastingCat in ["normal", "mild", "moderate", "high"]:
                for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
                    sumPopAge1 += self.testModel.listOfAgeCompartments[1].dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize 
        self.assertAlmostEqual(sumPopAge1, 32000)     
    

class TestsForDerivedClass(unittest.TestCase):
    def setUp(self):
        [self.testData, self.testModel, self.testDerived, self.testParams, self.keyList] = setupDataModelDerivedParameters()
        
    def testGetUnderlyingMortalities(self):
        # 64 compartments per age; 25/100=0.25 (distributions); 1 (cause); 1 (RR); 500*12/1000=6. for newborn otherwise 0.0 (total mortality) 
        # underlyingMortality = total mortality / (numCompartments * dist * dist * dist * RR * RR * RR * cause)
        # underlyingMortality = total mortality / (numBFCompartments * BFdist * RR * RR * cause) for newborns
        self.assertAlmostEqual(6./4./0.25, self.testDerived.referenceMortality["<1 month"]["Neonatal diarrhea"])
        for ageName in ['1-5 months', '6-11 months', '12-23 months', '24-59 months']:
            self.assertAlmostEqual((0./64.)*(1.e6), self.testDerived.referenceMortality[ageName]["Diarrhea"])
        
    def testStuntingProbabilitiesEqualExpectedWhenORis2(self):
        # for OR = 2, assuming F(a) = F(a-1) = 0.5:
        # pn = sqrt(2) - 1
        for ageName in ['1-5 months', '6-11 months', '12-23 months', '24-59 months']:
            self.assertAlmostEqual(self.testDerived.probStuntedIfPrevStunted["notstunted"][ageName], numpy.sqrt(2)-1)
        
    def testRelationshipBetweenStuntingProbabilitiesWhenORis2(self):
        # this relationship between ps and pn comes from the OR definition
        # ps = OR * pn / (1 - pn + (OR * pn)) 
        for ageName in ['1-5 months', '6-11 months', '12-23 months', '24-59 months']:
            ps = 2 * self.testDerived.probStuntedIfPrevStunted["notstunted"][ageName] / (1 + self.testDerived.probStuntedIfPrevStunted["notstunted"][ageName])
            self.assertAlmostEqual(self.testDerived.probStuntedIfPrevStunted["yesstunted"][ageName], ps)
           
    def testDiarrheaRiskSum(self):
        riskSum = self.testDerived.getDiarrheaRiskSum('24-59 months', self.testData.breastfeedingDistribution)        
        self.assertEqual(1., riskSum)
        
    def testGetZa(self):
        # Za = incidence / riskSum; riskSum = 1
        incidence = {'<1 month':1, '1-5 months':1, '6-11 months':1, '12-23 months':1, '24-59 months':1}
        Za = self.testDerived.getZa(incidence, self.testData.breastfeedingDistribution)
        self.assertEqual(incidence, Za)   

    def testGetAOGivenZa(self):
        # for neonatal:  OR = 1.04, RR = 1, alpha = 1, set Z = 1
        # AO[0] = OR ^ (RR * Z * alpha)
        z = {'<1 month':1, '1-5 months':1, '6-11 months':1, '12-23 months':1, '24-59 months':1}
        AO = self.testDerived.getAverageOR(z) 
        self.assertEqual(AO['<1 month'], 1.04)
           
    @unittest.skip("write test once quartic is solved")            
    def testGetBaselineBirthOutcome(self):
        # need to write tests for this once quartic equation is solved
         self.assertTrue(False)
         
 
class TestsForModelClass(unittest.TestCase):
    def setUp(self):
        [self.testData, self.testModel, self.testDerived, self.testParams, self.keyList] = setupDataModelDerivedParameters()
        

    def testApplyMortalityOneBox(self):
        # deaths = popsize * mortality * timestep
        #popsize = 100, mortality = 6., timestep = 1/12
        self.helper = helper.Helper()
        gaussianStuntingDist = self.helper.restratify(0.5) 
        initialPopSize = gaussianStuntingDist['high'] * 0.25 * 0.25 * 6400 
        self.testModel.applyMortality()
        popSize = self.testModel.listOfAgeCompartments[0].dictOfBoxes['high']['mild']['none'].populationSize
        cumulativeDeaths = self.testModel.listOfAgeCompartments[0].dictOfBoxes['high']['mild']['none'].cumulativeDeaths
        self.assertAlmostEqual(initialPopSize * 6. / 12., cumulativeDeaths)
        self.assertAlmostEqual(initialPopSize - (initialPopSize * 6. / 12.), popSize)
    
    @unittest.skip("underlying mortalites all set to zero except for neonatals")
    def testApplyMortalityBySummingAllBoxes(self):
        self.testModel.applyMortality()
        for iAge in range(0, len(self.testModel.listOfAgeCompartments)):
            sumPopSize = 0.
            sumCumulativeDeaths = 0.
            for stuntingCat in ["normal", "mild", "moderate", "high"]:
                for wastingCat in ["normal", "mild", "moderate", "high"]:
                    for breastfeedingCat in ["exclusive", "predominant", "partial", "none"]:
                        sumPopSize += self.testModel.listOfAgeCompartments[iAge].dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].populationSize
                        sumCumulativeDeaths += self.testModel.listOfAgeCompartments[iAge].dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat].cumulativeDeaths
            self.assertAlmostEqual(64. * (100.*0.5/12.), sumCumulativeDeaths)
            self.assertAlmostEqual(64. * (100. - (100.*0.5/12.)), sumPopSize)
            
    def testApplyAgingForNewbornsOnly(self):
        self.testModel.applyAging()
        self.assertEqual(0., self.testModel.listOfAgeCompartments[0].dictOfBoxes['mild']['high']['predominant'].populationSize)
        
    def testApplyAging(self):
        # sum aging out age[0] should equal sum aging in age[1]   
        # calculate what we expect        
        sumAgeingOutAge0 = 6400. * (1./1.) 
        sumAgeingOutAge1 = 32000. * (1./5.) 
        expectedSumPopAge1 = 32000. - sumAgeingOutAge1 + sumAgeingOutAge0
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
        self.testModel.derived.referenceMortality['12-23 months']["Diarrhea"] = 1
        self.testModel.updateMortalityRate()
        updatedMortalityRate = self.testModel.listOfAgeCompartments[3].dictOfBoxes['normal']['normal']['none'].mortalityRate
        expectedMortalityRate = 1. 
        self.assertEqual(expectedMortalityRate, updatedMortalityRate)
         
         
class TestsForHelperClass(unittest.TestCase):
    def setUp(self):
        self.helper = helper.Helper()
        [self.testData, self.testModel, self.testDerived, self.testParams, self.keyList] = setupDataModelDerivedParameters()
        self.agingRateList = [1./1., 1./5., 1./6., 1./12., 1./36.] 
        self.agePopSizes  = [6400, 6400, 6400, 6400, 6400]    
        self.gaussianStuntingDist = self.helper.restratify(0.5)         
             
    def testRestratifyWhenFractionYesIsHalf(self):
        # if FractionYes = 0.5 then (symmetric normal) distribution is centred at global mean -2 SD
        # therefore we expect moderate = normal and mild = high
        stratification = self.helper.restratify(0.5)
        self.assertEqual(stratification['moderate'], stratification['mild'])
        self.assertEqual(stratification['normal'], stratification['high'])
        
    def testMakeBoxes(self):
        # 0.25 * 0.25 * 0.25 * 6400 = 100
        # but we gaussianise the stunting dist now so..
        expected = self.gaussianStuntingDist['normal'] * 0.25 * 0.25 * 6400
        boxes = self.helper.makeBoxes(6400, '6-11 months', self.testData)   
        self.assertEqual(expected, boxes['normal']['normal']['none'].populationSize)

    def testMakeAgeCompartment(self):
        listOfAgeCompartments = self.helper.makeAgeCompartments(self.agePopSizes, self.testData)        
        self.assertAlmostEqual(5, len(listOfAgeCompartments))
        expected = self.gaussianStuntingDist['normal'] * 0.25 * 0.25 * 6400
        self.assertAlmostEqual(expected, listOfAgeCompartments[2].dictOfBoxes['normal']['normal']['none'].populationSize)
        
    def testsetupModelDerivedParameters(self):
        self.assertEqual(self.testDerived.initialStuntingTrend, self.testModel.derived.initialStuntingTrend)
        self.assertEqual(self.testParams.stuntingDistribution['1-5 months'], self.testModel.params.stuntingDistribution['1-5 months'])
    
# this needs to be here for the tests to run automatically    
if __name__ == '__main__':
    unittest.main()    
