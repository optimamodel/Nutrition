import nutrition as on

p = on.project.demo()
p.run_scens()
p.run_optims()
res = p.get_results(['Scenarios'])
