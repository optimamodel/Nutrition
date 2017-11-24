"""
guidemo1.py -- script for running functionality for the Nutrition GUI demo
    
Last update: 11/23/17 (gchadder3)
"""

#
# Imports
#

import os
import uuid
from copy import deepcopy as dcp
import datetime
import dateutil
import dateutil.tz

# Import cPickle if it is available in your Python setup because it is a 
# faster method.  If it's not available, import the regular pickle library.
try: 
    import cPickle as pickle
except: 
    import pickle
    
from gzip import GzipFile
from cStringIO import StringIO
from contextlib import closing

import costcov
import optimisation2
    
#
# Classes
#

# Provisional Project class.
class Project(object):
    """
    A Nutrition Project.
    
    Methods:
        __init__(name: str, theUID: UUID [None], spreadsheetPath: str [None]):
            void -- constructor 
        updateName(newName: str): void -- change the project name to newName
        updateSpreadsheet(spreadsheetPath: str): void -- change the 
            spreadsheet the project is using
        saveToPrjFile(dirPath: str, saveResults: bool [False]) -- save the 
            project to a .prj file and return the full path
            
    Attributes:
        uid (UUID) -- the UID of the Project
        name (str) -- the Project's name
        spreadsheetPath (str) -- the full path name for the Excel spreadsheet
        theOptimisation (Optimisation2) -- the Optimisation object used for 
            simulations
        createdTime (datetime.datetime) -- the time that the Project was 
            created
        updatedTime (datetime.datetime) -- the time that the Project was last 
            updated
        dataUploadTime (datetime.datetime) -- the time that the Project's 
            spreadsheet was last updated
        
    Usage:
        >>> theProj = Project('myproject', uuid.UUID('12345678123456781234567812345678'))                      
    """ 
    
    def  __init__(self, name, theUID=None, spreadsheetPath=None):        
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
            
        # Set the project name.
        self.name = name
        
        # Set the spreadsheetPath.
        self.spreadsheetPath = spreadsheetPath
        
        # Start the optimisation object as being None.
        self.theOptimisation = None
                
        # Set the creation time for now.
        self.createdTime = today()
        
        # Set the updating time to None.
        self.updatedTime = None
        
        # Set the spreadsheet upload time to None.
        self.dataUploadTime = None
        
        # If we have passed in a spreadsheet path...
        if self.spreadsheetPath is not None:
            # Set up Optimisation object to work with and save this.
            numModelSteps = 14
            optimise = 'dummy'
            resultsFileStem = 'dummy'
            costCurveType = 'dummy'
            self.theOptimisation = optimisation2.Optimisation(spreadsheetPath, 
                numModelSteps, optimise, resultsFileStem, costCurveType)
            
            # Set the data spreadsheet upload time for now.
            self.dataUploadTime = today()
            
    def updateName(self, newName):
        # Set the project name.
        self.name = newName
        
        # Set the updating time to now.
        self.updatedTime = today()
        
    def updateSpreadsheet(self, spreadsheetPath):
        # Set the spreadsheetPath from what's passed in.
        self.spreadsheetPath = spreadsheetPath
        
        # Set up Optimisation object to work with and save this.
        numModelSteps = 14
        optimise = 'dummy'
        resultsFileStem = 'dummy'
        costCurveType = 'dummy'
        self.theOptimisation = optimisation2.Optimisation(spreadsheetPath, 
            numModelSteps, optimise, resultsFileStem, costCurveType)
        
        # Set the data spreadsheet upload time for now.
        self.dataUploadTime = today()
        
        # Set the updating time to now.
        self.updatedTime = today()
        
    def saveToPrjFile(self, dirPath, saveResults=False):
        # Create a filename containing the project name followed by a .prj 
        # suffix.
        fileName = '%s.prj' % self.name
        
        # Generate the full file name with path.
        fullFileName = '%s%s%s' % (dirPath, os.sep, fileName)
        
        # Write the object to a Gzip string pickle file.
        objectToGzipStringPickleFile(fullFileName, self)
        
        # Return the full file name.
        return fullFileName
    
def loadProjectFromPrjFile(prj_filename):
    # Return object from the Gzip string pickle file.
    return gzipStringPickleFileToObject(prj_filename)  
      
#
# Pickle / unpickle functions
#

def objectToStringPickle(theObject):
    return pickle.dumps(theObject, protocol=-1)

def stringPickleToObject(theStringPickle):
    return pickle.loads(theStringPickle)

def objectToGzipStringPickleFile(fullFileName, theObject, compresslevel=5):
    # Object a Gzip file object to write to and set the compression level 
    # (which the function defaults to 5, since higher is much slower, but 
    # not much more compact).
    with GzipFile(fullFileName, 'wb', compresslevel=compresslevel) as fileobj:
        # Write the string pickle conversion of the object to the file.
        fileobj.write(objectToStringPickle(theObject))

def gzipStringPickleFileToObject(fullFileName):
    # Object a Gzip file object to read from.
    with GzipFile(fullFileName, 'rb') as fileobj:
        # Read the string pickle from the file.
        theStringPickle = fileobj.read()
        
    # Return the object gotten from the string pickle.    
    return stringPickleToObject(theStringPickle)

def objectToGzipStringPickle(theObject):
    # Start with a null result.
    result = None
    
    # Open a "fake file."
    with closing(StringIO()) as output:
        # Open a Gzip-compressing way to write to this "file."
        with GzipFile(fileobj=output, mode='wb') as fileobj: 
            # Write the string pickle conversion of the object to the "file."
            fileobj.write(objectToStringPickle(theObject))
            
        # Move the mark to the beginning of the "file."
        output.seek(0)
        
        # Read all of the content into result.
        result = output.read()
        
    # Return the read-in result.
    return result

def gzipStringPickleToObject(theGzipStringPickle):
    # Open a "fake file" with the Gzip string pickle in it.
    with closing(StringIO(theGzipStringPickle)) as output:
        # Set a Gzip reader to pull from the "file."
        with GzipFile(fileobj=output, mode='rb') as fileobj: 
            # Read the string pickle from the "file" (applying Gzip 
            # decompression).
            theStringPickle = fileobj.read()  
            
            # Extract the object from the string pickle.
            theObject = stringPickleToObject(theStringPickle)
            
    # Return the object.
    return theObject
        
#
# Misc functions
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

def today():
    ''' Get the current time, in UTC time '''
    now = datetime.datetime.now(dateutil.tz.tzutc())
    return now

def pctChange(startVal, endVal):
    if startVal == 0.0:
        if endVal == 0.0:
            return 0.0
        else:
            return 999999.0
    else:
        return (endVal - startVal) * 100.0 / startVal
    
#
# GUI server functions
#

def getInterventions(theProject):
    # Set up Optimisation object to work with.
    theOpt = theProject.theOptimisation 
    
    # If the optimisation is None, return an empty list.
    if theOpt is None:
        return []
    
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
    
    # If the optimisation is None, return an empty list.
    if theOpt is None:
        return []
    
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
# Script code
#

if __name__ == '__main__':
    #
    # SERVER: Setup and initial GUI info
    #
    
    # Set up Optimisation object to work with.
    rootpath = './'
    #spreadsheet = rootpath + 'input_spreadsheets/Bangladesh/2017Oct/InputForCode_Bangladesh.xlsx'
    spreadsheet = rootpath + 'input_spreadsheets/Bangladesh/gchadder3Test/InputForCode_Bangladesh.xlsx'    
    theProj = Project('demo', spreadsheetPath=spreadsheet)
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