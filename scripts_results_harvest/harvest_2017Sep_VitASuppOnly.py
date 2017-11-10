import os, sys

rootpath = '..'
moduleDir = os.path.join(os.path.dirname(__file__), rootpath)
sys.path.append(moduleDir)
import optimisation

country = 'Tanzania'
date = '2017Sep'
spreadsheetDate = '2017Sep'

costCurveType = 'standard'
numModelSteps = 180

# NATIONAL
dataSpreadsheetName = rootpath+'/input_spreadsheets/'+country+'/'+spreadsheetDate+'/TanzaniaHatSheets'+'/InputForCode_'+country+'Hat_VitASuppOnly_IYCF.xlsx'
outcomeOfInterestList = ['thrive']
cascadeValues = [1.0]

for optimise in outcomeOfInterestList:
    resultsFileStem = rootpath + '/Results/' + date + '/' + optimise + '/national/' + country + 'Hat/' + 'VitASuppOnly_IYCF/'
    # both time series when optimising for thrive
    thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem, costCurveType)
    thisOptimisation.outputCurrentSpendingToCSV()
    thisOptimisation.outputTimeSeriesToCSV('thrive')
    thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise,
                                                 resultsFileStem, costCurveType)  # this repitition is necessary
    thisOptimisation.outputTimeSeriesToCSV('deaths')
    # both outcomes for thrive cascade
    thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise,
                                                 resultsFileStem, costCurveType)  # this one might not be
    for outcomeOfInterest in outcomeOfInterestList:
        thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem, costCurveType)
        thisOptimisation.outputCascadeAndOutcomeToCSV(cascadeValues, outcomeOfInterest)

    # GET COVERAGE INFO FOR THE CASCADE
    import pickle
    import data
    import costcov
    import csv

    costCov = costcov.Costcov()
    thisOptimisation = optimisation.Optimisation(dataSpreadsheetName, numModelSteps, optimise, resultsFileStem, costCurveType)
    spreadsheetData = data.readSpreadsheet(dataSpreadsheetName, thisOptimisation.helper.keyList)

    coverages = {}
    for value in cascadeValues:
        coverages[value] = []
        filename = '%s_cascade_%s_%s.pkl' % (resultsFileStem, optimise, value)
        infile = open(filename, 'rb')
        allocation = pickle.load(infile)
        infile.close()
        # run the model with this allocation
        costCoverageInfo = thisOptimisation.getCostCoverageInfo()
        modelList = thisOptimisation.oneModelRunWithOutput(allocation)
        costCurves = optimisation.generateCostCurves(spreadsheetData, modelList[11], thisOptimisation.helper.keyList, thisOptimisation.dataSpreadsheetName,
                                       costCoverageInfo, thisOptimisation.costCurveType)
        for intervention in spreadsheetData.interventionList:
            costCurveThisIntervention = costCurves[intervention]
            coverages[value].append(costCurveThisIntervention(allocation[intervention]))
        # get cost coverage and target pop to translate cost to coverage
        # costCoverageInfo = thisOptimisation.getCostCoverageInfo()
        # # target pop size when interventions are added comes after 12 timesteps
        # targetPopSize = optimisation.getTargetPopSizeFromModelInstance(dataSpreadsheetName, thisOptimisation.helper.keyList,
        #                                                                 modelList[11])
        #
        # # get coverages
        # for i in range(0, len(spreadsheetData.interventionList)):
        #     intervention = spreadsheetData.interventionList[i]
        #     coverages[value].append(
        #         costCov.function(allocation[intervention], costCoverageInfo[intervention], targetPopSize[intervention]) /
        #         targetPopSize[intervention])
    # write to csv
    outfile = 'nationalCascadeCoverages_.csv'
    x = ['intervention'] + spreadsheetData.interventionList
    with open(outfile, "wb") as f:
        writer = csv.writer(f)
        writer.writerow(x)
        for value in cascadeValues:
            y = [value] + coverages[value]
            writer.writerow(y)


