import model2
from datetime import date

def setUpModel(filePath, adjustCoverage=True, optimise=False):
    model = model2.Model(filePath, adjustCoverage=adjustCoverage, optimise=optimise) # model has already moved 1 year
    return model

def getFilePath(root, bookDate, country):
    import os, sys
    moduleDir = os.path.join(os.path.dirname(__file__), root)
    sys.path.append(moduleDir)
    filePath = root + 'input_spreadsheets/' + country + '/' + bookDate + '/InputForCode_' + country + '.xlsx'
    today = date.today()
    resultsPath = root + 'Results/' + country + '/national/' + today.strftime('%Y%b%d')
    return filePath, resultsPath


if __name__ == '__main__':
    filePath = getFilePath('', '2017Nov', 'Bangladesh')[0]
    model = setUpModel(filePath)
    model.runSimulationFromWorkbook()
    print model.getOutcome('thrive')
