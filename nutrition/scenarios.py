from nutrition import settings, data, program_info, populations, model
from copy import deepcopy as dcp

class Scen(object):
    def __init__(self, scen_type, scen, name, prog_info, pops, active=True):
        self.scen_type = scen_type
        self.name = name
        self.t = scen.t
        self.year_names = range(self.t[0], self.t[1]+1)
        self.all_years = range(len(self.year_names)) # used to index lists

        self.prog_info = dcp(prog_info)
        self.pops = dcp(pops)
        self.scen = scen
        self.set_progs(pops)
        self.model = model.Model(name, self.pops, self.prog_info, self.all_years)
        self.active = active

    def set_progs(self, pops):
        self.prog_info.set_years(self.all_years)
        self.prog_info.set_init_covs(pops, self.all_years)
        self.prog_info.set_costcovs() # enables getting coverage from cost

    def run_scen(self):
        """ Define the coverage scenario (list of lists) then run the simulation """
        covs = self.prog_info.get_cov_scen(self.scen_type, self.scen)
        self.model.run_sim(covs, restr_cov=False) # coverage restricted in previous func

def make_scens(country, region, sim_type, prog_data, scen_names, scen_types):
    """ Define the custom scenarios by providing all necessary information.
    Scenarios defined by user specifications given by the GUI, while the other data remains fixed.
    These scenarios will be returned as a list so they can be added to Project
    """
    input_path = settings.data_path(country, region, sim_type)
    default_path = settings.default_path()
    # get data
    input = data.InputData(input_path)
    default_params = data.DefaultParams(default_path)
    scen_list = []
    # create all of the requested scenarios
    for i, name in enumerate(scen_names):
        scen_type = scen_types[i]
        scen_progs = prog_data[i]
        # initialise pops and progs
        prog_info = program_info.ProgramInfo(scen_progs, default_params)
        pops = populations.set_pops(input, default_params)
        # set up scenarios
        scen = Scen(scen_type, scen_progs, name, prog_info, pops)
        scen_list.append(scen)
    return scen_list


def default_scens(project, dorun=False):
    country = 'master'
    region = 'master'
    sim_type = 'national'
    names = ['test1']
    scen_types = ['Coverage']
    
    input_path = settings.data_path(country, region, sim_type)
    prog_path = settings.prog_path(country, sim_type) # this should come from the GUI
    prog_data = [data.ProgData(prog_path, input_path)]
    
    scen_list = make_scens(country, region, sim_type, prog_data, names, scen_types)
    project.add_scens(scen_list)
    
    if dorun:
        project.run_scens()
    
    return None
    