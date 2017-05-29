import unittest
import data
import helper

# This script will test code in derived.py

# TODO suggestion: in order to test for many different values,
# TODO create different spreadsheets and associate different tests with them

def setUpDataModelConstantsParameters():
    path = '/Users/samhainsworth/Desktop/Github Projects/InputForCode_tests.xlsx'
    helperTests = helper.Helper()
    testData = data.readSpreadsheet(path, helperTests.keyList)
    testModel, testDerived, testParams = helperTests.setupModelConstantsParameters(testData)
    return testData, testModel, testDerived, testParams, helperTests.keyList


class TestDerivedClass(unittest.TestCase):

    @classmethod  # allows to call this only once for all tests
    def setUpClass(cls):
        # call this to set up derived
        cls.helper = helper.Helper()
        [cls.testData, cls.testModel, cls.testDerived, cls.testParams,
         cls.keyList] = setUpDataModelConstantsParameters()
        cls.reproductiveAges = ['15-19 years', '20-24 years', '25-29 years', '30-34 years', '35-39 years', '40-44 years']
        cls.causesOfDeath = ['Neonatal diarrhea', 'Neonatal sepsis', 'Neonatal pneumonia', 'Neonatal asphyxia',
                             'Neonatal prematurity', 'Neonatal tetanus', 'Neonatal congenital anormalies',
                             'Neonatal other', 'Diarrhea', 'Pneumonia', 'Meningitis', 'Measles', 'Malaria',
                             'Pertussis', 'AIDS', 'Injury', 'Other', 'maternal: Antepartum hemorrhage',
                             'maternal: Intrapartum hemorrhage', 'maternal: Postpartum hemorrhage',
                             'maternal: Hypertensive disorders', 'maternal: Sepsis', 'maternal: Abortion',
                             'maternal: Embolism', 'maternal: Other direct causes', 'maternal: Indirect causes',
                             'WRA: cause1', 'WRA: cause2', 'WRA: cause3']

    #############
    # Tests for setReferenceMortality
    # Uses RR & distributions of each mortality risk factor
    # Make sure any changes to test spreadsheet added here
    # All these updated in function call above (self.testData)

    def testWRAReferenceMortality(self):
        # if all RR values are 1, then should just return original distribution of mortality risk factors
        for age in self.reproductiveAges:
            for cause in self.causesOfDeath:
                refMort = self.testDerived.referenceMortality[age][cause]
                expectedRefMort = self.testData.causeOfDeathDist[age][cause]
                self.assertAlmostEqual(expectedRefMort, refMort)

    def testPregnantWomenReferenceMortality(self):
        # should be the adjusted value of mortality multiplied by the mortality distribution
        popName = 'pregnant women'
        popSize = self.testData.demographics['number of pregnant women']
        numBirths = self.testData.demographics['number of live births']
        pregnantWomenMortality = self.testData.rawMortality['pregnant women']
        numPregnantWomenDeaths = numBirths * pregnantWomenMortality / 1000
        fractionPregnantWomenMortality = numPregnantWomenDeaths / popSize
        for cause in self.causesOfDeath:
            expectedRefMort = fractionPregnantWomenMortality * self.testData.causeOfDeathDist['pregnant women'][cause]
            refMort = self.testDerived.referenceMortality[popName][cause]
            self.assertAlmostEqual(expectedRefMort, refMort)
    

if __name__ == "__main__":
    unittest.main()