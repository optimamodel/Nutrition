# -*- coding: utf-8 -*-
"""
Created on Fri April 1 2016

@author: madhura
"""
from __future__ import division
from copy import deepcopy as dcp

class Params:
    def __init__(self, data, derived, keyList):
        self.derived = derived

        for key in keyList.keys():
            setattr(self, key, keyList[key])

        self.causesOfDeath = dcp(data.causesOfDeath)
        self.conditions = dcp(data.conditions)
        self.demographics = dcp(data.demographics)
        self.causeOfDeathDist = dcp(data.causeOfDeathDist)
        self.stuntingDistribution = dcp(data.stuntingDistribution)
        self.wastingDistribution = dcp(data.wastingDistribution)
        self.breastfeedingDistribution = dcp(data.breastfeedingDistribution)
        self.anemiaDistribution = dcp(data.anemiaDistribution)
        self.fracPoor = dcp(data.demographics['fraction food insecure (default poor)'])
        self.fracNotPoor = 1 - self.fracPoor
        self.fracAnemicNotPoor = dcp(data.fracAnemicNotPoor)
        self.fracAnemicPoor = dcp(data.fracAnemicPoor)
        self.fracAnemicExposedMalaria = dcp(data.fracAnemicExposedMalaria)
        self.fracExposedMalaria = dcp(data.fracExposedMalaria)
        self.RRdeathStunting = dcp(data.RRdeathStunting)
        self.RRdeathWasting = dcp(data.RRdeathWasting)
        self.RRdeathBreastfeeding = dcp(data.RRdeathBreastfeeding)
        self.RRdeathByBirthOutcome = dcp(data.RRdeathByBirthOutcome)
        self.RRdeathAnemia = dcp(data.RRdeathAnemia)
        self.incidences = dcp(data.incidences)
        self.birthOutcomeDist = dcp(data.birthOutcomeDist)
        self.ageAppropriateBreastfeeding = dcp(data.ageAppropriateBreastfeeding)
        self.coverage = dcp(data.coverage)
        self.effectivenessMortality = dcp(data.effectivenessMortality)
        self.affectedFraction = dcp(data.affectedFraction)
        self.effectivenessIncidence = dcp(data.effectivenessIncidence)
        self.interventionsBirthOutcome = dcp(data.interventionsBirthOutcome)
        self.foodSecurityGroups = dcp(data.foodSecurityGroups)
        self.projectedBirths = dcp(data.projectedBirths)
        self.projectedWRApop = dcp(data.projectedWRApop)
        self.projectedWRApopByAge = dcp(data.projectedWRApopByAge)
        self.projectedPWpop = dcp(data.projectedPWpop)
        self.projectedGeneralPop = dcp(data.projectedGeneralPop)
        self.PWageDistribution = dcp(data.PWageDistribution)
        self.fracSevereDia = dcp(data.fracSevereDia)
        self.rawTargetPop = dcp(data.targetPopulation)
    

# Add all functions for updating parameters due to interventions here....

    def getMortalityUpdate(self, newCoverage):
        mortalityUpdate = {}
        for pop in self.allPops:
            mortalityUpdate[pop] = {}
            for cause in self.causesOfDeath:
                mortalityUpdate[pop][cause] = 1.
        for pop in self.allPops:
            for intervention in newCoverage.keys():
                for cause in self.causesOfDeath:
                    affectedFrac = self.affectedFraction[intervention][pop][cause]
                    effectiveness = self.effectivenessMortality[intervention][pop][cause]
                    newCoverageVal = newCoverage[intervention]
                    oldCoverage = self.coverage[intervention]
                    reduction = affectedFrac * effectiveness * (newCoverageVal - oldCoverage) / (1. - effectiveness*oldCoverage)
                    mortalityUpdate[pop][cause] *= 1. - reduction
        return mortalityUpdate       

        
    def getBirthOutcomeUpdate(self, newCoverage):
        birthOutcomeUpdate = {}
        for outcome in self.birthOutcomes:
            birthOutcomeUpdate[outcome] = 1.
        for intervention in newCoverage.keys():
            for outcome in self.birthOutcomes:
                affectedFrac = self.interventionsBirthOutcome[intervention][outcome]['affected fraction']
                effectiveness = self.interventionsBirthOutcome[intervention][outcome]['effectiveness']
                newCoverageVal = newCoverage[intervention]
                oldCoverage = self.coverage[intervention]
                reduction = affectedFrac * effectiveness * (newCoverageVal - oldCoverage) / (1. - effectiveness*oldCoverage)
                birthOutcomeUpdate[outcome] *= 1. - reduction
        return birthOutcomeUpdate               
        
        
    def getStuntingUpdate(self, newCoverage):
        stuntingUpdate = {}
        for ageName in self.ages:
            stuntingUpdate[ageName] = 1.
            oldProbStunting = self.stuntingDistribution[ageName]["high"] + self.stuntingDistribution[ageName]["moderate"]
            for intervention in newCoverage.keys():            
                probStuntingIfCovered    = self.derived.probStuntedIfCovered[intervention]["covered"][ageName]
                probStuntingIfNotCovered = self.derived.probStuntedIfCovered[intervention]["not covered"][ageName]
                newProbStunting = newCoverage[intervention]*probStuntingIfCovered + (1.-newCoverage[intervention])*probStuntingIfNotCovered
                reduction = (oldProbStunting - newProbStunting)/oldProbStunting
                stuntingUpdate[ageName] *= 1. - reduction
        return stuntingUpdate

    def getAnemiaUpdate(self, newCoverage):
        anemiaUpdate = {}
        malariaReduction = {}
        poorReduction = {}
        notPoorReduction = {}
        for pop in self.allPops:
            anemiaUpdate[pop] = 1.
            malariaReduction[pop] = 0.
            poorReduction[pop] = {}
            notPoorReduction[pop] = {}
            for intervention in newCoverage.keys():
                probAnemicIfCovered = self.derived.probAnemicIfCovered[intervention]["covered"][pop]
                probAnemicIfNotCovered = self.derived.probAnemicIfCovered[intervention]["not covered"][pop]
                
                # set the right coverage level
                if "fortification" in intervention and "salt" not in intervention:
                    thisCoverage = newCoverage[intervention] * (1.- self.demographics['fraction of subsistence farming'])
                else:    
                    thisCoverage = newCoverage[intervention]
                newProbAnemic = thisCoverage*probAnemicIfCovered + (1-thisCoverage)*probAnemicIfNotCovered
                
                # set the right old probability of being anemic
                if intervention == 'IPTp':
                    oldProbAnemic = self.fracAnemicExposedMalaria[pop]
                    reduction = (oldProbAnemic - newProbAnemic)/oldProbAnemic
                    malariaReduction[pop] = reduction
                elif "IFA poor" in intervention: 
                    oldProbAnemic = self.fracAnemicPoor[pop]
                    reduction = (oldProbAnemic - newProbAnemic)/oldProbAnemic
                    poorReduction[pop][intervention] = reduction
                elif "IFA not poor" in intervention: 
                    oldProbAnemic = self.fracAnemicNotPoor[pop]
                    reduction = (oldProbAnemic - newProbAnemic)/oldProbAnemic
                    notPoorReduction[pop][intervention] = reduction    
                else:    
                    oldProbAnemic = self.anemiaDistribution[pop]["anemic"]
                    reduction = (oldProbAnemic - newProbAnemic)/oldProbAnemic
                    anemiaUpdate[pop] *= 1. - reduction
        return anemiaUpdate, malariaReduction, poorReduction, notPoorReduction

    def addCoverageConstraints(self, newCoverages, listOfAgeCompartments, listOfReproductiveAgeCompartments):
        from copy import deepcopy as dcp
        constrainedCoverages = dcp(newCoverages)
        bednetCoverage = newCoverages['Long-lasting insecticide-treated bednets']
        
        # FIRST CALCULATE SOME USEFUL THINGS
        # calculate overlap of PPCF+iron target pop with sprinkles target pop
        targetSprikles = 0.
        targetPPCFiron = 0.
        targetSpriklesMalaria = 0.
        targetPPCFironMalaria = 0.
        for age in range(0, len(listOfAgeCompartments)):
            targetSprikles += self.rawTargetPop['Sprikles'][age] * listOfAgeCompartments[age].getTotalPopulation()
            targetPPCFiron += self.rawTargetPop['Public provision of complementary foods with iron'][age] * listOfAgeCompartments[age].getTotalPopulation()
            targetSpriklesMalaria += self.rawTargetPop['Sprikles (malaria area)'][age] * listOfAgeCompartments[age].getTotalPopulation()
            targetPPCFironMalaria += self.rawTargetPop['Public provision of complementary foods with iron (malaria area)'][age] * listOfAgeCompartments[age].getTotalPopulation()
        percentExtraPop = (targetSprikles - targetPPCFiron) / targetPPCFiron
        percentExtraPopMalaria = (targetSprikles - targetPPCFiron) / targetPPCFiron
        
        # calculate average anemia prevalence children and WRA
        thisList = []
        for age in range(0, len(listOfAgeCompartments)):
            thisList.append(age.getAnemicFraction())
        aveAnemicFracChildren = sum(thisList)/len(thisList)
        thisList = []
        for age in range(0, len(listOfReproductiveAgeCompartments)):
            thisList.append(age.getAnemicFraction())
        aveAnemicFracWRA = sum(thisList)/len(thisList)
        
        # NOW ADD ALL CONSTRAINTS
        for intervention in newCoverages.keys():
            # set bed net constraints for all WRA IFAS interventions            
            if 'IFAS' and 'malaria' in intervention:
                if 'bed nets' in intervention:
                    IFASmalariaBedNetCoverage = newCoverages[intervention]
                    if IFASmalariaBedNetCoverage > (1. - bednetCoverage):
                        constrainedCoverages[intervention] = (1. - bednetCoverage)
                elif 'bed nets' not in intervention:
                    IFASmalariaCoverage = newCoverages[intervention]
                    if IFASmalariaCoverage > bednetCoverage:
                        constrainedCoverages[intervention] = bednetCoverage
                        
            # add constraint on PPCF + iron in malaria area to allow maximum coverage to equal bednet coverage - do this before sprinkles constraint!        
            if 'Public provision of complementary foods with iron (malaria area)' in intervention:
                if newCoverages[intervention] > bednetCoverage:
                    constrainedCoverages[intervention] = bednetCoverage
            
            # add constraints on sprinkles coverage                
            # prioritise PPCF+iron over sprinkles, taking into accout extra pop which can be covered by sprinkles
            if 'Sprinkles' in intervention:
                if 'malaria' in intervention:
                    constrainedCoverages[intervention] = (1. - newCoverages['Public provision of complementary foods with iron (malaria area)']) * (1. + percentExtraPopMalaria)
                    if constrainedCoverages[intervention] > bednetCoverage:
                        constrainedCoverages[intervention] = bednetCoverage
                else:
                    constrainedCoverages[intervention] = (1. - newCoverages['Public provision of complementary foods with iron']) * (1. + percentExtraPop)
                # if anemia <20% set coverage to zero
                if aveAnemicFracChildren < 0.2:
                    constrainedCoverages[intervention] = 0.
                    
            # add constraints on vitamin A and zinc- neither can be given if sprikles already given.  Constrain sprinkles first!
            s1 = 'Sprinkles'
            s2 = 'Sprinkles (malaria area)'
            totalNumSprinkles = constrainedCoverages[s1] * targetSprikles + constrainedCoverages[s2] * targetSpriklesMalaria                
            totalConstrainedSprinklesCov = totalNumSprinkles/(targetSprikles + targetSpriklesMalaria)        
            if newCoverages['Vitamin A supplementation'] > (1. - totalConstrainedSprinklesCov):
                constrainedCoverages['Vitamin A supplementation'] = (1. - totalConstrainedSprinklesCov)
            if newCoverages['Zinc supplementation'] > (1. - totalConstrainedSprinklesCov):
                constrainedCoverages['Zinc supplementation'] = (1. - totalConstrainedSprinklesCov)    
             
            #
             
                        
        return constrainedCoverages

    def getAppropriateBFNew(self, newCoverage):
        correctbfFracNew = {}
        for ageName in self.ages:
            correctPractice = self.ageAppropriateBreastfeeding[ageName]
            correctbfFracBefore = self.breastfeedingDistribution[ageName][correctPractice]
            correctbfFracNew[ageName] = correctbfFracBefore
            for intervention in newCoverage.keys():
                probCorrectIfCovered    = self.derived.probCorrectlyBreastfedIfCovered[intervention]["covered"][ageName]
                probCorrectIfNotCovered = self.derived.probCorrectlyBreastfedIfCovered[intervention]["not covered"][ageName]
                correctbfFracNewThis = newCoverage[intervention]*probCorrectIfCovered + (1.-newCoverage[intervention])*probCorrectIfNotCovered
                fracAdd = correctbfFracNewThis - correctbfFracBefore
                correctbfFracNew[ageName] += fracAdd
        return correctbfFracNew               

            
    def getIncidenceUpdate(self, newCoverage):
        incidenceUpdate = {}
        for ageName in self.ages:
            incidenceUpdate[ageName] = {}
            for condition in self.conditions:
                incidenceUpdate[ageName][condition] = 1.
        for ageName in self.ages:
            for intervention in newCoverage.keys():
                for condition in self.conditions:
                    affectedFrac = self.affectedFraction[intervention][ageName][condition]
                    effectiveness = self.effectivenessIncidence[intervention][ageName][condition]
                    newCoverageVal = newCoverage[intervention]
                    oldCoverage = self.coverage[intervention]
                    reduction = affectedFrac * effectiveness * (newCoverageVal - oldCoverage) / (1. - effectiveness*oldCoverage)
                    incidenceUpdate[ageName][condition] *= 1. - reduction
        return incidenceUpdate                         

    def getUpdatesDueToIncidence(self, beta):
        stuntingUpdate = {}
        anemiaUpdate = {}
        for ageName in self.ages:
            # stunting
            stuntingUpdate[ageName] = 1.
            newProbStunting = 0
            oldProbStunting = self.stuntingDistribution[ageName]["high"] + self.stuntingDistribution[ageName]["moderate"]
            # anemia
            anemiaUpdate[ageName] = 1.
            newProbAnemia = 0
            oldProbAnemia = self.anemiaDistribution[ageName]["anemia"]
            for breastfeedingCat in self.breastfeedingList:
                pab = self.breastfeedingDistribution[ageName][breastfeedingCat]
                # stunting
                t1 = beta[ageName][breastfeedingCat] * self.derived.fracStuntedIfDiarrhea["dia"][ageName]
                t2 = (1 - beta[ageName][breastfeedingCat]) * self.derived.fracStuntedIfDiarrhea["nodia"][ageName]                
                newProbStunting += pab * (t1 + t2)
                # anemia
                t1 = beta[ageName][breastfeedingCat] * self.derived.fracAnemicIfDiarrhea["dia"][ageName]
                t2 = (1 - beta[ageName][breastfeedingCat]) * self.derived.fracAnemicIfDiarrhea["nodia"][ageName]                
                newProbAnemia += pab * (t1 + t2)
            # stunting    
            reductionStunting = (oldProbStunting - newProbStunting)/oldProbStunting 
            stuntingUpdate[ageName] *= 1. - reductionStunting
            # anemia
            reductionAnemia = (oldProbAnemia - newProbAnemia)/oldProbAnemia
            anemiaUpdate[ageName] *= 1. - reductionAnemia                
        return stuntingUpdate, anemiaUpdate
        
    def getStuntingUpdateComplementaryFeeding(self, newCoverage):
        stuntingUpdate = {}
        for ageName in self.ages:
            stuntingUpdate[ageName] = 1.      
        key1 = 'Complementary feeding education'
        key2 = 'Public provision of complementary foods'
        key3 = 'Public provision of complementary foods with iron'
        # collect data
        X1 = self.demographics['fraction food insecure (default poor)']
        X2 = 1.0 
        X3 = 0.0 
        Ce  = newCoverage[key1]
        Cse = newCoverage[key2] + newCoverage[key3]
        if Cse > 0.95: #::warning:: this is current saturation coverage
            Cse = 0.95
        # calculate fraction of children in each of the food security/access to intervention groups
        Frac = [0.]*4
        Frac[0] = X1*(1.-X2)*Ce + (1.-X1)*(1.-X3)*Ce + X1*(1.-X2)*(1.-Ce)*Cse
        Frac[1] = X1*(1.-X2)*(1.-Ce)*(1.-Cse) + (1.-X1)*(1.-X3)*(1.-Ce)
        Frac[2] = X1*X2*Cse + (1.-X1)*X3*Ce
        Frac[3] = X1*X2*(1.-Cse) + (1.-X1)*X3*(1.-Ce)
        # calculate stunting update
        for ageName in self.ages:
            oldProbStunting = self.stuntingDistribution[ageName]["high"] + self.stuntingDistribution[ageName]["moderate"]
            newProbStunting = 0
            for i in range(len(self.foodSecurityGroups)):            
                probStuntedThisGroup = self.derived.probStuntedComplementaryFeeding[ageName][self.foodSecurityGroups[i]]
                newProbStunting += probStuntedThisGroup * Frac[i]
            reduction = (oldProbStunting - newProbStunting)/oldProbStunting
            stuntingUpdate[ageName] *= 1. - reduction
        return stuntingUpdate           
