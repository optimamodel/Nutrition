import os
import unittest
import numpy as np
import helper
import data

# This script will test code in helper.py
# Note: attributes for boxes like mortality rate not tested
# because requires more sophisticated calculation that is better served in testing derived.py

def setupDataModelDerivedParameters():
    cwd = os.getcwd()
    path = cwd + '/input_spreadsheets/testingSpreadsheets/InputForCode_helperTests.xlsx'
    helperTests = helper.Helper()
    testData = data.readSpreadsheet(path, helperTests.keyList)
    testModel, testDerived, testParams = helperTests.setupModelDerivedParameters(testData)
    return testData, testModel, testDerived, testParams, helperTests.keyList


class TestHelperClass(unittest.TestCase):
    @classmethod    # allows to call this only once for all tests
    def setUpClass(cls):
        cls.helper = helper.Helper()
        [cls.testData, cls.testModel, cls.testDerived, cls.testParams, cls.keyList] = setupDataModelDerivedParameters()
        cls.ages = ["<1 month", "1-5 months", "6-11 months", "12-23 months", "24-59 months"]
        cls.anemiaList = {"anemic", "not anemic"}
        cls.deliveryList = {"unassisted", "assisted at home", "essential care", "BEmOC", "CEmOC"}
        cls.wastingList = ["obese", "normal", "mild", "moderate", "high"]
        cls.breastfeedingList = ["exclusive", "predominant", "partial", "none"]
        cls.anemiaDist = {"anemic": 0.5, "not anemic": 0.5}
        cls.stuntingDist = {"normal": 0.25, "mild": 0.25, "moderate": 0.25, "high": 0.25}
        cls.wasingDist = {"obese": 0.2, "normal": 0.2, "mild": 0.2, "moderate": 0.2, "high": 0.2}
        cls.breastfeedingDist = {"exclusive": 0.25, "predominant": 0.25, "partial": 0.25, "none": 0.25}
        cls.deliveryDist = {"unassisted": 0.2, "assisted at home": 0.2, "essential care": 0.2, "BEmOC": 0.2, "CEmOC": 0.2}
        # restratify stunting dist
        cls.stuntingList = ["normal", "mild", "moderate", "high"]
        cls.restratifiedStuntingDist = {}
        for ageName in cls.ages:
            probStunting = cls.helper.sumStuntedComponents(cls.testData.stuntingDistribution[ageName])
            cls.restratifiedStuntingDist[ageName] = cls.helper.restratify(probStunting)


    ############
    # Tests for restratify of stunting distribution
    # Test for different fractionYes values

    def testRestratifyWhenFractionYesIsHalf(self):
        # if FractionYes = 0.5 then (symmetric normal) distribution is centred at global mean -2 SD
        # therefore we expect moderate = normal and mild = high
        stratification = self.helper.restratify(0.5)
        self.assertEqual(stratification['moderate'], stratification['mild'])
        self.assertEqual(stratification['normal'], stratification['high'])

    def testRestratifyWhenFractionYesIsZero(self):
        # expect everyone to be 'normal'
        stratification = self.helper.restratify(0.)
        self.assertEqual(stratification['normal'], 1.0)
        self.assertEqual(stratification['moderate'], 0.)
        self.assertEqual(stratification['mild'], 0.)
        self.assertEqual(stratification['high'], 0.)

    def testRestratifyWhenFractionYesIsOne(self):
        # expect everyone to be stunted
        stratification = self.helper.restratify(1.)
        self.assertEqual(stratification['normal'], 0.)
        self.assertEqual(stratification['moderate'], 0.)
        self.assertEqual(stratification['mild'], 0.)
        self.assertEqual(stratification['high'], 1.0)


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
        expectedTotalPop = 1000000. # 1 mil
        for anemiaStatus in self.anemiaList:
            for deliveryStatus in self.deliveryList:
                expectedPop = expectedTotalPop * self.deliveryDist[deliveryStatus] * self.anemiaDist[anemiaStatus]
                self.assertAlmostEqual(expectedPop, boxes[anemiaStatus][deliveryStatus].populationSize)

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
        expectedAgePopSizes = []

    #################
    # Tests for makeAgeCompartments

    def testCompartmentListLength(self):
        agePopSizes = self.helper.makeAgePopSizes(self.testData)
        listOfAgeCompartments = self.helper.makeAgeCompartments(agePopSizes, self.testData)
        self.assertEqual(5, len(listOfAgeCompartments))


    def testAgePopSizes(self):
        # make sure total pop is maintained
        expectedTotalPop = 15000000.
        agePopSizes = self.helper.makeAgePopSizes(self.testData)
        self.assertAlmostEqual(expectedTotalPop, sum(agePopSizes))

    def testCompartmentListOrder(self):
        agePopSizes = self.helper.makeAgePopSizes(self.testData)
        listOfAgeCompartments = self.helper.makeAgeCompartments(agePopSizes, self.testData)
        nameOrder = []
        for compartment in listOfAgeCompartments:
            nameOrder += [compartment.name]
        expectedNameOrder = self.ages
        self.assertEqual(expectedNameOrder, nameOrder)

    ##################
    # Tests for makeBoxes

    def testTotalPopulation(self):
        # make sure all boxes add to original pop size
        expectedTotalPop = 15000000.
        agePopSizes = self.helper.makeAgePopSizes(self.testData)
        popSum = 0.
        for i in range(len(agePopSizes)):
            boxes = self.helper.makeBoxes(agePopSizes[i], self.ages[i], self.testData)
            # get the population size
            for stuntingCat in self.stuntingList:
                for wastingCat in self.wastingList:
                    for breastfeedingCat in self.breastfeedingList:
                        for anemiaStatus in self.anemiaList:
                            popSum += boxes[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus].populationSize
        self.assertAlmostEqual(popSum, expectedTotalPop)

    def testBoxesAttributes(self):
        agePopSizes = self.helper.makeAgePopSizes(self.testData)
        for index in range(len(agePopSizes)):
            for stuntingCat in self.stuntingList:
                for wastingCat in self.wastingList:
                    for breastfeedingCat in self.breastfeedingList:
                        for anemiaStatus in self.anemiaList:
                            expectedPopThisBox = agePopSizes[index] * self.restratifiedStuntingDist[self.ages[index]][stuntingCat] * \
                                          self.wasingDist[wastingCat] * self.breastfeedingDist[breastfeedingCat] * \
                                          self.anemiaDist[anemiaStatus]
                            box = self.helper.makeBoxes(agePopSizes[index], self.ages[index], self.testData)
                            popSize = box[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus].populationSize
                            self.assertAlmostEqual(expectedPopThisBox, popSize)

    #############
    # Tests for makeReproductiveAgeCompartments
    def testReproductiveCompartmentListLength(self):
        listOfReproductiveAgeCompartments = self.helper.makeReproductiveAgeCompartments(self.testData)
        self.assertEqual(6, len(listOfReproductiveAgeCompartments))

    def testReproductiveAgePopSizes(self):
        totalPopSize = 0.
        expectedPopSize = 10000000.
        listOfReproductiveAgeCompartments = self.helper.makeReproductiveAgeCompartments(self.testData)
        for age in listOfReproductiveAgeCompartments:
            for anemiaStatus in self.anemiaList:
                totalPopSize += age.dictOfBoxes[anemiaStatus].populationSize
        self.assertAlmostEqual(expectedPopSize, totalPopSize)

    def testReproductiveCompartmentsListOrder(self):
        listOfReproductiveAgeCompartments = self.helper.makeReproductiveAgeCompartments(self.testData)
        nameOrder = []
        for compartment in listOfReproductiveAgeCompartments:
            nameOrder += [compartment.name]
        expectedNameOrder = ["15-19 years", "20-24 years", "25-29 years", "30-34 years", "35-39 years", "40-44 years"]
        self.assertEqual(expectedNameOrder, nameOrder)


if __name__ == "__main__":
    unittest.main()
