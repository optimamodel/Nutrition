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

    def testMortalityIfCoverageIsZero(self):
        # expect the update to be 0
        coverages = self.testParams.coverage
        newCoverages = {intervention: 0. for intervention in coverages.key()}
        mortalityUpdate = self.testParams.getMortalityUpdate(newCoverages)
        expectedUpdate = 0.
        self.assertAlmostEqual(expectedUpdate, mortalityUpdate)









