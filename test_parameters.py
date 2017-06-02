# This script will test the code in parameters.py

import os
import unittest
import data
import helper
from copy import deepcopy as dcp

def setupDataModelDerivedParameters():
    cwd = os.getcwd()
    path = cwd + '/input_spreadsheets/testingSpreadsheets/InputForCode_modelTests.xlsx'
    helperTests = helper.Helper()
    testData = data.readSpreadsheet(path, helperTests.keyList)
    testModel, testDerived, testParams = helperTests.setupModelDerivedParameters(testData)
    return testData, testModel, testDerived, testParams, helperTests.keyList


class TestParamsClass(unittest.TestCase):

    @classmethod  # allows to call this only once for all tests
    def setUpClass(cls):
        # call this to set up model
        cls.helper = helper.Helper()
        [cls.testData, cls.testModel, cls.testDerived, cls.testParams,
         cls.keyList] = setupDataModelDerivedParameters()

    ################
    # Tests for getMortalityUpdate

    def testMortalityIfCoverageRemainsConstant(self):
        # expect that mortality won't change, hence mortalityUpdate =1
        coverages = self.testParams.coverage
        mortalityUpdate = self.testParams.getMortalityUpdate(coverages)
        expectedUpdate = 1.
        for pop in self.keyList['allPops']:
            for cause in self.testData.causesOfDeath:
                self.assertAlmostEqual(expectedUpdate, mortalityUpdate[pop][cause])

    def testMortalityIfCoverageDecreasesToZero(self):
        # Expect mortality rates to increase (>1)
        coverages = self.testParams.coverage
        newCoverages = {intervention: 0. for intervention in coverages.keys()}
        mortalityUpdate = self.testParams.getMortalityUpdate(newCoverages)
        for pop in self.keyList['allPops']:
            for cause in self.testData.causesOfDeath:
                self.assertGreaterEqual(mortalityUpdate[pop][cause], 1)

if __name__ == "__main__":
    unittest.main()





