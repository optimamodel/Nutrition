import model2


def setUpModel(filePath):
    model = model2.Model(filePath)
    return model

def getFilePath(root, bookDate, country):
    import os, sys
    moduleDir = os.path.join(os.path.dirname(__file__), root)
    sys.path.append(moduleDir)
    filePath = root + 'input_spreadsheets/' + country + '/' + bookDate + '/InputForCode_' + country + '.xlsx'
    return filePath

if __name__ == '__main__':
    filePath = getFilePath(root='', bookDate='2017Nov',  country='Bangladesh')
    model = setUpModel(filePath)
    model.applyNewProgramCoverages(model.project.costCurveInfo['baseline coverage'])
    #model.applyUpdates({'Zinc supplementation': .5})
