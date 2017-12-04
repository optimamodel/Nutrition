#-*- coding: utf-8 -*-
"""
Created on Mon Feb 29 11:35:02 2016

@author: madhura
"""
from copy import deepcopy as dcp

class Helper:
    def __init__(self):
        self.keyList = {}
        self.keyList['timestep'] = 1./12. 
        self.keyList['ages'] = ["<1 month", "1-5 months", "6-11 months", "12-23 months", "24-59 months"]
        self.keyList['birthOutcomes'] = ["Pre-term SGA", "Pre-term AGA", "Term SGA", "Term AGA"]
        self.keyList['wastingList'] = ["normal", "mild", "MAM", "SAM"]
        self.keyList['wastedList'] = ["SAM", "MAM"]
        self.keyList['nonWastedList'] = ["mild", "normal"]
        self.keyList['stuntingList'] = ["normal", "mild", "moderate", "high"]
        self.keyList['breastfeedingList'] = ["exclusive", "predominant", "partial", "none"]
        self.keyList['anemiaList'] = ['anemic', 'not anemic']
        self.keyList['ageGroupSpans'] = [1., 5., 6., 12., 36.] # number of months in each age group
        self.keyList['agingRates'] = [1./1., 1./5., 1./6., 1./12., 1./36.]
        self.keyList['reproductiveAges'] = ['WRA: 15-19 years', 'WRA: 20-29 years', 'WRA: 30-39 years', 'WRA: 40-49 years']
        self.keyList['reproductiveAgingRates'] = [1./5., 1./10., 1./10., 1./10.] # this is in years
        self.keyList['stuntedList'] = ["moderate", "high"]
        self.keyList['lifeExpectancy'] = 83.5
        self.keyList['pregnantWomenAges'] = ["PW: 15-19 years", "PW: 20-29 years", "PW: 30-39 years", "PW: 40-49 years"]
        self.keyList['pregnantWomenAgeSpans'] = [5./35., 10./35., 10./35., 10./35.]
        self.keyList['allPops'] = dcp(self.keyList['ages'])
        self.keyList['allPops'] += self.keyList['pregnantWomenAges'] + self.keyList['reproductiveAges']

    # Going from binary stunting/wasting to four fractions
    # Yes refers to more than 2 standard deviations below the global mean/median
    # in our notes, fractionYes = alpha
    def restratify(self, fractionYes):
        from scipy.stats import norm
        invCDFalpha = norm.ppf(fractionYes)
        fractionHigh     = norm.cdf(invCDFalpha - 1.)
        fractionModerate = fractionYes - norm.cdf(invCDFalpha - 1.)
        fractionMild     = norm.cdf(invCDFalpha + 1.) - fractionYes
        fractionNormal   = 1. - norm.cdf(invCDFalpha + 1.)
        restratification = {}
        restratification["normal"] = fractionNormal
        restratification["mild"] = fractionMild
        restratification["moderate"] = fractionModerate
        restratification["high"] = fractionHigh
        return restratification

    def sumStuntedComponents(self, thingToSum):
        sumStuntedComponents = 0
        for stuntingCat in self.keyList['stuntedList']:
            sumStuntedComponents += thingToSum[stuntingCat]  
        return sumStuntedComponents    

    def makeAgePopSizes(self, inputData):
        numAgeGroups = len(self.keyList['ages'])        
        agePopSizes = [0.]*numAgeGroups
        numGroupsInYear = 3
        numMonthsInYear = sum(self.keyList['ageGroupSpans'][:numGroupsInYear])
        numPopEachMonth = inputData.demographics['number of live births'] / numMonthsInYear
        for i in range(numGroupsInYear):
            agePopSizes[i] = numPopEachMonth * self.keyList['ageGroupSpans'][i]
        numMonthsOlder = sum(self.keyList['ageGroupSpans']) - numMonthsInYear
        numPopOlder = inputData.demographics['population U5'] - inputData.demographics['number of live births']
        numPopEachMonthOlder = numPopOlder / numMonthsOlder
        for i in range(numGroupsInYear,numAgeGroups):
            agePopSizes[i] = numPopEachMonthOlder * self.keyList['ageGroupSpans'][i]
        return agePopSizes

    def makeBoxes(self, thisAgePopSize, ageName, inputData):
        import populations 
        wastingList = self.keyList['wastingList']
        stuntingList = self.keyList['stuntingList']
        breastfeedingList = self.keyList['breastfeedingList']
        allBoxes = {}
        for stuntingCat in stuntingList:
            allBoxes[stuntingCat] = {} 
            for wastingCat in wastingList:
                allBoxes[stuntingCat][wastingCat] = {}
                for breastfeedingCat in breastfeedingList:
                    allBoxes[stuntingCat][wastingCat][breastfeedingCat] = {}
                    for anemiaStatus in self.keyList['anemiaList']:
                        thisPopSize = thisAgePopSize * inputData.stuntingDistribution[ageName][stuntingCat] * inputData.wastingDistribution[ageName][wastingCat] * \
                                      inputData.breastfeedingDistribution[ageName][breastfeedingCat] * inputData.anemiaDistribution[ageName][anemiaStatus] # Assuming independent
                        allBoxes[stuntingCat][wastingCat][breastfeedingCat][anemiaStatus] =  populations.Box(thisPopSize)
        return allBoxes

        
    def makeReproductiveAgeBoxes(self, thisAgePopSize, ageName, inputData):
        import populations
        boxes = {}
        for status in self.keyList['anemiaList']:
             thisPopSize = thisAgePopSize * inputData.anemiaDistribution[ageName][status]
             boxes[status] = populations.Box(thisPopSize)   
        return boxes       

    def makePregnantWomenAgeBoxes(self, thisAgePopSize, ageName, inputData):
        import populations
        boxes = {}
        for anemiaStatus in self.keyList['anemiaList']:
            boxes[anemiaStatus] = {}
            thisPopSize = thisAgePopSize * inputData.anemiaDistribution[ageName][anemiaStatus]
            boxes[anemiaStatus] = populations.Box(thisPopSize)
        return boxes

    def makeAgeCompartments(self, inputData):
        import populations 
        agePopSizes = self.makeAgePopSizes(inputData)
        ages = self.keyList['ages']
        numAgeGroups = len(ages)
        listOfAgeCompartments = []
        for iAge in range(numAgeGroups): # Loop over all age-groups
            ageName  = ages[iAge]
            agingRate = self.keyList['agingRates'][iAge]
            agePopSize = agePopSizes[iAge]
            thisAgeBoxes = self.makeBoxes(agePopSize, ageName, inputData)
            compartment = populations.AgeCompartment(ageName, thisAgeBoxes, agingRate, self.keyList)
            listOfAgeCompartments.append(compartment)
        return listOfAgeCompartments     
        
        
        
    def makeWRAAgePopSizes(self, inputData):
        popPW = self.makePregnantWomenAgePopSizes(inputData)        
        popWRA = dcp(inputData.demographics['population reproductive age'])
        ages = self.keyList['reproductiveAges']
        numAgeGroups = len(ages)
        agePopSizes = [0.]*numAgeGroups
        for iAge in range(numAgeGroups):
            ageName  = ages[iAge]
            agePopSizes[iAge] = popWRA[ageName] - popPW[iAge] # population WRA not pregnant 
        return agePopSizes
   
    def makeReproductiveAgeCompartments(self, inputData):
        import populations 
        agePopSizes = self.makeWRAAgePopSizes(inputData)
        ages = self.keyList['reproductiveAges']
        numAgeGroups = len(ages)
        listOfReproductiveAgeCompartments = []
        for iAge in range(numAgeGroups):
            ageName  = ages[iAge]
            agingRate = self.keyList['reproductiveAgingRates'][iAge] # TODO: can probably remove this
            thisAgeBoxes = self.makeReproductiveAgeBoxes(agePopSizes[iAge], ageName, inputData)
            compartment = populations.ReproductiveAgeCompartment(ageName, thisAgeBoxes, agingRate, self.keyList)
            listOfReproductiveAgeCompartments.append(compartment)
        return listOfReproductiveAgeCompartments
 
    def makePregnantWomenAgePopSizes(self, inputData):
        popPW = dcp(inputData.demographics['number of pregnant women'])
        PWageDistribution = dcp(inputData.PWageDistribution)
        ages = self.keyList['pregnantWomenAges']
        numAgeGroups = len(ages)
        agePopSizes = [0.]*numAgeGroups
        for iAge in range(numAgeGroups):
            ageName = ages[iAge]
            agePopSizes[iAge] = popPW * PWageDistribution[ageName]
        return agePopSizes    
    
    def makePregnantWomenAgeCompartments(self, inputData):
        import populations
        agePopSizes = self.makePregnantWomenAgePopSizes(inputData)
        popPW = dcp(inputData.demographics['number of pregnant women'])
        ages = self.keyList['pregnantWomenAges']
        numAgeGroups = len(ages)
        listOfPregnantWomenAgeCompartments = []
        annualBirths = dcp(inputData.demographics['number of live births'])
        birthRate = annualBirths / popPW
        for iAge in range(numAgeGroups):
            ageName = ages[iAge]
            agingRate = self.keyList['pregnantWomenAgeSpans'][iAge]
            thisAgeBoxes = self.makePregnantWomenAgeBoxes(agePopSizes[iAge], ageName, inputData)
            compartment = populations.PregnantWomenAgeCompartment(ageName, birthRate, thisAgeBoxes, agingRate, self.keyList)
            listOfPregnantWomenAgeCompartments.append(compartment)
        return listOfPregnantWomenAgeCompartments
        
        
        
    def setupModelDerivedParameters(self, inputData):
        import model 
        import derived 
        import parameters        
        # gaussianise stunting in *data*
        ages = self.keyList['ages']
        for iAge in range(len(ages)):
            ageName = ages[iAge]
            probStunting = self.sumStuntedComponents(inputData.stuntingDistribution[ageName])
            inputData.stuntingDistribution[ageName] = self.restratify(probStunting)
        listOfAgeCompartments = self.makeAgeCompartments(inputData)
        listOfPregnantWomenAgeCompartments = self.makePregnantWomenAgeCompartments(inputData)
        listOfReproductiveAgeCompartments = self.makeReproductiveAgeCompartments(inputData)
        model = model.Model(listOfPregnantWomenAgeCompartments, listOfAgeCompartments, listOfReproductiveAgeCompartments, self.keyList)
        derived = derived.Derived(inputData, model, self.keyList)
        model.setDerived(derived)
        parameters = parameters.Params(inputData, derived, self.keyList)
        model.setParams(parameters)
        model.updateMortalityRate()
        return model, derived, parameters
                
                
    
    def setupModelSpecificPopsizes(self, inputData, agePopSizes):
        import model 
        import derived 
        import parameters        
        # gaussianise stunting in *data*
        ages = self.keyList['ages']
        for iAge in range(len(ages)):
            ageName = ages[iAge]
            probStunting = self.sumStuntedComponents(inputData.stuntingDistribution[ageName])
            inputData.stuntingDistribution[ageName] = self.restratify(probStunting)
        listOfAgeCompartments = self.makeAgeCompartments(agePopSizes, inputData)
        listOfPregnantWomenAgeCompartments = self.makePregnantWomenAgeCompartments(inputData)
        model = model.Model(listOfPregnantWomenAgeCompartments, listOfAgeCompartments, self.keyList)
        derived = derived.Derived(inputData, model, self.keyList)
        model.setDerived(derived)
        parameters = parameters.Params(inputData, derived, self.keyList)
        model.setParams(parameters)
        model.updateMortalityRate()
        return model, derived, parameters

    def getPopSizeOfAgeGroups(self, myAgeGroups, allAgeGroups, compartments):
        groups = set(myAgeGroups)
        idxs = [(i,item) for i, item in enumerate(allAgeGroups) if item in groups]
        popSizes = {item: compartments[i].getTotalPopulation() for i, item in idxs}
        return popSizes

    def setIYCFTargetPopSize(self, data, model, fromModel=True):
        targetPop = data.IYCFtargetPop
        allPopSizes = {}
        PWages = self.keyList['pregnantWomenAges']
        childAges = self.keyList['ages']
        if fromModel: # get pop sizes from model instance
            PWpopSize = self.getPopSizeOfAgeGroups(PWages, PWages, model.listOfPregnantWomenAgeCompartments)
            allPopSizes.update(PWpopSize)
            # excldude 24-59 months
            childPopSize = self.getPopSizeOfAgeGroups(childAges, childAges, model.listOfAgeCompartments)
            allPopSizes.update(childPopSize)
        else:
            # initial pop sizes
            PWpopSize = self.makePregnantWomenAgePopSizes(data)
            childPopSize = self.makeAgePopSizes(data)
            allPopSizes = {age: popSize for age in childAges+PWages for popSize in childPopSize+PWpopSize}
        # equation: maxCovIYCF = sum(popSize * fracExposed) / sum(popSize)
        maxCov = {}
        for name, package in targetPop.iteritems():
            maxCov[name] = 0.
            for pop, modeFrac in package.iteritems():
                for mode, frac in modeFrac.iteritems():
                    maxCov[name] += frac * allPopSizes[pop]
        return maxCov

        
    def setIFASTargetPopWRA(self, spreadsheetData, model, fromModel):
        attendance = spreadsheetData.demographics['school attendance WRA 15-19']
        fracPoor = spreadsheetData.demographics['fraction food insecure (default poor)']
        fracNotPoor = 1.-fracPoor
        fracMalaria = spreadsheetData.demographics['fraction at risk of malaria']
        fracNotMalaria = 1. - fracMalaria
        # get correct population sizes
        if fromModel:
            # if getting target popsize from model instance
            pop15to19 = model.listOfReproductiveAgeCompartments[0].getTotalPopulation()        
            pop20to29 = model.listOfReproductiveAgeCompartments[1].getTotalPopulation()
            pop30to39 = model.listOfReproductiveAgeCompartments[2].getTotalPopulation()
            pop40to49 = model.listOfReproductiveAgeCompartments[3].getTotalPopulation()
            bednetCoverage = model.params.coverage['Long-lasting insecticide-treated bednets']
        else:    
            # if getting initial target pop size
            agePopSizes = self.makeWRAAgePopSizes(spreadsheetData)
            pop15to19 = agePopSizes[0]
            pop20to29 = agePopSizes[1]
            pop30to39 = agePopSizes[2]
            pop40to49 = agePopSizes[3]       
            bednetCoverage = spreadsheetData.coverage['Long-lasting insecticide-treated bednets']
        
        IFASinterventions = [intervention for intervention in spreadsheetData.interventionCompleteList if "IFAS" in intervention]
        targetPopulation= {}
        for intervention in IFASinterventions:
            # get the targetted age groups total number of people
            if "school" in intervention:
                pop = pop15to19 * attendance
            else:
                pop = pop20to29 + pop30to39 + pop40to49 + pop15to19*(1. - attendance)
            # get fraction of poor status: frac1
            if "not poor" in intervention:
                frac1 = fracNotPoor
            else:
                frac1 = fracPoor
            # get fraction targetted by delivery method: frac2
            if "community" in intervention and "not poor" in intervention:
                frac2 = 0.49
            elif "community" in intervention:
                frac2 = 0.7
            elif "hospital" in intervention and "not poor" in intervention:
                frac2 = 0.21
            elif "hospital" in intervention:    
                frac2 = 0.3
            elif "retailer" in intervention and "not poor" in intervention:
                frac2 = 0.3
            else:
                frac2 = 1.0
            # get fraction for malaria or no malaria: frac3
            if "malaria area" in intervention:
                frac3 = fracMalaria
            else:
                frac3 = fracNotMalaria   
            # get fractional reduction for bednet coverage: frac4
            if "malaria area" in intervention and " with bed nets" in intervention:
                frac4 = 1. # used in optimisation so target pop size can be everyone, optimisation will learn not to give more than 1-bednetCoverage
            elif "malaria area" in intervention:
                frac4 = bednetCoverage
            else:
                frac4 = 1.0
            # set target popluation for this intervention
            targetPopulation[intervention] = pop * frac1 * frac2 * frac3 * frac4
        return targetPopulation        
                
                
    def setIFASFractionTargetted(self, attendance, fracPoor, fracMalaria, interventionCompleteList, bednetCoverage):
        fracNotPoor = 1.-fracPoor
        fracNotMalaria = 1. - fracMalaria
        IFASinterventions = [intervention for intervention in interventionCompleteList if "IFAS" in intervention]
        fractionTargeted = {}
        for pop in self.keyList['reproductiveAges']:
            fractionTargeted[pop] = {}
            for intervention in IFASinterventions:
                # get fraction of poor status: frac1
                if "not poor" in intervention:
                    frac1 = fracNotPoor
                else:
                    frac1 = fracPoor
                # get fraction targetted by delivery method: frac2
                if "community" in intervention and "not poor" in intervention:
                    frac2 = 0.49
                elif "community" in intervention:
                    frac2 = 0.7
                elif "hospital" in intervention and "not poor" in intervention:
                    frac2 = 0.21
                elif "hospital" in intervention:    
                    frac2 = 0.3
                elif "retailer" and "not poor" in intervention:
                    frac2 = 0.3
                else:
                    frac2 = 1.0
                # get fraction for malaria or no malaria: frac3
                if "malaria area" in intervention:
                    frac3 = fracMalaria
                else:
                    frac3 = fracNotMalaria   
                # get fractional reduction for bednet coverage: frac4
                if "malaria area" and " with bed nets" in intervention:
                    frac4 = 1.- bednetCoverage # this has to do with probabilities so needs to be 1-bednetCoverage
                elif "malaria area" in intervention:
                    frac4 = bednetCoverage
                else:
                    frac4 = 1.0
                # get fraction of age group targetted: frac5   
                if "school" in intervention and "15-19" in pop:
                    frac5 = attendance
                elif "community" in intervention and "15-19" in pop:
                    frac5 = (1.-attendance)
                elif "community" in intervention and "15-19" not in pop:
                    frac5 = 1.
                elif "hospital" in intervention and "15-19" in pop:
                    frac5 = (1.-attendance)
                elif "hospital" in intervention and "15-19" not in pop:
                    frac5 = 1.
                elif "retailer" in intervention and "15-19" not in pop:
                    frac5 = 1.
                else:
                    frac5 = 0.
                # set fraction targetted for this pop and intervention
                fractionTargeted[pop][intervention] = frac1 * frac2 * frac3 * frac4 * frac5
        return fractionTargeted            