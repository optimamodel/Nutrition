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

def setUpPrograms(project):
    programAreas = {}
    for risk, programList in project.programAreas.iteritems():
        programAreas[risk] = []
        for program in programList:
            programAreas[risk].append(progs.Program(program, project))
    return programAreas


if __name__ == '__main__':
    filePath = '/Users/samhainsworth/Desktop/Github Projects/Nutrition/input_spreadsheets/Bangladesh/2017Nov/InputForCode_Bangladesh.xlsx'
    project = setUpProject(filePath)
    populations = setUpPopulations(project)
    programs = setUpPrograms(project)