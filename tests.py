# -*- coding: utf-8 -*-
"""
Created on Tue Mar 15 15:32:21 2016

@author: ruth
"""
import unittest
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
    agePopSizes  = [2.e5, 3.e5, 7.e5, 14.e5, 43.e5]
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
        self.assertEqual(100, self.testConstants.underlyingMortalityByAge['<1 month'])
        
    
    
    
if __name__ == '__main__':
    unittest.main()    