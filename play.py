import model2
import data2
from datetime import date
import os, sys

def setUpModel(filePath, adjustCoverage=True, optimise=False):
    model = model2.Model(filePath, adjustCoverage=adjustCoverage, optimise=optimise) # model has already moved 1 year
    return model

def setUpProject(filePath):
    return data2.setUpProject(filePath)

def getFilePath(root, country, name):
    moduleDir = os.path.join(os.path.dirname(__file__), root)
    sys.path.append(moduleDir)
    filePath = '{}/input_spreadsheets/{}/InputForCode_{}.xlsx'.format(root, country, name)
    return filePath

def getResultsDir(root, country, analysisType):
    today = date.today()
    thisDate = today.strftime('%Y%b%d')
    resultsPath = '{}Results/{}/{}/{}'.format(root, country, analysisType, thisDate)
    return resultsPath

