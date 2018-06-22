import nutrition as on

p = on.project.default_project()
on.scenarios.default_scens(p)

p.run_scens()
res = p.get_results('default')

allplots = on.plotting.make_plots(res, toplot=['prevs'])


