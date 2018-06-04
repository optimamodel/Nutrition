"""
Version:
"""

import nutrition as on

country = 'master'
region = 'master'
sim_type = 'national'
names = ['test1']
scen_types = ['Coverage']

input_path = on.settings.data_path(country, region, sim_type)
prog_path = on.settings.prog_path(country, sim_type) # this should come from the GUI
prog_data = [on.data.ProgData(prog_path, input_path)]

scen_list = on.scenarios.make_scens(country, region, sim_type, prog_data, names, scen_types)

p = on.project.Project()
p.add_scens(scen_list)

p.run_scens()
result = p.get_results('test1')

on.plotting.make_plots(result) # HARDCODED EXAMPLE








