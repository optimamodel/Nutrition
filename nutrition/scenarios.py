def runScenarios(project=None, name=None): # TODO: this is to be called within the project class in a 'runScenarios' method.
    if project is None: raise Exception("First argument of runScenarios must be a project")
    scenList = [scen for scen in project.scens.values() if scen.active==True]
    nscens = len(scenList)

    # TODO: need to convert the parsets of project?

    # run scenarios
    allResults = []
    for scenno, scen in enumerate(scenparsets):





