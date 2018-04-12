import model
import data
from datetime import date
import os, sys

def setUpModel(filePath, numYears=None, adjustCoverage=False, optimise=False, calibrate=True):
    myModel = model.Model(filePath, numYears=numYears, adjustCoverage=adjustCoverage, optimise=optimise, calibrate=calibrate) # model has already moved 1 year
    return myModel

def setUpProject(filePath):
    return data.setUpProject(filePath)

def getFilePath(root, country, name):
    moduleDir = os.path.join(os.path.dirname(__file__), root)
    sys.path.append(moduleDir)
    filePath = os.path.join(root, 'input_spreadsheets', country, 'InputForCode_{}.xlsx'.format(name))
    return filePath

def getResultsDir(root, country, analysisType):
    today = date.today()
    thisDate = today.strftime('%Y%b%d')
    resultsPath = os.path.join(root, 'Results', country, analysisType, thisDate)
    return resultsPath

if __name__ == '__main__':
    filePath = getFilePath('', 'Master', 'Master')
    myModel = setUpModel(filePath)
    myModel.runSimulationFromWorkbook()