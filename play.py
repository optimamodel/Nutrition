import model
import data
from datetime import date
import os, sys

def setUpModel(filePath, numYears=None, adjustCoverage=False, optimise=False, calibrate=True):
    myModel = model.Model(filePath, numYears=numYears, adjustCoverage=adjustCoverage, optimise=optimise, calibrate=calibrate) # model has already moved 1 year
    return myModel

def setUpProject(filePath):
    return data.setUpProject(filePath)

def getFilePath(root, analysisType, name):
    moduleDir = os.path.join(os.path.dirname(__file__), root)
    sys.path.append(moduleDir)
    filePath = os.path.join(root, 'data', analysisType, 'InputForCode_{}.xlsx'.format(name))
    return filePath

def getResultsDir(root, country, scenario):
    today = date.today()
    thisDate = today.strftime('%Y%b%d')
    resultsPath = os.path.join(root, 'Results', country, scenario, thisDate)
    return resultsPath

if __name__ == '__main__': # this is just for testing
    root = os.path.join('Projects', 'Master')
    filePath = getFilePath(root=root, analysisType='national', name='Master')
    myModel = setUpModel(filePath)
    myModel.runSimulationFromWorkbook()