from nutrition import project, scenarios, data
from nutrition import settings

country = 'master'
region = 'master'
sim_type = 'national'
names = ['test1', 'test2']
scen_types = ['Coverage', 'Coverage']

input_path = settings.data_path(country, region, sim_type)
prog_path = settings.prog_path(country, sim_type) # this should come from the GUI
prog_data = [data.ProgData(prog_path, input_path), data.ProgData(prog_path, input_path)]

scen_list = scenarios.make_scens(country, region, sim_type, prog_data, names, scen_types)

p = project.Project()
p.add_scens(scen_list)
p.run_scens()
result = p.get_results('test1')








