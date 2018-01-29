import model2

def setUpModel(filePath):
    model = model2.Model(filePath)
    return model

def getFilePath(root, bookDate, country):
    import os, sys
    moduleDir = os.path.join(os.path.dirname(__file__), root)
    sys.path.append(moduleDir)
    filePath = root + '/input_spreadsheets/' + country + '/' + bookDate + '/InputForCode_' + country + '.xlsx'
    resultsPath = root + '/Results/' + country + '/national/' + bookDate
    return filePath, resultsPath
