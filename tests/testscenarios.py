import nutrition as on

p = on.project.demo()
p.run_scens()
fig = p.plot(key='Scenarios', toplot='outputs')
