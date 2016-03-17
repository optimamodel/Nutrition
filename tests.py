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


def setUpDataAndModelObjects(self):
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
                    thisPopSize = int(agePopSize/64.) # WARNING need to distribute appropriately
                    thisMortalityRate = testData.totalMortalityByAge[age] # WARNING need to distribute appropriately
                    allBoxes[stuntingStatus][wastingStatus][breastfeedingStatus] =  model.Box(stuntingStatus, wastingStatus, breastfeedingStatus, thisPopSize, thisMortalityRate)
        compartment = model.AgeCompartment(ageRange, allBoxes, agingRate)
        listOfAgeCompartments.append(compartment)
    #------------------------------------------------------------------------    
    # make a model object
    testModel = model.Model("Main model", mothers, listOfAgeCompartments, testData.ages, timestep)
    return testData, testModel
    

class TestsForConstantsClass(unittest.TestCase):
    def setUp(self):
        [self.testData, self.testModel] = setUpDataAndModelObjects(self)
        self.testConstants = constants.Constants(self.testData, self.testModel)
        
    def testGetUnderlyingMortalityByAge(self):
        for age in self.testModel.ages:
            self.assertEqual(1./6400, self.testConstants.underlyingMortalityByAge[age])
        
    def testStuntingProbabilitiesEqualExpectedWhenORis2(self):
        # for OR = 2, assuming F(a) = F(a-1) = 0.5:
        # pn = sqrt(2) - 1
        for age in ['1-5 months', '6-11 months', '12-23 months', '24-59 months']:
            self.assertEqual(self.testConstants.probStuntedIfNotPreviously[age], numpy.sqrt(2)-1)
        
    def testRealtionshipBetweenStuntingProbabilitiesWhenORis2(self):
        # this relationship between ps and pn comes from the OR definition
        # ps = OR * pn / (1 - pn + (OR * pn)) 
        for age in ['1-5 months', '6-11 months', '12-23 months', '24-59 months']:
            ps = 2 * self.testConstants.probStuntedIfNotPreviously[age] / (1 + self.testConstants.probStuntedIfNotPreviously[age])
            self.assertEqual(self.testConstants.probStuntedIfPreviously[age], ps)
                
    def testGetBaselineBirthOutcome(self):
        # need to write tests for this once quartic equation is solved
         self.assertTrue(False)
    
    
    
if __name__ == '__main__':
    unittest.main()    