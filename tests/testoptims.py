from nutrition import project, optimisation

p = project.Project()
optimisation.default_optims(p, key='default1', dorun=True)
result = p.get_results('defaul1')






