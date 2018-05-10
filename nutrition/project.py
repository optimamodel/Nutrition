## For starters, should contain odicts for scenarios, optimisations, and results

from nutrition import model2, populations, program_info
from utils import odict, today
import loadspreadsheet

class Project(object):
    """
    #TODO
    """
    def __init__(self, name='default'):

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
        self.default_params = loadspreadsheet.DefaultParams(country) # TODO: would like to specify 'filename, folder' like in HIV
        self.data = loadspreadsheet.InputData() # assume these values fixed for all projects, since they are real life data

        ## Define metadata
        # self.uid = uuid() # TODO: for storing in database? from utils
        self.created = today()
        self.modified = today()
        self.spreadsheetdate = 'Spreadsheet never loaded'
        # self.version = version
        # self.gitbranch, self.gitversion = gitinfo()

    def runScenarios(self, scenList=None, name=None):
        """Function for running scenarios"""
        if scenList is not None: self.addScens(scenList) # replace existing scen list with new one
        if name is None: name = 'scenarios'

        self.pops = populations.setPops(self.data, self.constants) # TODO: rethink usage of constants...
        self.prog_info = program_info.ProgramInfo(self.constants, prog_set) # none of the coverage info is set here, since it depends on pop sizes
        # need to provide

        # scenRes = runScenarios() # TODO: this is imported from another module, does all the work
        scenRes = self.runSim() # TODO: better alternative to above?
        self.addResult(result=scenRes[name])
        self.modified = today()
        return scenRes

    def run_sim(self): # TODO: could have this called by 'runScenarios', and cut out the middle-man of 'scenarios.py'
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
        myModel = model2.Model() # TODO: pass in the data.
        myModel.run_sim()




        return

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




    










