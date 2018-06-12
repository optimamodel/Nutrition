from nutrition import project, optimisation, data

country = 'master'
region = 'master'

user_opts = [data.DefaultOptimOpts('optimtest1')]

optim_list = optimisation.make_optims(country, region, user_opts)

p = project.Project()
p.add_optims(optim_list)
p.run_optims()







