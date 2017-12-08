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
        self.projectedBirths = dcp(data.projectedBirths)
        self.projectedWRApop = dcp(data.projectedWRApop)
        self.projectedWRApopByAge = dcp(data.projectedWRApopByAge)
        self.projectedPWpop = dcp(data.projectedPWpop)
        self.projectedGeneralPop = dcp(data.projectedGeneralPop)
        self.PWageDistribution = dcp(data.PWageDistribution)
        self.fracSevereDia = dcp(data.fracSevereDia)
        self.rawTargetPop = dcp(data.targetPopulation)
        self.attendance = dcp(data.demographics['school attendance WRA 15-19'])
        self.interventionCompleteList = dcp(data.interventionCompleteList)
        self.fracSAMtoMAM = dcp(data.fracSAMtoMAM)
        self.fracMAMtoSAM = dcp(data.fracMAMtoSAM)
        self.IYCFprograms = dcp(data.IYCFprograms)
    

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

    def addSubpopConstraints(self, subpopProb, oldProb, fracTargeted):
        '''Uses law of total probability: Pr(A) = sum(Pr(A|B)*Pr(B))'''
        newProb = subpopProb * fracTargeted + oldProb * (1-fracTargeted)
        return newProb
        
    def getStuntingUpdate(self, newCoverage):
        stuntingUpdate = {}
        for ageName in self.ages:
            stuntingUpdate[ageName] = 1.
            oldProbStunting = self.stuntingDistribution[ageName]["high"] + self.stuntingDistribution[ageName]["moderate"]
            for intervention in newCoverage.keys():            
                probStuntingIfCovered    = self.derived.probStuntedIfCovered[intervention]["covered"][ageName]
                probStuntingIfNotCovered = self.derived.probStuntedIfCovered[intervention]["not covered"][ageName]
                newProbStunting = newCoverage[intervention]*probStuntingIfCovered + (1.-newCoverage[intervention])*probStuntingIfNotCovered
                if "Public provision" in intervention: # only give to fraction poor
                    newProbStunting = self.addSubpopConstraints(newProbStunting, oldProbStunting, self.fracPoor)
                reduction = (oldProbStunting - newProbStunting)/oldProbStunting
                stuntingUpdate[ageName] *= 1. - reduction
        return stuntingUpdate

    def getAnemiaUpdate(self, newCoverage, thisHelper):
        anemiaUpdate = {}
        fracTargetedIFAS = thisHelper.setIFASFractionTargetted(self.attendance, self.fracPoor, self.fracExposedMalaria, self.interventionCompleteList, newCoverage["Long-lasting insecticide-treated bednets"])
        interventionsPW = ['IPTp', 'Multiple micronutrient supplementation', 'Iron and folic acid supplementation for pregnant women']        
        for pop in self.allPops:
            anemiaUpdate[pop] = 1.
            for intervention in newCoverage.keys():
                probAnemicIfCovered = self.derived.probAnemicIfCovered[intervention]["covered"][pop]
                probAnemicIfNotCovered = self.derived.probAnemicIfCovered[intervention]["not covered"][pop]
                thisCoverage = newCoverage[intervention]
                newProbAnemic = thisCoverage*probAnemicIfCovered + (1-thisCoverage)*probAnemicIfNotCovered
                oldProbAnemic = self.anemiaDistribution[pop]["anemic"]
                # adjust newProbAnemic if necessary as newProbAnemic is amongst subgroup of age group in some cases
                # new prob age group = prob old * frac not targeted + prob new in subgroup * frac targeted
                # PW interventions
                if any(this in intervention for this in interventionsPW) and "PW" in pop:
                    if 'malaria area' in intervention:
                        fractionTargeted = self.fracExposedMalaria
                    elif 'IPTp' in intervention:
                        fractionTargeted = self.fracExposedMalaria
                    else:
                        fractionTargeted = 1. - self.fracExposedMalaria
                    fractionNotTargeted = 1. - fractionTargeted
                    newProbAnemic = fractionNotTargeted * oldProbAnemic + newProbAnemic * fractionTargeted    
                # sprinkles
                if any(this in pop for this in ["6-11 months", "12-23 months", "24-59 months"]) and "Sprinkles" in intervention:
                    if 'malaria area' in intervention:
                        fractionTargeted = self.fracExposedMalaria
                    else:
                        fractionTargeted = 1. - self.fracExposedMalaria
                    fractionNotTargeted = 1. - fractionTargeted
                    newProbAnemic = fractionNotTargeted * oldProbAnemic + newProbAnemic * fractionTargeted     
                # PPCF + iron
                if any(this in pop for this in ["6-11 months", "12-23 months"]) and "Public provision of complementary foods with iron" in intervention:
                    if 'malaria area' in intervention:
                        fractionTargeted = self.fracExposedMalaria
                    else:
                        fractionTargeted = 1. - self.fracExposedMalaria   
                    fractionNotTargeted = 1. - fractionTargeted
                    newProbAnemic = fractionNotTargeted * oldProbAnemic + newProbAnemic * fractionTargeted     
                # WRA IFAS
                if "IFAS" in intervention and "WRA" in pop: 
                    fractionTargeted = fracTargetedIFAS[pop][intervention]
                    fractionNotTargeted = 1. - fractionTargeted
                    newProbAnemic = fractionNotTargeted * oldProbAnemic + newProbAnemic * fractionTargeted
                # bed nets
                if "insecticide-treated bednets" in intervention:
                    fractionTargeted = self.fracExposedMalaria
                    fractionNotTargeted = 1. - fractionTargeted
                    newProbAnemic = fractionNotTargeted * oldProbAnemic + newProbAnemic * fractionTargeted
                # now calculate reduction    
                reduction = (oldProbAnemic - newProbAnemic)/oldProbAnemic
                anemiaUpdate[pop] *= 1. - reduction
        return anemiaUpdate

    def getWastingPrevalenceUpdate(self, newCoverage):
        wastingUpdate = {} # overall update to prevalence of MAM and SAM
        fromSAMtoMAMupdate = {} # accounts for children moving from SAM to MAM after SAM treatment
        fromMAMtoSAMupdate = {} # accounts for children moving from MAM to SAM after MAM treatment
        for ageName in self.ages:
            fromSAMtoMAMupdate[ageName] = {}
            fromMAMtoSAMupdate[ageName] = {}
            wastingUpdate[ageName] = {}
            for wastingCat in self.wastedList:
                fromSAMtoMAMupdate[ageName][wastingCat] = 1.
                fromMAMtoSAMupdate[ageName][wastingCat] = 1.
                wastingUpdate[ageName][wastingCat] = 1.
                oldProbWasting = self.wastingDistribution[ageName][wastingCat]
                for intervention in newCoverage.keys():
                    probWastingIfCovered = self.derived.probWastedIfCovered[wastingCat][intervention]["covered"][ageName]
                    probWastingIfNotCovered = self.derived.probWastedIfCovered[wastingCat][intervention]["not covered"][ageName]
                    newProbWasting = newCoverage[intervention]*probWastingIfCovered + (1.-newCoverage[intervention])*probWastingIfNotCovered
                    reduction = (oldProbWasting - newProbWasting) / oldProbWasting
                    wastingUpdate[ageName][wastingCat] *= 1. - reduction
            fromSAMtoMAMupdate[ageName]['MAM'] = (1. + (1.-wastingUpdate[ageName]['SAM']) * self.fracSAMtoMAM)
            fromMAMtoSAMupdate[ageName]['SAM'] = (1. - (1.-wastingUpdate[ageName]['MAM']) * self.fracMAMtoSAM)
        return wastingUpdate, fromSAMtoMAMupdate, fromMAMtoSAMupdate

    def addCoverageConstraints(self, newCoverages, listOfAgeCompartments, listOfReproductiveAgeCompartments):
        from copy import deepcopy as dcp
        constrainedCoverages = dcp(newCoverages)
        bednetCoverage = constrainedCoverages['Long-lasting insecticide-treated bednets']
        IPTpCoverage = constrainedCoverages['IPTp']
        
        # FIRST CALCULATE SOME USEFUL THINGS
        # calculate overlap of PPCF+iron target pop with sprinkles target pop
        targetSprinkles = 0.
        targetPPCFiron = 0.
        targetSprinklesMalaria = 0.
        targetPPCFironMalaria = 0.
        for age in range(0, len(listOfAgeCompartments)):
            ageName = listOfAgeCompartments[age].name
            targetSprinkles += self.rawTargetPop['Sprinkles'][ageName] * listOfAgeCompartments[age].getTotalPopulation()
            targetPPCFiron += self.rawTargetPop['Public provision of complementary foods with iron'][ageName] * listOfAgeCompartments[age].getTotalPopulation()
            targetSprinklesMalaria += self.rawTargetPop['Sprinkles (malaria area)'][ageName] * listOfAgeCompartments[age].getTotalPopulation()
            targetPPCFironMalaria += self.rawTargetPop['Public provision of complementary foods with iron (malaria area)'][ageName] * listOfAgeCompartments[age].getTotalPopulation()
        percentExtraPop = (targetSprinkles - targetPPCFiron) / targetPPCFiron
        percentExtraPopMalaria = (targetSprinklesMalaria - targetPPCFironMalaria) / targetPPCFironMalaria
        
        # calculate average anemia prevalence children and WRA
        thisList = []
        for age in range(0, len(listOfAgeCompartments)):
            thisList.append(listOfAgeCompartments[age].getAnemicFraction())
        aveAnemicFracChildren = sum(thisList)/len(thisList)
        thisList = []
        for age in range(0, len(listOfReproductiveAgeCompartments)):
            thisList.append(listOfReproductiveAgeCompartments[age].getAnemicFraction())
        aveAnemicFracWRA = sum(thisList)/len(thisList)
        
        # NOW ADD ALL CONSTRAINTS
        for intervention in newCoverages.keys():
            # set bed net constraints for all WRA IFAS interventions
            if ('IFAS' in intervention) and ('malaria' in intervention):
                if 'bed nets' in intervention:
                    if newCoverages[intervention] > (1. - bednetCoverage):
                        constrainedCoverages[intervention] = (1. - bednetCoverage)
                elif 'bed nets' not in intervention:
                    if newCoverages[intervention] > bednetCoverage:
                        constrainedCoverages[intervention] = bednetCoverage
                        
            # add constraint on PPCF + iron in malaria area to allow maximum coverage to equal bednet coverage - do this before sprinkles constraint!
            if 'Public provision of complementary foods with iron (malaria area)' in intervention:
                if newCoverages[intervention] > bednetCoverage:
                    constrainedCoverages[intervention] = bednetCoverage

            # constrain PPCF to target only those not covered by PPCF + iron
            if 'Public provision of complementary foods' == intervention:
                totalPPCFCoverage = self.fracExposedMalaria * newCoverages['Public provision of complementary foods with iron (malaria area)'] + \
                               (1.-self.fracExposedMalaria) * newCoverages['Public provision of complementary foods with iron']
                if newCoverages[intervention] > (1.-totalPPCFCoverage):
                    constrainedCoverages[intervention] = (1. - totalPPCFCoverage)

            # add constraints on sprinkles coverage                
            # prioritise PPCF+iron over sprinkles, taking into account extra pop which can be covered by sprinkles
            if 'Sprinkles' in intervention:
                if 'malaria' in intervention:
                    maxAllowedCov = (1. - newCoverages['Public provision of complementary foods with iron (malaria area)']) * (1. + percentExtraPopMalaria)
                    if newCoverages[intervention] > maxAllowedCov:                    
                        constrainedCoverages[intervention] = maxAllowedCov
                    if constrainedCoverages[intervention] > bednetCoverage:
                        constrainedCoverages[intervention] = bednetCoverage
                else:
                    maxAllowedCov = (1. - newCoverages['Public provision of complementary foods with iron']) * (1. + percentExtraPop)
                    if newCoverages[intervention] > maxAllowedCov:                        
                        constrainedCoverages[intervention] = maxAllowedCov
                # if anemia <20% set coverage to zero
                if aveAnemicFracChildren < 0.2:
                    constrainedCoverages[intervention] = 0.
                    
            # add constraints on vitamin A and zinc- neither can be given if sprinkles already given.  Constrain sprinkles first!
            s1 = 'Sprinkles'
            s2 = 'Sprinkles (malaria area)'
            totalNumSprinkles = constrainedCoverages[s1] * targetSprinkles + constrainedCoverages[s2] * targetSprinklesMalaria
            totalConstrainedSprinklesCov = totalNumSprinkles/(targetSprinkles + targetSprinklesMalaria)
            if newCoverages['Vitamin A supplementation'] > (1. - totalConstrainedSprinklesCov):
                constrainedCoverages['Vitamin A supplementation'] = (1. - totalConstrainedSprinklesCov)
            if newCoverages['Zinc supplementation'] > (1. - totalConstrainedSprinklesCov):
                constrainedCoverages['Zinc supplementation'] = (1. - totalConstrainedSprinklesCov)    
             
            # add IPTp constraint to PW MMS in malaria area
            if ('Multiple micronutrient' in intervention) and ('malaria area' in intervention):
                if newCoverages[intervention] > IPTpCoverage:
                    constrainedCoverages[intervention] = IPTpCoverage
            
            # add constraint on PW IFAS and MMS- prefer MMS as the most expensive
            if 'Iron and folic acid' in intervention:
                if 'malaria' in intervention:
                    if newCoverages[intervention] > 1. - constrainedCoverages['Multiple micronutrient supplementation (malaria area)']:
                        constrainedCoverages[intervention] = 1. - constrainedCoverages['Multiple micronutrient supplementation (malaria area)']
                    if constrainedCoverages[intervention] > IPTpCoverage:
                        constrainedCoverages[intervention] = IPTpCoverage
                else:
                    if newCoverages[intervention] > 1. - constrainedCoverages['Multiple micronutrient supplementation']:
                        constrainedCoverages[intervention] = 1. - constrainedCoverages['Multiple micronutrient supplementation']
                    
            # add constraint to WRA IFAS interventions, set to 0 coverage if anemia prevalance <20%
            if 'IFAS' in intervention:
                if aveAnemicFracWRA < 0.2:
                    constrainedCoverages[intervention] = 0.
                    
            # add food fortification constraints
            if ("IFA fortification" in intervention):
                # cannot give iron fortification to those already receiving IFA fortification
                maxAllowedCovIron = 1.-newCoverages[intervention]
                IFAend = intervention.replace('IFA ', '')
                ironIntName = 'Iron ' + IFAend
                ironCov = newCoverages.get(ironIntName)
                if ironCov is None: # TODO: HACKY WAY TO GET AROUND REMOVING IRON FORTIFICATION -- not long-term solution
                    pass
                else:
                    if ironCov > maxAllowedCovIron:
                        constrainedCoverages[ironIntName] = maxAllowedCovIron
                    # only cover those not growing own food
                    fracNotFarming = 1.- self.demographics['fraction of subsistence farming']
                    constrainedCoverages[intervention] = newCoverages[intervention] * fracNotFarming
                    constrainedCoverages[ironIntName] *= fracNotFarming
        return constrainedCoverages

    def addWastingInterventionConstraints(self, wastingUpdateDueToWastingIncidence):
        # cash transfers and PPCF only target the fraction poor
        constrainedWastingUpdate = {}
        for ageName in self.ages:
            constrainedWastingUpdate[ageName] = {}
            for wastingCat in self.wastedList:
                fracTargeted = self.fracPoor
                fracNotTargeted = 1.-fracTargeted
                oldProbThisCat = self.wastingDistribution[ageName][wastingCat]
                newProbThisCat = oldProbThisCat * wastingUpdateDueToWastingIncidence[wastingCat][ageName]
                newProbThisCat = fracTargeted * newProbThisCat + fracNotTargeted * oldProbThisCat
                # convert back into an update
                reduction  = (oldProbThisCat - newProbThisCat) / oldProbThisCat
                constrainedWastingUpdate[ageName][wastingCat] = 1.-reduction
        return constrainedWastingUpdate

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
            oldProbAnemia = self.anemiaDistribution[ageName]["anemic"]
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
        # wasting (SAM and MAM)
        wastingUpdate = {}
        for ageName in self.ages:
            wastingUpdate[ageName] = {}
            for wastingCat in self.wastedList:
                wastingUpdate[ageName][wastingCat] = 1.
                newProbWasting = 0.
                oldProbWasting = self.wastingDistribution[ageName][wastingCat]
                for breastfeedingCat in self.breastfeedingList:
                    pab = self.breastfeedingDistribution[ageName][breastfeedingCat]
                    t1 = beta[ageName][breastfeedingCat] * self.derived.fracWastedIfDiarrhea[wastingCat]["dia"][ageName]
                    t2 = (1. - beta[ageName][breastfeedingCat]) * \
                         self.derived.fracWastedIfDiarrhea[wastingCat]["nodia"][ageName]
                    newProbWasting += pab * (t1 + t2)
                reductionWasting = (oldProbWasting - newProbWasting) / oldProbWasting
                wastingUpdate[ageName][wastingCat] *= 1. - reductionWasting
        return stuntingUpdate, anemiaUpdate, wastingUpdate

    def getWastingUpdateDueToWastingIncidence(self, incidenceBefore, incidenceAfter):
        wastingUpdate = {}
        for age in self.ages:
            reduction = (incidenceBefore[age] - incidenceAfter[age])/incidenceAfter[age]
            wastingUpdate[age] = 1. - reduction
        return wastingUpdate

    def getStuntingUpdateComplementaryFeeding(self, newCoverage):
        stuntingUpdate = {}
        for ageName in self.ages:
            stuntingUpdate[ageName] = 1.
        Ce = 0
        for program in self.IYCFprograms:
            Ce += newCoverage[program]
        if Ce > 0.95: # TODO: don't actually want this restriction, b/c we are going to be targetting different target populations
            Ce = 0.95
        key1 = 'Public provision of complementary foods'
        key2 = 'Public provision of complementary foods with iron'
        # collect data
        X1 = self.demographics['fraction food insecure (default poor)']
        X2 = 1.0 
        X3 = 0.0 
        Cse = newCoverage[key1] + newCoverage[key2]
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
