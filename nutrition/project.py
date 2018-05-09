## For starters, should contain odicts for scenarios, optimisations, and results

from nutrition import model, populations, program_info
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
        self.defaultParams = loadspreadsheet.DefaultParams(country) # TODO: would like to specify 'filename, folder' like in HIV
        self.data = loadspreadsheet.InputData() # assume these values fixed for all projects, since they are real life data
        self.userSettings = None

        ## Define metadata
        # self.uid = uuid() # TODO: for storing in database? from utils
        self.created = today()
        self.modified = today()
        self.spreadsheetdate = 'Spreadsheet never loaded'
        # self.version = version
        # self.gitbranch, self.gitversion = gitinfo()

    def settings(self):
        """Get the user-defined settings for each scenario"""
        self.userSettings = loadspreadsheet.UserSettings()

        return

    def runScenarios(self, scenList=None, name=None):
        """Function for running scenarios"""
        if scenList is not None: self.addScens(scenList) # replace existing scen list with new one
        if name is None: name = 'scenarios'

        self.pops = populations.setPops(self.data, self.constants) # TODO: rethink usage of constants...
        self.progInfo = program_info.ProgramInfo(self.constants, progset) # none of the coverage info is set here, since it depends on pop sizes
        myModel = model.Model(self.pops, self.progInfo)


        # scenRes = runScenarios() # TODO: this is imported from another module, does all the work
        scenRes = self.runSim() # TODO: better alternative to above?
        self.addResult(result=scenRes[name])
        self.modified = today()
        return scenRes

    def runSim(self): # TODO: could have this called by 'runScenarios', and cut out the middle-man of 'scenarios.py'
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
        myModel = model.Model() # TODO: pass in the data.
        myModel.runSimulation() # TODO: can do this once set everything up.




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




    










