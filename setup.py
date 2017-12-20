import data2 as data
import populations2 as pops
import programs as progs

def setUpPopulations(project):
    children = pops.Children('children', project)
    PW = pops.PW('PW', project)
    WRA = pops.WRA('WRA', project)
    return [children, PW, WRA]

def setUpProject(filePath):
    project = data.Project(filePath)
    return project

def setUpPrograms(project): # TODO: if each intervention is an object, will need to create these in a loop.
    programs = progs.Program(project)
    pass


if __name__ == 'main':
    filePath = ''
    project = setUpProject(filePath)
    populations = setUpPopulations(project)
    programs = setUpPrograms(project)