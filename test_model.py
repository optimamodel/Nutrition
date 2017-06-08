# This script tests the code in model.py

import os
import unittest
import data
import helper
from copy import deepcopy as dcp

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
                                                      ageName in self.keyList['allPops']}
        tmpAnemiaOR = self.testDerived.data.ORanemiaIntervention
        self.testDerived.data.ORanemiaIntervention = {ageName: {intervention: 1.5 for intervention in coverages.keys()} for
                                                      ageName in self.keyList['allPops']}
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





if __name__ == "__main__":
    unittest.main()



