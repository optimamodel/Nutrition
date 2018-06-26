from nutrition import data, program_info, populations, model, utils
import sciris.core as sc

class Scen(object):
    def __init__(self, prog_info=None, pops=None, scen_type=None, scen=None, name=None, t=None, prog_set=None, active=True):
        self.scen_type = scen_type
        self.scen = scen
        self.name = name
        self.t = t
        self.prog_set = prog_set
        self.active = active

        self.year_names = range(self.t[0], self.t[1]+1)
        self.all_years = range(len(self.year_names)) # used to index lists
        prog_info = sc.dcp(prog_info)
        pops = sc.dcp(pops)
        self.model = model.Model(name, pops, prog_info, self.all_years)
    
    def __repr__(self):
        output  = sc.desc(self)
        return output

    def run_scen(self):
        """ Define the coverage scenario (list of lists) then run the simulation """
        covs = self.model.prog_info.get_cov_scen(self.scen_type, self.scen)
        self.model.run_sim(covs, restr_cov=False) # coverage restricted in previous func

def make_scens(country=None, region=None, user_opts=None, json=None, project=None, dataset=None):
    """ Define the custom scenarios by providing all necessary information.
    Scenarios defined by user specifications given by the GUI, while the other data remains fixed.
    These scenarios will be returned as a list so they can be added to Project
    """
    demo_data, prog_data, default_params, pops = data.get_data(country=country, region=region, project=project, dataset=dataset, withpops=True)
    scen_list = []
    # create all of the requested scenarios
    if user_opts is not None:
        for opt in user_opts:
            # initialise pops and progs
            prog_info = program_info.ProgramInfo(opt.prog_set, prog_data, default_params)
            # set up scenarios
            scen = Scen(prog_info, pops, **opt.get_attr())
            scen_list.append(scen)
    if json is not None:
        json = sc.dcp(json) # Just to be sure, probably unnecessary
        prog_info = program_info.ProgramInfo(json['prog_set'], prog_data, default_params)
        scen = Scen(prog_info, pops, json['scen_type'], json['scen'], json['name'], json['t'], json['prog_set'], active=True)
        scen_list.append(scen)
    return scen_list