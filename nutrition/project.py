## For starters, should contain odicts for scenarios, optimisations, and results

from nutrition import model2, populations, program_info, settings
from utils import odict, today
import loadspreadsheet

class Project(object):
    """
    #TODO
    """
    def __init__(self, spreadsheet, name='default'):

        ## Define the structure sets
        self.parsets = {} # TODO: populated by wrapper for Model
        self.progsets = {} # TODO: populated by wrapper for Model which extracts info for ProgramInfo
        self.scens = {}
        self.optims = {}
        self.results = {}

        ## Define other quantities
        self.name = name
        self.settings = settings.Settings()
        self.data = loadspreadsheet.InputData(spreadsheet) # once uploaded, assume these values are fixed for all projects
        self.user_settings = loadspreadsheet.UserSettings()
        self.default_params = loadspreadsheet.DefaultParams()

        ## Define metadata
        self.created = today()
        self.modified = today()
        self.spreadsheetdate = 'Spreadsheet never loaded'

    def add(self, name, item, what=None, overwrite=True):
        """ Add an entry to a structure list """
        structlist = self.getwhat(what=what)
        structlist[name] = item
        print 'Item "{}" added to "{}"'.format(name, what)
        self.modified = today()

    def remove(self, what, name):
        structlist = self.getwhat(what=what)
        structlist.pop(name)
        print '{} "{}" removed'.format(what, name)
        self.modified = today()

    def getwhat(self, what):
        '''
        Return the requested item ('what')
            structlist = getwhat('parameters')
        will return P.parset.
        '''
        if what in ['p', 'pars', 'parset', 'parameters']: structlist = self.parsets
        elif what in ['pr', 'progs', 'progset', 'progsets']: structlist = self.progsets
        elif what in ['s', 'scen', 'scens', 'scenario', 'scenarios']: structlist = self.scens
        elif what in ['o', 'opt', 'opts', 'optim', 'optims', 'optimisation', 'optimization', 'optimisations', 'optimizations']: structlist = self.optims
        elif what in ['r', 'res', 'result', 'results']: structlist = self.results
        else: raise Exception("Item not found")
        return structlist

    def add_scens(self, scen_list, overwrite=True):
        if overwrite: self.scens = {} # remove exist scenarios
        for scen in scen_list:
            self.add(name=scen.name, item=scen, what='scen', overwrite=True)
        self.modified = today()

    def add_result(self, my_model):
        """Add result by name"""
        keyname = my_model.name
        self.add(name=keyname, item=my_model, what='result')
        return

    def run_scens(self, scen_list=None, name=None):
        """Function for running scenarios"""
        if scen_list is not None: self.add_scens(scen_list) # replace existing scen list with new one
        if name is None: name = 'scenarios'
        # TODO: currently not implemented
        # TODO: extract information from the scen_list one at a time and run
        for scen in self.scens:
            pops = populations.set_pops(self.data, self.default_params, self.settings)
            prog_set = self.user_settings.prog_set # TODO: make this dynamic so can define for different scenarios
            prog_info = program_info.ProgramInfo(self.data, self.user_settings, self.default_params,
                                                 prog_set=prog_set, name=name) # none of the coverage info is set here, since it depends on pop sizes
            start_year = self.user_settings.start_year
            end_year = self.user_settings.end_year
            covs = self.user_settings.covs

            my_model = model2.Model(name, pops, prog_info, start_year, end_year)
            my_model.run_sim(covs)
            self.add_result(my_model=my_model)
        self.modified = today()

    def run_sim(self, name, pops, covs, prog_info, start_year, end_year): # TODO: Should keep this? If so, put outside class?
        """Performs a single run of the model for specified scenario"""
        # the things which vary between scenario runs within the same project are:
        # - annual prog spending/cov
        # - numYears
        # - progSet
        # - prog dependencies (?)
        # - referenceSet (?)

        # set up the model
        myModel = model2.Model(name, pops, prog_info, start_year, end_year)
        myModel.run_sim(covs)

        return myModel

    def optimise(self): # TODO: for optimising the model. Could call optimise in the Optimisation class

        return


    def sensitivity(self): # TODO: sensitivity analysis over the parameters as
        return

class Test(object):
    def __init__(self, name):
        self.name = name

if __name__ == "__main__":
    names = ['thing1', 'thing2', 'thing3']
    objs = [Test(name) for name in names]
    # TESTING
    P = Project('../applications/master/data/national/master_input.xlsx', 'test')
    P.add_scens(objs)
    P.run_scens()
    










