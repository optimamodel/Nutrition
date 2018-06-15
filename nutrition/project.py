from sciris.core import odict, uuid, today, gitinfo, objrepr, getdate, printv, makefilepath, saveobj, dcp
from .model import Model
from .scenarios import default_scens
from .optimisation import default_optims
from .results import ScenResult, OptimResult
from . import version

#######################################################################################################
## Project class -- this contains everything else!
#######################################################################################################

class Project(object):
    """
    PROJECT

    The main Nutrition project class. Almost all functionality is provided by this class.

    An Nutrition project is based around 4 major lists:
        1. models -- an odict of model/workbook objects
        2. scens -- an odict of scenario structures
        3. optims -- an odict of optimization structures
        4. results -- an odict of results associated with the choices above


    Methods for structure lists:
        1. add -- add a new structure to the odict
        2. remove -- remove a structure from the odict
        3. copy -- copy a structure in the odict
        4. rename -- rename a structure in the odict

    Version: 2018apr19
    """



    #######################################################################################################
    ### Built-in methods -- initialization, and the thing to print if you call a project
    #######################################################################################################

    def __init__(self, name='default', workbookfile=None, **kwargs):
        ''' Initialize the project '''

        ## Define the structure sets
        self.models      = odict()
        self.scens       = odict()
        self.optims      = odict()
        self.results     = odict()

        ## Define other quantities
        self.name = name
        self.uid = uuid()
        self.created = today()
        self.modified = today()
        self.version = version
        self.gitinfo = gitinfo(__file__)
        self.filename = None # File path, only present if self.save() is used
        self.warnings = None # Place to store information about warnings (mostly used during migrations)

        ## Load burden spreadsheet, if available
        if workbookfile:
            model = Model(workbookfile, **kwargs)
            self.models['default'] = model
        


    def __repr__(self):
        ''' Print out useful information when called '''
        output = objrepr(self)
        output += '      Project name: %s\n'    % self.name
        output += '\n'
        output += '            Models: %i\n'    % len(self.models)
        output += '         Scenarios: %i\n'    % len(self.scens)
        output += '     Optimizations: %i\n'    % len(self.optims)
        output += '      Results sets: %i\n'    % len(self.results)
        output += '\n'
        output += '      Date created: %s\n'    % getdate(self.created)
        output += '     Date modified: %s\n'    % getdate(self.modified)
        output += '               UID: %s\n'    % self.uid
        output += '  Optima Nutrition: v%s\n'   % self.version
        output += '        Git branch: %s\n'    % self.gitinfo['branch']
        output += '          Git hash: %s\n'    % self.gitinfo['hash']
        output += '============================================================\n'
#        output += self.getwarnings(doprint=False) # Don't print since print later
        return output
    
    
    def getinfo(self):
        ''' Return an odict with basic information about the project'''
        info = odict()
        for attr in ['name', 'version', 'created', 'modified', 'gitbranch', 'gitversion', 'uid']:
            info[attr] = getattr(self, attr) # Populate the dictionary
#        info['parsetkeys'] = self.parsets.keys()
#        info['progsetkeys'] = self.parsets.keys()
        return info
    
    
    def save(self, filename=None, folder=None, saveresults=False, verbose=2):
        ''' Save the current project, by default using its name, and without results '''
        fullpath = makefilepath(filename=filename, folder=folder, default=[self.filename, self.name], ext='prj', sanitize=True)
        self.filename = fullpath # Store file path
        if saveresults:
            saveobj(fullpath, self, verbose=verbose)
        else:
            tmpproject = dcp(self) # Need to do this so we don't clobber the existing results
            tmpproject.cleanresults() # Get rid of all results
            saveobj(fullpath, tmpproject, verbose=verbose) # Save it to file
            del tmpproject # Don't need it hanging around any more
        return fullpath

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

    #######################################################################################################
    ### Utilities
    #######################################################################################################

    def model(self, key=-1, verbose=2):
        ''' Shortcut for getting the latest model, i.e. self.models[-1] '''
        try:    return self.models[key]
        except: return printv('Warning, burden set not found!', 1, verbose) # Returns None
    
    def cleanresults(self):
        ''' Remove all results '''
        for key,result in self.results.items():
            self.results.pop(key)

    def add_scens(self, scen_list, overwrite=True):
        if overwrite: self.scens = {} # remove exist scenarios
        for scen in scen_list:
            self.add(name=scen.name, item=scen, what='scen', overwrite=True)
        self.modified = today()

    def add_optims(self, optim_list, overwrite=True):
        if overwrite: self.optims = {} # remove exist scenarios
        for optim in optim_list:
            self.add(name=optim.name, item=optim, what='optim', overwrite=True)
        self.modified = today()

    def add_result(self, result):
        """Add result by name"""
        keyname = result.name
        self.add(name=keyname, item=result, what='result')

    def run_scens(self, scen_list=None, name=None):
        """Function for running scenarios"""
        if scen_list is not None: self.add_scens(scen_list) # replace existing scen list with new one
        if name is None: name = 'scenarios'
        scens = dcp(self.scens)
        for scen in scens.itervalues():
            scen.run_scen()
            result = ScenResult(scen)
            self.add_result(result)

    def default_scens(self, key='default', dorun=None):
        default_scens(self, key=key, dorun=dorun)

    def default_optims(self, key='default', dorun=None):
        default_optims(self, key=key, dorun=dorun)

    def run_optims(self, optim_list=None, name=None):
        if optim_list is not None: self.add_optims(optim_list)
        if name is None: name = 'optimizations'
        optims = dcp(self.optims)
        for optim in optims.itervalues():
            optim.run_optim()
            result = OptimResult(optim)
            self.add_result(result)

    def get_results(self, result_key):
        return self.results[result_key]

    def sensitivity(self):
        print('Not implemented')

