import os
import unittest
import data
import helper
from copy import deepcopy as dcp

# This script will test code in derived.py

def setUpDataModelConstantsParameters():
    cwd = os.getcwd()
    path = cwd + '/input_spreadsheets/testingSpreadsheets/InputForCode_derivedTests.xlsx'
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
        cls.ages = ["<1 month", "1-5 months", "6-11 months", "12-23 months", "24-59 months"]
        cls.anemiaList = {"anemic", "not anemic"}
        cls.deliveryList = {"unassisted", "assisted at home", "essential care", "BEmOC", "CEmOC"}
        cls.wastingList = ["obese", "normal", "mild", "moderate", "high"]
        cls.birthOutcomeList = ["Pre-term SGA", "Pre-term AGA", "Term SGA", "Term AGA"]
        cls.breastfeedingList = ["exclusive", "predominant", "partial", "none"]
        cls.anemiaDist = {"anemic": 0.5, "not anemic": 0.5}
        cls.stuntingDist = {"normal": 0.25, "mild": 0.25, "moderate": 0.25, "high": 0.25}
        cls.wasingDist = {"obese": 0.2, "normal": 0.2, "mild": 0.2, "moderate": 0.2, "high": 0.2}
        cls.breastfeedingDist = {"exclusive": 0.25, "predominant": 0.25, "partial": 0.25, "none": 0.25}
        cls.birthOutcomeDist = {"Pre-term SGA": 0.25, "Pre-term AGA": 0.25, "Term SGA": 0.25, "Term AGA": 0.25} # must sum to 1
        cls.deliveryDist = {"unassisted": 0.2, "assisted at home": 0.2, "essential care": 0.2, "BEmOC": 0.2, "CEmOC": 0.2}

    #############
    # Tests for setReferenceMortality (associated functions tested below)
    # Uses RR & distributions of each mortality risk factor
    # Make sure any changes to test spreadsheet added here
    # All these updated in function call above (self.testData)

    def testNewbornReferenceMortality(self):
        # With all RR set to 1, expected that it is RHS = product of distributions (summed for each cause & age)
        # Corrected mortality = rawMort * num births/1000./ population size
        # RHS
        refMort = self.testDerived.referenceMortality
        expectedRHS = {}
        for cause in self.causesOfDeath:
            expectedRHS[cause] = 0.
            for breastfeedingCat in self.breastfeedingList:
                for birthOutcome in self.birthOutcomeList:
                    for anemiaStatus in self.anemiaList:
                        expectedRHS[cause] += 0.25 * 0.25 * 0.5
        # LHS
        rawMort = 1.
        liveBirths = 3000000.
        popSize = self.helper.makeAgePopSizes(self.testData)[0]
        expectedCorrectedMortality = rawMort * liveBirths /1000. / popSize
        expectedRefMort = {}
        for cause in ['Neonatal diarrhea', 'Neonatal sepsis', 'Neonatal pneumonia', 'Neonatal asphyxia',
                       'Neonatal prematurity', 'Neonatal tetanus', 'Neonatal congenital anormalies',
                        'Neonatal other']:
            expectedLHS = expectedCorrectedMortality * 0.125
            expectedRefMort[cause] = expectedLHS/expectedRHS[cause]
            self.assertAlmostEqual(expectedRefMort[cause], refMort['<1 month'][cause])

    #def testOneToFiveReferenceMortality(self):
        # TODO: this is complicated b/c of age adjustments to all other child age compartments

    ##############
    # Tests for setReferenceWRAMortality & setReferencePregnantWomenMortality

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

    def testRefMortalityDictLength(self):
        refMort = self.testDerived.referenceMortality
        self.assertEqual(12, len(refMort.keys()))

    def testIfRawMortalityIsZero(self):
        #if raw mortality is 0 than reference mortality should be 0
        originalPops = ['under 5', 'neonatal', 'infant', 'pregnant women'] + self.reproductiveAges
        data = dcp(self.testData)
        # change raw mortalities to 0
        data.rawMortality = {age: 0. for age in originalPops}
        testModel, testDerived, testParams = self.helper.setupModelConstantsParameters(data)
        refMort = testDerived.referenceMortality
        for ageName in self.helper.keyList['allPops']:
            for cause in self.causesOfDeath:
                self.assertAlmostEqual(0., refMort[ageName][cause])

    def testIfRawMortalityIsMaximum(self): # TODO: think on this
        # children: 1000 deaths per 1000 births
        # pregnant women: 1000 deaths
        # WRA: 1 (?)
        # If mortality is 100% for all ages, we expect reference mortality
        # for each age to sum to 1 (i.e. whole population will die of a cause).
        data = dcp(self.testData)
        data.rawMortality['under 5'] = 1000.
        data.rawMortality['neonatal'] = 1000. * self.testModel.listOfAgeCompartments[0].getTotalPopulation() / self.testData.demographics['number of live births']
        data.rawMortality['infant'] = 1000.
        data.rawMortality['pregnant women'] = 1000.
        for name in self.reproductiveAges:
            data.rawMortality[name] = 1.
        testModel, testDerived, testParams = self.helper.setupModelConstantsParameters(data)
        refMort = testDerived.referenceMortality
        for ageName in self.helper.keyList['allPops']:
            mortalitySum = 0.
            for cause in self.causesOfDeath:
                mortalitySum += refMort[ageName][cause]
            #self.assertAlmostEqual(1., mortalitySum)


if __name__ == "__main__":
    unittest.main()