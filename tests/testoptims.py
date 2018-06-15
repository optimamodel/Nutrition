import nutrition as on

p = on.project.Project()
p.default_optims(key='default', dorun=True)
res = p.get_results('default')
