"""
guidemo1.py -- script for running functionality for the Nutrition GUI demo
    
Last update: 11/13/17 (gchadder3)
"""

#
# Imports
#

import costcov
import optimisation2
from copy import deepcopy as dcp
import uuid

#
# Classes
#

# Provisional Project class.
class Project(object):
    def  __init__(self, spreadsheetPath, theUID=None):        
        # If a UUID was passed in...
        if theUID is not None:
            # Make sure the argument is a valid UUID, converting a hex text to a
            # UUID object, if needed.        
            validUID = getValidUUID(theUID) 
            
            # If a validUID was found, use it.
            if validUID is not None:
                self.uid = validUID
            # Otherwise, generate a new random UUID using uuid4().
            else:
                self.uid = uuid.uuid4()
        # Otherwise, generate a new random UUID using uuid4().
        else:
            self.uid = uuid.uuid4()
     
        # Set the spreadsheetPath.
        self.spreadsheetPath = spreadsheetPath
    
        # Set up Optimisation object to work with and save this.
        numModelSteps = 14
        optimise = 'dummy'
        resultsFileStem = 'dummy'
        costCurveType = 'dummy'
        self.theOptimisation = optimisation2.Optimisation(spreadsheetPath, 
            numModelSteps, optimise, resultsFileStem, costCurveType)    

#
# Functions
#

def getValidUUID(uidParam):
    # Get the type of the parameter passed in.
    paramType = type(uidParam)
    
    # Return what was passed in if it is already the right type.
    if paramType == uuid.UUID:
        return uidParam
    
    # Try to do the conversion and if it fails, set the conversion to None.
    try:
        convertParam = uuid.UUID(uidParam)
    except:
        convertParam = None
    
    # Return the converted value.
    return convertParam 

def pctChange(startVal, endVal):
    if startVal == 0.0:
        if endVal == 0.0:
            return 0.0
        else:
            return 999999.0
    else:
        return (endVal - startVal) * 100.0 / startVal
    
def getInterventions(theProject):
    # Set up Optimisation object to work with.
    theOpt = theProject.theOptimisation 
    
    # Load the spreadsheet data in the Optimisation object and make a link to 
    # this.
    theOpt.loadData()
    spreadsheetData = theOpt.spreadsheetData
    
    # Create a Costcov object to use for calculating spendings from coverage
    # percentages.
    costCov = costcov.Costcov()

    # Get the cost coverage info from the Optimisation object.
    costCoverageInfo = theOpt.getCostCoverageInfo()
    
    # Get the initial target population sizes for each intervention from the 
    # Optimisation object.
    targetPopSize = theOpt.getInitialTargetPopSize()
    
    # Get the intervention labels and default coverages (in spreadsheet order).
    intervLabels = []
    intervCovDefs = []
    intervDefSpending = []
    intervMaxCovs = []
    # Loop over all of the interventions in the spreadsheet...
    for interv in spreadsheetData.interventionList:
        intervLabels.append(interv)
        intervCovDefs.append(spreadsheetData.coverage[interv])
        intervMaxCovs.append(costCoverageInfo[interv]['saturation'])
        covNumber = spreadsheetData.coverage[interv] * targetPopSize[interv]
        spending = costCov.getSpending(covNumber, costCoverageInfo[interv], 
            targetPopSize[interv])
        intervDefSpending.append(spending)

    # Pass the results back.
    return [intervLabels, intervCovDefs, intervDefSpending, intervMaxCovs]

def runModel(theProject, interventionCoverages, yearsToRun):
    # Set up Optimisation object to work with.    
    theOpt = theProject.theOptimisation
    
    # Load the spreadsheet data in the Optimisation object and make a link to 
    # this.
    theOpt.loadData()
    spreadsheetData = theOpt.spreadsheetData
    
    # Create a Costcov object to use for calculating spendings from coverage
    # percentages.    
    costCov = costcov.Costcov()

    # Get the cost coverage info from the Optimisation object.
    costCoverageInfo = theOpt.getCostCoverageInfo()
    
    # Get the initial target population sizes for each intervention from the 
    # Optimisation object.
    targetPopSize = theOpt.getInitialTargetPopSize()
    
    # Set the model number of years.
    theOpt.numModelSteps = yearsToRun
    
    SCintervSpending = []
    SCallocationDict = {}
    for ind, interv in enumerate(spreadsheetData.interventionList):
        covNumber = interventionCoverages[ind] * targetPopSize[interv]
        spending = costCov.getSpending(covNumber, costCoverageInfo[interv], 
            targetPopSize[interv])
        SCallocationDict[interv] = spending
        SCintervSpending.append(spending)
        
    # Run the baseline model.
    BLallocationDict = theOpt.getInitialAllocationDictionary()  # reads from the spreadsheet
    BLrunResults = theOpt.oneModelRunWithOutput(BLallocationDict) # reads from the spreadsheet
    
    # Run the scenario model.
    SCrunResults = theOpt.oneModelRunWithOutput(SCallocationDict) # reads from the spreadsheet
    
    # Create lists to be passed back to the client.
    outcomeLabels = []
    BLoutcomes = []
    SCoutcomes = []
    pctChanges = []
    
    outcomeLabels.append('Thriving children')
    BLoutcomes.append(BLrunResults[-1].getOutcome('thrive'))
    SCoutcomes.append(SCrunResults[-1].getOutcome('thrive'))
    pctChanges.append(pctChange(BLoutcomes[-1], SCoutcomes[-1]))
    
    outcomeLabels.append('Child deaths')
    BLoutcomes.append(BLrunResults[-1].getOutcome('deaths children'))
    SCoutcomes.append(SCrunResults[-1].getOutcome('deaths children'))
    pctChanges.append(pctChange(BLoutcomes[-1], SCoutcomes[-1]))
    
    outcomeLabels.append('Maternal deaths')
    BLoutcomes.append(BLrunResults[-1].getOutcome('deaths PW'))
    SCoutcomes.append(SCrunResults[-1].getOutcome('deaths PW'))
    pctChanges.append(pctChange(BLoutcomes[-1], SCoutcomes[-1]))
    
    outcomeLabels.append('Anemia prevalence in pregnant women')
    BLoutcomes.append(BLrunResults[-1].getOutcome('anemia frac pregnant'))
    SCoutcomes.append(SCrunResults[-1].getOutcome('anemia frac pregnant'))
    pctChanges.append(pctChange(BLoutcomes[-1], SCoutcomes[-1]))
    
    outcomeLabels.append('Anemia prevalence in women of reproductive age')
    BLoutcomes.append(BLrunResults[-1].getOutcome('anemia frac WRA'))
    SCoutcomes.append(SCrunResults[-1].getOutcome('anemia frac WRA'))
    pctChanges.append(pctChange(BLoutcomes[-1], SCoutcomes[-1]))
    
    outcomeLabels.append('Anemia prevalence in children')
    BLoutcomes.append(BLrunResults[-1].getOutcome('anemia frac children'))
    SCoutcomes.append(SCrunResults[-1].getOutcome('anemia frac children'))
    pctChanges.append(pctChange(BLoutcomes[-1], SCoutcomes[-1]))
    
    outcomeLabels.append('Wasting prevalence (all types)')
    BLoutcomes.append(BLrunResults[-1].getOutcome('wasting_prev'))
    SCoutcomes.append(SCrunResults[-1].getOutcome('wasting_prev'))
    pctChanges.append(pctChange(BLoutcomes[-1], SCoutcomes[-1]))
    
    outcomeLabels.append('Wasting prevalence (moderate)')
    BLoutcomes.append(BLrunResults[-1].getOutcome('MAM_prev'))
    SCoutcomes.append(SCrunResults[-1].getOutcome('MAM_prev'))
    pctChanges.append(pctChange(BLoutcomes[-1], SCoutcomes[-1]))
    
    outcomeLabels.append('Wasting prevalence (severe)')
    BLoutcomes.append(BLrunResults[-1].getOutcome('SAM_prev'))
    SCoutcomes.append(SCrunResults[-1].getOutcome('SAM_prev'))
    pctChanges.append(pctChange(BLoutcomes[-1], SCoutcomes[-1]))
    
    outcomeLabels.append('Stunting prevalance')
    BLoutcomes.append(BLrunResults[-1].getOutcome('stunting prev'))
    SCoutcomes.append(SCrunResults[-1].getOutcome('stunting prev'))
    pctChanges.append(pctChange(BLoutcomes[-1], SCoutcomes[-1]))
    
    # Pass the results back.
    return [SCintervSpending, outcomeLabels, BLoutcomes, SCoutcomes, pctChanges]
    
#
# Script
#

if __name__ == '__main__':
    #
    # SERVER: Setup and initial GUI info
    #
    
    # Set up Optimisation object to work with.
    rootpath = './'
    #spreadsheet = rootpath + 'input_spreadsheets/Bangladesh/2017Oct/InputForCode_Bangladesh.xlsx'
    spreadsheet = rootpath + 'input_spreadsheets/Bangladesh/gchadder3Test/InputForCode_Bangladesh.xlsx'    
    theProj = Project(spreadsheet)  
    theOpt = theProj.theOptimisation
    
    # Load the spreadsheet data in the Optimisation object and make a link to 
    # this.
    theOpt.loadData()
    spreadsheetData = theOpt.spreadsheetData
    
    # Create a Costcov object to use for calculating spendings from coverage
    # percentages.    
    costCov = costcov.Costcov()

    # Get the cost coverage info from the Optimisation object.
    costCoverageInfo = theOpt.getCostCoverageInfo()
    
    # Get the initial target population sizes for each intervention from the 
    # Optimisation object.
    targetPopSize = theOpt.getInitialTargetPopSize()
    
    # Get the intervention labels and default coverages (in spreadsheet order).
    intervLabels = []
    intervCovDefs = []
    intervDefSpending = []
    intervMaxCovs = []
    # Loop over all of the interventions in the spreadsheet...
    for interv in spreadsheetData.interventionList:
        intervLabels.append(interv)
        intervCovDefs.append(spreadsheetData.coverage[interv])
        intervMaxCovs.append(costCoverageInfo[interv]['saturation'])
        covNumber = spreadsheetData.coverage[interv] * targetPopSize[interv]
        spending = costCov.getSpending(covNumber, costCoverageInfo[interv], 
            targetPopSize[interv])
        intervDefSpending.append(spending)
        
    # Stuff getting passed back to client:
    # intervLabels
    # intervCovDefs
    # intervDefSpending
    # intervMaxCovs
    
    #
    # CLIENT: First GUI display
    #
       
    # GUI Info for the users.
    print 'GUI info provided:'
    for ind, intervLabel in enumerate(intervLabels):
        print '%s:' % intervLabel
        print '  BL Coverage = %f, BL Spending = %f' % \
            (intervCovDefs[ind], intervDefSpending[ind])
    
    #
    # CLIENT: User action on GUI
    #
            
    # Set set GUI interventions for allocation.  Set just the 5 intervention to 1.0, 
    # and the rest to 0.0.
    SCintervCovs = dcp(intervCovDefs)
    SCintervCovs[0] = 0.0
    SCintervCovs[1] = 0.0
    SCintervCovs[2] = 0.0
    SCintervCovs[3] = 0.0
    SCintervCovs[4] = 0.0 # 0.75
    SCintervCovs[-1] = 0.0
    
    numYearsToRun = 14
    
    #
    # CLIENT: Validate user entries
    #
    
    for ind, intervLabel in enumerate(intervLabels):
        if SCintervCovs[ind] >= intervMaxCovs[ind]:
            print 'ERROR: %s coverage value needs to be smaller than saturation' % intervLabel
        elif SCintervCovs[ind] < 0.0:
            print 'ERROR: %s coverage value is set to a negative value' % intervLabel
    
    if numYearsToRun < 1:
        print 'ERROR: This needs to run at least 1 year.'
    elif numYearsToRun > 14:
        print 'ERROR: There is not enough data here to run for %d years.' % numYearsToRun
    #
    # SERVER: Response to user Simulate button press
    #
    
    # Set the model number of years.
    theOpt.numModelSteps = numYearsToRun
    
    SCintervSpending = []
    SCallocationDict = {}
    for ind, interv in enumerate(spreadsheetData.interventionList):
        covNumber = SCintervCovs[ind] * targetPopSize[interv]
        spending = costCov.getSpending(covNumber, costCoverageInfo[interv], 
            targetPopSize[interv])
        SCallocationDict[interv] = spending
        SCintervSpending.append(spending)
        
    # Run the baseline model.
    BLallocationDict = theOpt.getInitialAllocationDictionary()  # reads from the spreadsheet
    BLrunResults = theOpt.oneModelRunWithOutput(BLallocationDict) # reads from the spreadsheet
    
    # Run the scenario model.
    SCrunResults = theOpt.oneModelRunWithOutput(SCallocationDict) # reads from the spreadsheet
    
    # Create lists to be passed back to the client.
    outcomeLabels = []
    BLoutcomes = []
    SCoutcomes = []
    pctChanges = []
    
    outcomeLabels.append('Thriving children')
    BLoutcomes.append(BLrunResults[-1].getOutcome('thrive'))
    SCoutcomes.append(SCrunResults[-1].getOutcome('thrive'))
    pctChanges.append(pctChange(BLoutcomes[-1], SCoutcomes[-1]))
    
    outcomeLabels.append('Child deaths')
    BLoutcomes.append(BLrunResults[-1].getOutcome('deaths children'))
    SCoutcomes.append(SCrunResults[-1].getOutcome('deaths children'))
    pctChanges.append(pctChange(BLoutcomes[-1], SCoutcomes[-1]))
    
    outcomeLabels.append('Maternal deaths')
    BLoutcomes.append(BLrunResults[-1].getOutcome('deaths PW'))
    SCoutcomes.append(SCrunResults[-1].getOutcome('deaths PW'))
    pctChanges.append(pctChange(BLoutcomes[-1], SCoutcomes[-1]))
    
    outcomeLabels.append('Anemia prevalence in pregnant women')
    BLoutcomes.append(BLrunResults[-1].getOutcome('anemia frac pregnant'))
    SCoutcomes.append(SCrunResults[-1].getOutcome('anemia frac pregnant'))
    pctChanges.append(pctChange(BLoutcomes[-1], SCoutcomes[-1]))
    
    outcomeLabels.append('Anemia prevalence in women of reproductive age')
    BLoutcomes.append(BLrunResults[-1].getOutcome('anemia frac WRA'))
    SCoutcomes.append(SCrunResults[-1].getOutcome('anemia frac WRA'))
    pctChanges.append(pctChange(BLoutcomes[-1], SCoutcomes[-1]))
    
    outcomeLabels.append('Anemia prevalence in children')
    BLoutcomes.append(BLrunResults[-1].getOutcome('anemia frac children'))
    SCoutcomes.append(SCrunResults[-1].getOutcome('anemia frac children'))
    pctChanges.append(pctChange(BLoutcomes[-1], SCoutcomes[-1]))
    
    outcomeLabels.append('Wasting prevalence (all types)')
    BLoutcomes.append(BLrunResults[-1].getOutcome('wasting_prev'))
    SCoutcomes.append(SCrunResults[-1].getOutcome('wasting_prev'))
    pctChanges.append(pctChange(BLoutcomes[-1], SCoutcomes[-1]))
    
    outcomeLabels.append('Wasting prevalence (moderate)')
    BLoutcomes.append(BLrunResults[-1].getOutcome('MAM_prev'))
    SCoutcomes.append(SCrunResults[-1].getOutcome('MAM_prev'))
    pctChanges.append(pctChange(BLoutcomes[-1], SCoutcomes[-1]))
    
    outcomeLabels.append('Wasting prevalence (severe)')
    BLoutcomes.append(BLrunResults[-1].getOutcome('SAM_prev'))
    SCoutcomes.append(SCrunResults[-1].getOutcome('SAM_prev'))
    pctChanges.append(pctChange(BLoutcomes[-1], SCoutcomes[-1]))
    
    outcomeLabels.append('Stunting prevalance')
    BLoutcomes.append(BLrunResults[-1].getOutcome('stunting prev'))
    SCoutcomes.append(SCrunResults[-1].getOutcome('stunting prev'))
    pctChanges.append(pctChange(BLoutcomes[-1], SCoutcomes[-1]))
    
    # Stuff getting passed back to client:
    # SCintervSpending
    # outcomeLabels
    # BLoutcomes
    # SCoutcomes
    # pctChanges
    
    #
    # CLIENT: GUI display of BL and SC coverage and spending
    #
    
    # GUI Button pressed
    print
    print 'GUI Simulate Button Pressed'
    print
    print 'GUI info provided after button press:'
    for ind, intervLabel in enumerate(intervLabels):
        print '%s:' % intervLabel
        print '  BL Coverage = %f, BL Spending = %f, SC Coverage = %f, SC Spending = %f' % \
            (intervCovDefs[ind], intervDefSpending[ind], SCintervCovs[ind], \
             SCintervSpending[ind])
            
    #
    # CLIENT: GUI display of outcome for baseline and scenario
    #
    
    print
    print 'Model run results to show in GUI:'
    
    for ind, outcomeLabel in enumerate(outcomeLabels):
        print '%s:' % outcomeLabel
        print '  BL = %f, SC = %f, %% diff = %f' % \
            (BLoutcomes[ind], SCoutcomes[ind], pctChanges[ind])  