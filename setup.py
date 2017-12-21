import data2 as data
import populations2 as pops
import programs as progs


def setUpModel(filePath):
    project = data.setUpProject(filePath)
    populations = pops.setUpPopulations(project)
    programs = progs.setUpPrograms(project)
    # TODO: setup model function here
    return populations, programs

def getFilePath(root, bookDate, country):
    import os, sys
    moduleDir = os.path.join(os.path.dirname(__file__), root)
    sys.path.append(moduleDir)
    filePath = root + 'input_spreadsheets/' + country + '/' + bookDate + '/InputForCode_' + country + '.xlsx'
    return filePath

if __name__ == '__main__':
    filePath = getFilePath('', '2017Nov',  'Bangladesh')
    populations, programs = setUpModel(filePath)
