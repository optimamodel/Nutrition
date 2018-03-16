import model2
import data2
from datetime import date

def setUpModel(filePath, adjustCoverage=False, optimise=False, numYears=None):
    model = model2.Model(filePath, adjustCoverage=adjustCoverage, optimise=optimise, numYears=numYears) # model has already moved 1 year
    return model

def setUpProject(filePath):
    return data2.setUpProject(filePath)

def getFilePath(root, bookDate, country):
    import os, sys
    moduleDir = os.path.join(os.path.dirname(__file__), root)
    sys.path.append(moduleDir)
    filePath = root + 'input_spreadsheets/' + country + '/' + bookDate + '/InputForCode_' + country + '.xlsx'
    today = date.today()
    resultsPath = root + 'Results/' + country + '/national/' + today.strftime('%Y%b%d')
    return filePath, resultsPath


if __name__ == '__main__':
    filePath = getFilePath('', '', 'Master')[0]
    model = setUpModel(filePath)
    model.runSimulationFromWorkbook()
