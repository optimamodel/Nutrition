from nutrition import data, program_info, populations, model, utils
from copy import deepcopy as dcp

class Scen(object):
    def __init__(self, prog_info, pops, scen_type, scen, name, t, prog_set, active=True):
        self.scen_type = scen_type
        self.scen = scen
        self.name = name
        self.t = t
        self.prog_set = prog_set
        self.active = active

        self.year_names = range(self.t[0], self.t[1]+1)
        self.all_years = range(len(self.year_names)) # used to index lists
        prog_info = dcp(prog_info)
        pops = dcp(pops)
        self.model = model.Model(name, pops, prog_info, self.all_years)

    def run_scen(self):
        """ Define the coverage scenario (list of lists) then run the simulation """
        covs = self.model.prog_info.get_cov_scen(self.scen_type, self.scen)
        self.model.run_sim(covs, restr_cov=False) # coverage restricted in previous func

def make_scens(country, region, user_opts):
    """ Define the custom scenarios by providing all necessary information.
    Scenarios defined by user specifications given by the GUI, while the other data remains fixed.
    These scenarios will be returned as a list so they can be added to Project
    """
    demo_data, prog_data, default_params = data.get_data(country, region)
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

def default_scens(project, key='default', dorun=False):
    country = 'default'
    region = 'default'

    defaults = data.ScenOptsTest(key, 'coverage')
    opts = [utils.ScenOpts(**defaults.get_attr())] # todo: more than 1 default scen will require another key
    scen_list = make_scens(country, region, opts)
    project.add_scens(scen_list)
    
    if dorun:
        project.run_scens()