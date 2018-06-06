from nutrition import project, scenarios, data, plotting
from nutrition import settings

country = 'master'
region = 'master'
sim_type = 'national'
names = ['test1']
scen_types = ['Coverage']

input_path = settings.data_path(country, region, sim_type)
prog_path = settings.prog_path(country, sim_type) # this should come from the GUI
prog_data = [data.ProgData(prog_path, input_path)]

scen_list = scenarios.make_scens(country, region, sim_type, prog_data, names, scen_types)

p = project.Project()
p.add_scens(scen_list)

from time import time
now = time()
p.run_scens()
print time() - now
result = p.get_results('test1')
print result.model.get_outcome('thrive')

# plotting.make_plots(result) # HARDCODED EXAMPLE








