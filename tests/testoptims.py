import nutrition as on

country = 'master'
region = 'master'
name = 'test'

p = on.project.Project(name)

defaults = on.data.OptimOptsTest(name, filepath=on.settings.test_opts_path())
opts = [on.utils.OptimOpts(**defaults.get_attr())]
optim_list = on.optimisation.make_optims(country, region, opts)
p.add_optims(optim_list)

p.run_optims()

