import unittest
import numpy as np
import helper
import data

# This script will test code in helper.py

def setUpDataModelConstantsParameters():
    path = '/Users/samhainsworth/Desktop/Github Projects/InputForCode_tests.xlsx'
    helperTests = helper.Helper()
    testData = data.readSpreadsheet(path, helperTests.keyList)
    testModel, testDerived, testParams = helperTests.setupModelConstantsParameters(testData)
    return testData, testModel, testDerived, testParams, helperTests.keyList


class TestHelperClass(unittest.TestCase):
    @classmethod    # allows to call this only once for all tests
    def setUpClass(cls):
        cls.helper = helper.Helper()
        [cls.testData, cls.testModel, cls.testDerived, cls.testParams, cls.keyList] = setUpDataModelConstantsParameters()
        cls.ages = ["<1 month", "1-5 months", "6-11 months", "12-23 months", "24-59 months"]
        cls.anemiaList = {"anemic", "not anemic"}
        cls.deliveryList = {"unassisted", "assisted at home", "essential care", "BEmOC", "CEmOC"}
        cls.wastingList = ["obese", "normal", "mild", "moderate", "high"]
        cls.stuntingList = ["normal", "mild", "moderate", "high"]
        cls.breastfeedingList = ["exclusive", "predominant", "partial", "none"]
        cls.anemiaDist = {"anemic": 0.5, "not anemic": 0.5}
        cls.stuntingDist = {"normal": 0.25, "mild": 0.25, "moderate": 0.25, "high": 0.25}
        cls.wasingDist = {"obese": 0.2, "normal": 0.2, "mild": 0.2, "moderate": 0.2, "high": 0.2}
        cls.breastfeedingDist = {"exclusive": 0.25, "predominant": 0.25, "partial": 0.25, "none": 0.25}
        cls.deliveryDist = {"unassisted": 0.2, "assisted at home": 0.2, "essential care": 0.2, "BEmOC": 0.2, "CEmOC": 0.2}

        return

    #############
    # Tests for makePregnantWomenBoxes

    def testAllBoxesExist(self):
        # Test all stratifications exist & none additional
        boxes = self.helper.makePregnantWomenBoxes(self.testData)
        anemiaKeys = set()
        deliveryKeys = set()
        for key, value in boxes.items():
            anemiaKeys.add(key)
            for k, v in value.items():
                deliveryKeys.add(k)
        self.assertTrue((anemiaKeys == self.anemiaList) & (deliveryKeys == self.deliveryList))

    def testPopulationSize(self):
        # Test population size of each box
        boxes = self.helper.makePregnantWomenBoxes(self.testData)
        expectedTotalPop = 1000000 # 1 mil
        for anemiaStatus in self.anemiaList:
            for deliveryStatus in self.deliveryList:
                expectedPop = expectedTotalPop * self.deliveryDist[deliveryStatus] * self.anemiaDist[anemiaStatus]
                self.assertEqual(expectedPop, boxes[anemiaStatus][deliveryStatus].populationSize)

    ###############
    # Tests for makePregnantWomen

    def testBoxAttributes(self):
        # ensure birth rate, annual growth set correctly
        expectedPregnancies = 1000000. # 1mil
        expectedBirths = 3000000. # 3 mil
        expectedBirthRate = expectedBirths/expectedPregnancies
        expectedProjectedBirths = [3000000.]*14
        numYears = len(expectedProjectedBirths)-1
        expectedAnnualGrowth = (expectedProjectedBirths[numYears]-expectedProjectedBirths[0])/float(numYears)/expectedProjectedBirths[0]
        pregnantWomen = self.helper.makePregnantWomen(self.testData)
        self.assertEqual(pregnantWomen.annualGrowth, expectedAnnualGrowth)
        self.assertEqual(pregnantWomen.birthRate, expectedBirthRate)

    ################
    # Tests for makeAgePopSizes

    def testAgePopulationSize(self):
        # TODO The method this is supposed to test is pretty hard to follow
        expectedAgePopSizes = []

    #################
    # Tests for makeAgeCompartments

    def testCompartmentListLength(self):
        agePopSizes = self.helper.makeAgePopSizes(self.testData)
        listOfAgeCompartments = self.helper.makeAgeCompartments(agePopSizes, self.testData)
        self.assertEqual(5, len(listOfAgeCompartments))

    ##################
    # Tests for makeBoxes
    def testTotalPopulation(self):
        # make sure all boxes add to original pop size
        agePopSizes = self.helper.makeAgePopSizes(self.testData)
        self.assertEqual(15000000, sum(agePopSizes))
        for i in range(len(agePopSizes)):
            boxes = self.helper.makeBoxes(agePopSizes[i], self.ages[i], self.testData)
            popSize = boxes.getTotalPopulation # TODO issue here
            self.assertEqual(popSize, agePopSizes[i])



    def testAgeBoxPopulationSize(self):
        agePopSizes = self.helper.makeAgePopSizes(self.testData)
        for ind in range(len(agePopSizes)):
            for stuntingCat in self.stuntingList:
                for wastingCat in self.wastingList:
                    for breastfeedingCat in self.breastfeedingList:
                        for anemiaStatus in self.anemiaList:
                            expectedPop = agePopSizes[ind] * self.stuntingDist[stuntingCat] * \
                                          self.wasingDist[wastingCat] * self.breastfeedingDist[breastfeedingCat] * \
                                          self.anemiaDist[anemiaStatus]
                            box = self.helper.makeBoxes(agePopSizes[ind], self.ages[ind], self.testData)
                            popSize = box[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus].populationSize # TODO issue here
                            self.assertEqual(expectedPop, popSize)


if __name__ == "__main__":
    unittest.main()
