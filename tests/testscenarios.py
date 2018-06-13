from nutrition import project, scenarios

p = project.Project()
scenarios.default_scens(p, key='default', dorun=True)
result = p.get_results('default')








