from nutrition import project, scenarios, data, plotting

country = 'master'
region = 'master'

default_opts1 = data.DefaultOpts('test1', 'Coverage')
default_opts2 = data.DefaultOpts('test2', 'Budget')
user_opts = [default_opts1, default_opts2]

scen_list = scenarios.make_scens(country, region, user_opts)

p = project.Project()
p.add_scens(scen_list)

from time import time
now = time()
p.run_scens()
print time() - now

# result = p.get_results('test1')

# plotting.make_plots(result) # HARDCODED EXAMPLE








