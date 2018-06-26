import nutrition as on

p = on.project.demo()
p.default_optims(dorun=True)
res = p.get_results(['default'])
allplots = on.plotting.make_plots(res, toplot=['alloc'])
