import model2
import data2
from datetime import date
import os, sys

def setUpModel(filePath, adjustCoverage=False, optimise=False, numYears=None):
    model = model2.Model(filePath, adjustCoverage=adjustCoverage, optimise=optimise, numYears=numYears) # model has already moved 1 year
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

if __name__ == '__main__':
    # filePath = getFilePath('', 'Master', 'Master')
    filePath = '/Users/samhainsworth/Desktop/Github Projects/Nutrition/input_spreadsheets/Tanzania/regions/InputForCode_Kaskazini_Unguja.xlsx'
    model = setUpModel(filePath)
    model.runSimulationFromWorkbook()