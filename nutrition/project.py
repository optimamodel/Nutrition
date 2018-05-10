## For starters, should contain odicts for scenarios, optimisations, and results

from nutrition import model2, populations, program_info
from utils import odict, today
import loadspreadsheet

class Project(object):
    """
    #TODO
    """
    def __init__(self, spreadsheet, name='default'):

        ## Define the structure sets
        # TODO: we don't have a 'parset', since these are stored elsewhere
        self.parsets = odict()
        self.progsets = odict() # TODO: can come from user input, for now read from spreadsheet
        self.scens = odict()
        self.optims = odict()
        self.results = odict()

        ## Define other quantities
        self.name = name
        # self.setting = Settings() # TODO: this is essentially 'Constants'
        # self.data = odict() # TODO: currently we have the Data object...
        self.default_params = loadspreadsheet.DefaultParams()
        self.data = loadspreadsheet.InputData(spreadsheet) # assume these values fixed for all projects, since they are real life data
        self.user_settings = loadspreadsheet.UserSettings(spreadsheet)

        ## Define metadata
        self.created = today()
        self.modified = today()
        self.spreadsheetdate = 'Spreadsheet never loaded'

    def runScenarios(self, scenList=None, name=None): #TODO: should be able to run several scenarios at once, defined before-hand
        """Function for running scenarios"""
        if scenList is not None: self.addScens(scenList) # replace existing scen list with new one
        if name is None: name = 'scenarios'

        pops = populations.setPops(self.data, self.constants) # TODO: rethink usage of constants...
        prog_set = self.user_settings.prog_set # TODO: make this dynamic so can define for different scenarios
        prog_info = program_info.ProgramInfo(self.constants, prog_set) # none of the coverage info is set here, since it depends on pop sizes
        start_year = self.user_settings.start_year
        end_year = self.user_settings.end_year
        covs = self.user_settings.covs

        scenRes = self.runSim(pops, covs, prog_info, start_year, end_year)
        self.addResult(result=scenRes[name])
        self.modified = today()
        return scenRes

    def run_sim(self, pops, covs, prog_info, start_year, end_year): # TODO: could have this called by 'runScenarios', and cut out the middle-man of 'scenarios.py'
        # TODO: should specify the key requirements for a model run here
        """Performs a single run of the model for specified scenario"""
        # the things which vary between scenario runs within the same project are:
        # - annual prog spending/cov
        # - numYears
        # - progSet
        # - prog dependencies (?)
        # - referenceSet (?)

        # set up the model
        # TODO: would like to pass in prog coverage data type, and see if scalar or sequence...
        myModel = model2.Model(pops, prog_info, start_year, end_year)
        myModel.run_sim(covs)


        return

    def make_defaults(self):
        progset =

    def optimise(self): # TODO: for optimising the model. Could call optimise in the Optimisation class

        return

    def addResult(self, result=None, overwrite=True):
        """Add result by name"""
        keyname = result.name
        self.add(what='result', name=keyname, item=result, overwrite=overwrite)
        return

    def addScen(self):
        """Add a scenario"""
        return







    def sensitivity(self): # TODO: sensitivity analysis over the parameters as
        return




    










