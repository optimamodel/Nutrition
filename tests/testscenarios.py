import nutrition as on

p = on.project.demo()
p.run_scens()
#p.run_optims()
p.plot(key='Scenarios', toplot='outputs')
#res = p.get_results(['Scenarios'])
