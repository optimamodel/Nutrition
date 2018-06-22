import nutrition as on

p = on.project.default_project()
p.default_scens(dorun=True)
res = p.get_results('default')

allplots = on.plotting.make_plots(res, toplot=['prevs'])