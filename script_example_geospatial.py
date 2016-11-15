# -*- coding: utf-8 -*-
"""
Created on Mon Jul 11 17:54:47 2016

@author: ruth

This is an example script of how to use the geospatial class to generate and harvest results.
Use as a reference, do not edit.
"""
# all the code is contained in the optimisation module (optimisation.py)
import optimisation

# information about the analysis
country = 'Bangladesh'
date = '2016Oct'

# how long to run the analysis for (1 step = 1 month)
numModelSteps = 180

# the multiples of the current budget to run the budget cascades for
cascadeValues = [1.0, 1.1, 1.25, 1.5, 1.7, 2.0, 'extreme']  

# the objective of the optimisation
optimise = 'deaths'

# the list of names of each region in the geospatial analysis 
regionNameList = ['Barisal', 'Chittagong', 'Dhaka', 'Khulna', 'Rajshahi', 'Rangpur', 'Sylhet']

# create a list of the spreadsheet names for each region
spreadsheetFileStem = 'input_spreadsheets/' + country + '/' + date + '/subregionSpreadsheets/'
spreadsheetList = []
for regionName in regionNameList:
    spreadsheet = spreadsheetFileStem + regionName + '.xlsx'
    spreadsheetList.append(spreadsheet)

# this is the location of the optimisation results per region (to be generated or harvested)
resultsFileStem = 'Results/'+date+'/'+optimise+'/geospatial/'

# this specifies if the current coverage of programs is fixed.  If True, only money above 100% of current spending will be optimised
haveFixedProgCosts = True

# check athena and then specify how many cores you are going to use (this translates into the number of jobs as we assume 1 core per job)
# this is only needed if you plan to run in parallel
nCores = 49

#  --------------------     STEP 1:  FIRST GENERATE THE BUDGET CASCADES FOR EACH REGION   --------------------

# how many MC samples (chains of the optimisation) to run
MCSampleSize = 25

# instantiate a geospatial object
geospatialOptimisation = optimisation.GeospatialOptimisation(spreadsheetList, regionNameList, numModelSteps, cascadeValues, optimise, resultsFileStem)

# use it to genarate geospatial cascades if they're not already there (these will be stored in the resultsFileStem location)
geospatialOptimisation.generateParallelResultsForGeospatialCascades(nCores, MCSampleSize, haveFixedProgCosts)


#  --------------------    STEP 2:  NOW DO THE GEOSPATIAL ANALYSIS  --------------------

# this is how much extra money you want to add to the current budget to be optimised
extraMoney = 10000000

# this is the file prefix of the results of the geospatial analysis
GAFile = 'GA_fixedProg_extra_'+str(extraMoney)

# this is the number of cores if running in parallel.  
# It refers to the individual regional optimisation of their optimal spending, (as determined by the geospatial optimisation), and so should equal the number of regions
nCores = 7

# this is the MC sample size for the geospatial optimisation (that which optimises across regions using the budget-outcome curves)
geoMCSampleSize = 25

# this is the MC sample size for the post-GA regional optimisations across interventions
rerunMCSampleSize = 25

# perform the geospatial optimisation
geospatialOptimisation.performParallelGeospatialOptimisationExtraMoney(geoMCSampleSize, rerunMCSampleSize, GAFile, nCores, extraMoney, haveFixedProgCosts)



#  --------------------  STEP 3:  NOW HARVEST THE RESULTS   --------------------

# output the current regional spending to CSV
geospatialOptimisation.outputRegionalCurrentSpendingToCSV()

# output the recommended regional spending from the geospatial analysis (GA)
geospatialOptimisation.outputRegionalPostGAOptimisedSpendingToCSV(GAFile)

# output trade off curves to CSV
geospatialOptimisation.outputTradeOffCurves()

# output budget cascade and outcome cascade to CSV for each region (two CSVs per region)
geospatialOptimisation.outputRegionalCascadesAndOutcomeToCSV('stunting')

# output the time series of each region to CSV for a given outcome of interest (doesn't have to be ther same as 'optimise')
outcomeOfInterest = 'stunting'
geospatialOptimisation.outputRegionalTimeSeriesToCSV(outcomeOfInterest)

# plot the time series (baseline and post-GA) for each region.  Outcome here is 'optimise'.
geospatialOptimisation.plotTimeSeriesPostGAReallocationByRegion(GAFile)

# output the time series (baseline and post-GA) for each region to CSV.  Outcome here is 'optimise'.
geospatialOptimisation.outputToCSVTimeSeriesPostGAReallocationByRegion(GAFile)









