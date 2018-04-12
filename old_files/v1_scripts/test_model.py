# This script tests the code in model.py

import os
import unittest
import data
from old_files import helper


def setupDataModelDerivedParameters():
    cwd = os.getcwd()
    path = cwd + '/input_spreadsheets/testingSpreadsheets/InputForCode_mainTests.xlsx'
    helperTests = helper.Helper()
    testData = data.readSpreadsheet(path, helperTests.keyList)
    testModel, testDerived, testParams = helperTests.setupModelDerivedParameters(testData)
    return testData, testModel, testDerived, testParams, helperTests.keyList


class TestModelClass(unittest.TestCase):

    @classmethod  # allows to call this only once for all tests
    def setUpClass(cls):
        # call this to set up model
        cls.helper = helper.Helper()
        [cls.testData, cls.testModel, cls.testDerived, cls.testParams,
         cls.keyList] = setupDataModelDerivedParameters()
        cls.everyone = cls.keyList['allPops']


    ####################
    # Tests for updateCoverages

    def testMortalityIfCoverageIsZero(self):
        # We know (from test_parameters) that setting coverage to 0 will result in stunting/anemia update > 1
        coverages = self.testParams.coverage
        newCoverages = {intervention: 0. for intervention in coverages.keys()}
        self.testModel.updateCoverages(newCoverages)
        refMort = self.testModel.derived.referenceMortality
        for pop in self.keyList['allPops']:
            for cause in self.testData.causesOfDeath:
                self.assertLessEqual(refMort[pop][cause], 1.)

    def testMortalityIfCoverageIsZeroAndRRLargerThanOne(self):
        # Same as above but set RR/OR to be larger than 1
        # set tmp values
        coverages = self.testParams.coverage
        tmpAnemiaRR = self.testDerived.data.RRanemiaIntervention
        self.testDerived.data.RRanemiaIntervention = {ageName: {intervention: 1.5 for intervention in coverages.keys()} for
                                                      ageName in self.everyone}
        tmpAnemiaOR = self.testDerived.data.ORanemiaIntervention
        self.testDerived.data.ORanemiaIntervention = {ageName: {intervention: 1.5 for intervention in coverages.keys()} for
                                                      ageName in self.everyone}
        tmpStuntingOR = self.testDerived.data.ORstuntingIntervention
        self.testDerived.data.ORstuntingIntervention = {ageName: {intervention: 1.5 for intervention in coverages.keys()} for
                                                      ageName in self.keyList['allPops']}
        newCoverages = {intervention: 0. for intervention in coverages.keys()}
        self.testModel.updateCoverages(newCoverages)
        refMort = self.testModel.derived.referenceMortality
        for pop in self.keyList['allPops']:
            for cause in self.testData.causesOfDeath:
                self.assertLessEqual(refMort[pop][cause], 1.)
        # reset values
        self.testDerived.data.RRanemiaIntervention = tmpAnemiaRR
        self.testDerived.data.ORanemiaIntervention = tmpAnemiaOR
        self.testDerived.data.ORstuntingIntervention = tmpStuntingOR


    def testMortalityIfUpdatedTwice(self):
        # expect the same results if coverages are the same each time (but different to original coverages)
        coverages = self.testParams.coverage
        newCoverages = {intervention: 0.5 for intervention in coverages.keys()}
        self.testModel.updateCoverages(newCoverages)
        mortalityFirst = self.testModel.derived.referenceMortality
        self.testModel.updateCoverages(newCoverages)
        mortalitySecond = self.testModel.derived.referenceMortality
        self.assertDictEqual(mortalityFirst, mortalitySecond)


    #################
    # Tests for updateMortalityRate

    def testMortalityIfRRAndORAreZero(self):
        # spreadsheet with all zeros
        cwd = os.getcwd()
        path = cwd + '/input_spreadsheets/testingSpreadsheets/InputForCode_mainTests_RRandORzero.xlsx'
        helperTests = helper.Helper()
        testData = data.readSpreadsheet(path, helperTests.keyList)
        testModel, testDerived, testParams = helperTests.setupModelDerivedParameters(testData)
        testModel.updateMortalityRate()

    def testIfReferenceMortalityIsZero(self):
        # expect that all mortalities updated to 0
        refMort = self.testModel.derived.referenceMortality
        self.testModel.derived.referenceMortality = {ageName:
                                                         {cause: 0. for cause in self.testData.causesOfDeath}
                                                     for ageName in self.everyone}
        self.testModel.updateMortalityRate()
        for ageGroup in self.testModel.listOfAgeCompartments:
            for stuntingCat in self.keyList['stuntingList']:
                for wastingCat in self.keyList['wastingList']:
                    for breastfeedingCat in self.keyList['breastfeedingList']:
                        for anemiaStatus in self.keyList['anemiaList']:
                            ageMortality = ageGroup.dictOfBoxes[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus].mortalityRate
                            self.assertEqual(0., ageMortality)

        for ageGroup in  self.testModel.listOfReproductiveAgeCompartments:
            for anemiaStatus in self.keyList['anemiaList']:
                ageMortality = ageGroup.dictOfBoxes[anemiaStatus].mortalityRate
                self.assertEqual(0., ageMortality)

        for anemiaStatus in self.keyList['anemiaList']:
            for deliveryStatus in self.keyList['deliveryList']:
                ageMortality = self.testModel.pregnantWomen.dictOfBoxes[anemiaStatus][deliveryStatus].mortalityRate
                self.assertEqual(0., ageMortality)

        # reset
        self.testModel.derived.referenceMortality = refMort





if __name__ == "__main__":
    unittest.main()



