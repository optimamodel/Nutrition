from nutrition import settings, data, program_info, populations, model
from copy import deepcopy as dcp

class Scen(object):
    def __init__(self, prog_info, pops, scen_type, scen, name, t, prog_set, active=True):
        self.scen_type = scen_type
        self.scen = scen
        self.name = name
        self.t = t
        self.prog_set = prog_set
        self.year_names = range(self.t[0], self.t[1]+1)
        self.all_years = range(len(self.year_names)) # used to index lists

        self.prog_info = dcp(prog_info)
        self.pops = dcp(pops)
        self.model = model.Model(name, self.pops, self.prog_info, self.all_years)
        self.active = active

    def run_scen(self):
        """ Define the coverage scenario (list of lists) then run the simulation """
        covs = self.prog_info.get_cov_scen(self.scen_type, self.scen)
        self.model.run_sim(covs, restr_cov=False) # coverage restricted in previous func

def make_scens(country, region, user_opts):
    """ Define the custom scenarios by providing all necessary information.
    Scenarios defined by user specifications given by the GUI, while the other data remains fixed.
    These scenarios will be returned as a list so they can be added to Project
    """
    sim_type = 'national' if country == region else 'regional'
    input_path = settings.data_path(country, region, sim_type)
    default_path = settings.default_path()
    # get data
    demo_data = data.InputData(input_path)
    prog_data = data.ProgData(input_path)
    default_params = data.DefaultParams(default_path)
    scen_list = []
    # create all of the requested scenarios
    for opt in user_opts:
        # initialise pops and progs
        prog_info = program_info.ProgramInfo(opt.prog_set, prog_data, default_params)
        pops = populations.set_pops(demo_data, default_params)
        # set up scenarios
        scen = Scen(prog_info, pops, **opt.get_attr())
        scen_list.append(scen)
    return scen_list


def default_scens(project, dorun=False):
    country = 'master'
    region = 'master'

    default_opts1 = data.DefaultOpts('test1', 'Coverage')
    user_opts = [default_opts1]

    scen_list = make_scens(country, region, user_opts)

    p = project.Project()
    p.add_scens(scen_list)

    if dorun:
        project.run_scens()
    
    return None
    