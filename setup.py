import model2
from copy import deepcopy as dcp

def setUpModel(filePath, optimise=False):
    model = model2.Model(filePath, optimise=optimise) # model has already moved 1 year
    return model

def getFilePath(root, bookDate, country):
    import os, sys
    moduleDir = os.path.join(os.path.dirname(__file__), root)
    sys.path.append(moduleDir)
    filePath = root + 'input_spreadsheets/' + country + '/' + bookDate + '/InputForCode_' + country + '.xlsx'
    resultsPath = root + '/Results/' + country + '/national/' + bookDate
    return filePath, resultsPath


if __name__ == '__main__':
    filePath = getFilePath('', '', 'Master')[0]
    model = setUpModel(filePath)
    model.runSimulation()
    print model.getOutcome('thrive')
