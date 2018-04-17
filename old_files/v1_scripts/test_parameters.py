# This script will test the code in parameters.py

import os
import unittest
from nutrition import data
from old_files import helper


def setupDataModelDerivedParameters():
    cwd = os.getcwd()
    path = cwd + '/input_spreadsheets/testingSpreadsheets/InputForCode_parametersTests.xlsx'
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

    def testMortalityIfCoverageIsSameAsOriginal(self):
        # expect that mortality won't change, hence mortalityUpdate =1
        coverages = self.testParams.coverage
        mortalityUpdate = self.testParams.getMortalityUpdate(coverages)
        expectedUpdate = 1.
        for pop in self.keyList['allPops']:
            for cause in self.testData.causesOfDeath:
                self.assertAlmostEqual(expectedUpdate, mortalityUpdate[pop][cause])

    def testMortalityIfCoverageDecreasesToZero(self):
        # Expect mortality rates to increase (>=1)
        coverages = self.testParams.coverage
        newCoverages = {intervention: 0. for intervention in coverages.keys()}
        mortalityUpdate = self.testParams.getMortalityUpdate(newCoverages)
        for pop in self.keyList['allPops']:
            for cause in self.testData.causesOfDeath:
                self.assertGreaterEqual(mortalityUpdate[pop][cause], 1)

    def testMortalityIfCoverageIncreasesFromZeroToOne(self):
        # expect mortality update to be product of all reductions for each intervention: (1-eff*affFrac)
        # affectedFrac & effectiveness = 1 so all updates will be 0
        coverages = self.testParams.coverage
        self.testParams.coverage = {intervention: 0. for intervention in coverages.keys()}
        newCoverages = {intervention: 1. for intervention in coverages.keys()}
        # set all affectedFrac & effectiveness to 1
        self.testParams.affectedFraction = {intervention: {pop: {cause: 1. for cause in self.testData.causesOfDeath}
                                            for pop in self.keyList['allPops']} for intervention in coverages.keys() }
        self.testParams.effectivenessMortality = {intervention: {pop: {cause: 1. for cause in self.testData.causesOfDeath}
                                            for pop in self.keyList['allPops']} for intervention in coverages.keys() }
        mortalityUpdate = self.testParams.getMortalityUpdate(newCoverages)
        for pop in self.keyList['allPops']:
            for cause in self.testData.causesOfDeath:
                self.assertAlmostEqual(0., mortalityUpdate[pop][cause])

    def testIfUpdateMortalityTwice(self):
        # keep coverages the same (but different from original coverage) and update twice
        # expect updates to be the same
        coverages = self.testParams.coverage
        newCoverages = {intervention: 0.5 for intervention in coverages.keys()}
        mortalityUpdateFirst = self.testParams.getMortalityUpdate(newCoverages)
        mortalityUpdateSecond = self.testParams.getMortalityUpdate(newCoverages)
        self.assertDictEqual(mortalityUpdateFirst, mortalityUpdateSecond)



    ####################
    # Tests for getStuntingUpdate

    def testStuntingIfCoverageIsSameAsOriginal(self):
        # expect reduction=0 so update=1
        coverages = self.testParams.coverage
        # set probability stunted if covered
        self.testDerived.setProbStuntedIfCovered(coverages, self.testData.stuntingDistribution)
        stuntingUpdate = self.testParams.getStuntingUpdate(coverages)
        for age in self.keyList['ages']:
            self.assertAlmostEqual(1., stuntingUpdate[age])

    def testStuntingIfCoverageDescreasesToZero(self):
        # expect stunting to increase (>=1)
        coverages = self.testParams.coverage
        # set probability stunted if covered
        self.testDerived.setProbStuntedIfCovered(coverages, self.testData.stuntingDistribution)
        newCoverages = {intervention: 0. for intervention in coverages.keys()}
        stuntingUpdate = self.testParams.getStuntingUpdate(newCoverages)
        for age in self.keyList['ages']:
            self.assertGreaterEqual(stuntingUpdate[age], 1.)

    def testStuntingIfCoverageIncreasesFromZeroToOne(self):
        # expect stunting to decrease (<=1)
        coverages = self.testParams.coverage
        newCoverages = {intervention: 0. for intervention in coverages.keys()}
        # set probability stunted if covered
        self.testDerived.setProbStuntedIfCovered(newCoverages, self.testData.stuntingDistribution)
        newCoverages = {intervention: 1. for intervention in coverages.keys()}
        stuntingUpdate = self.testParams.getStuntingUpdate(newCoverages)
        for age in self.keyList['ages']:
            self.assertLessEqual(stuntingUpdate[age], 1.)

    def testIfUpdateStuntingTwice(self):
        # keep coverages the same (but different from original coverage) and update twice
        # expect updates to be the same
        coverages = self.testParams.coverage
        newCoverages = {intervention: 0.5 for intervention in coverages.keys()}
        stuntingUpdateFirst = self.testParams.getMortalityUpdate(newCoverages)
        stuntingUpdateSecond = self.testParams.getMortalityUpdate(newCoverages)
        self.assertDictEqual(stuntingUpdateFirst, stuntingUpdateSecond)


    #########################
    # Tests for getStuntingUpdateDueToIncidence

    def testStuntingIfBetaIsOne(self):
        # proportion of children who experience x episodes of diarrhoea per month is 100%
        # expect newProbstunting = 1 (if values below also 1) & update is then 1 - (-1) = 2
        self.testDerived.fracStuntedIfDiarrhea['dia'] = {ageName: 1. for ageName in self.keyList['ages']}
        self.testDerived.fracStuntedIfDiarrhea['nodia'] = {ageName: 1. for ageName in self.keyList['ages']} # not used
        beta = {ageName: {feedingCat: 1. for feedingCat in self.keyList['breastfeedingList']} for ageName in self.keyList['ages']}
        update = self.testParams.getStuntingUpdateDueToIncidence(beta)
        expectedUpdate = 2.
        for age in self.keyList['ages']:
            self.assertAlmostEqual(update[age], expectedUpdate)

    def testStuntingIfBetaIsZero(self):
        # proportion of children who experience x episodes of diarrhoea per month is 0%
        # expect newProbstunting = 1 (if values below also 1) & update is then 1 - (-1) = 2
        self.testDerived.fracStuntedIfDiarrhea['dia'] = {ageName: 1. for ageName in self.keyList['ages']}
        self.testDerived.fracStuntedIfDiarrhea['nodia'] = {ageName: 1. for ageName in self.keyList['ages']} # not used
        beta = {ageName: {feedingCat: 0. for feedingCat in self.keyList['breastfeedingList']} for ageName in self.keyList['ages']}
        update = self.testParams.getStuntingUpdateDueToIncidence(beta)
        expectedUpdate = 2.
        for age in self.keyList['ages']:
            self.assertAlmostEqual(update[age], expectedUpdate)






if __name__ == "__main__":
    unittest.main()





