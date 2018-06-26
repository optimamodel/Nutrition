#######################################################################################################
#%% Imports
#######################################################################################################

import sciris.core as sc
from .version import version
from .model import Model
from .scenarios import make_scens
from .optimization import make_optims
from .results import ScenResult, OptimResult
from .data import Dataset, ScenOptsTest, OptimOptsTest
from .utils import ScenOpts, OptimOpts
from .plotting import make_plots


#######################################################################################################
#%% Project class -- this contains everything else!
#######################################################################################################

class Project(object):
    """
    PROJECT

    The main Nutrition project class. Almost all functionality is provided by this class.

    An Nutrition project is based around 4 major lists:
        1. datasets -- an odict of model/workbook objects
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
        self.datasets    = sc.odict()
        self.scens       = sc.odict()
        self.optims      = sc.odict()
        self.results     = sc.odict()

        ## Define other quantities
        self.name = name
        self.uid = sc.uuid()
        self.created = sc.today()
        self.modified = sc.today()
        self.version = version
        self.gitinfo = sc.gitinfo(__file__)
        self.filename = None # File path, only present if self.save() is used
        self.warnings = None # Place to store information about warnings (mostly used during migrations)

        ## Load burden spreadsheet, if available
        if workbookfile:
            model = Model(workbookfile, **kwargs)
            self.models['default'] = model
        


    def __repr__(self):
        ''' Print out useful information when called '''
        output = sc.objrepr(self)
        output += '      Project name: %s\n'    % self.name
        output += '\n'
        output += '          Datasets: %i\n'    % len(self.datasets)
        output += '         Scenarios: %i\n'    % len(self.scens)
        output += '     Optimizations: %i\n'    % len(self.optims)
        output += '      Results sets: %i\n'    % len(self.results)
        output += '\n'
        output += '      Date created: %s\n'    % sc.getdate(self.created)
        output += '     Date modified: %s\n'    % sc.getdate(self.modified)
        output += '               UID: %s\n'    % self.uid
        output += '  Optima Nutrition: v%s\n'   % self.version
        output += '        Git branch: %s\n'    % self.gitinfo['branch']
        output += '          Git hash: %s\n'    % self.gitinfo['hash']
        output += '============================================================\n'
#        output += self.getwarnings(doprint=False) # Don't print since print later
        return output
    
    
    def getinfo(self):
        ''' Return an odict with basic information about the project'''
        info = sc.odict()
        attrs = ['name', 'version', 'created', 'modified', 'gitbranch', 'gitversion', 'uid']
        for attr in attrs:
            info[attr] = getattr(self, attr) # Populate the dictionary
        return info
    
    
    def save(self, filename=None, folder=None, saveresults=False, verbose=2):
        ''' Save the current project, by default using its name, and without results '''
        fullpath = sc.makefilepath(filename=filename, folder=folder, default=[self.filename, self.name], ext='prj', sanitize=True)
        self.filename = fullpath # Store file path
        if saveresults:
            sc.saveobj(fullpath, self, verbose=verbose)
        else:
            tmpproject = sc.dcp(self) # Need to do this so we don't clobber the existing results
            tmpproject.cleanresults() # Get rid of all results
            sc.saveobj(fullpath, tmpproject, verbose=verbose) # Save it to file
            del tmpproject # Don't need it hanging around any more
        return fullpath

    def add(self, name, item, what=None, overwrite=True):
        """ Add an entry to a structure list """
        structlist = self.getwhat(what=what)
        structlist[name] = item
        print 'Item "{}" added to "{}"'.format(name, what)
        self.modified = sc.today()

    def remove(self, what, name):
        structlist = self.getwhat(what=what)
        structlist.pop(name)
        print '{} "{}" removed'.format(what, name)
        self.modified = sc.today()

    def getwhat(self, what):
        '''
        Return the requested item ('what')
            structlist = getwhat('parameters')
        will return P.parset.
        '''
        if what in ['d', 'ds', 'dataset', 'datasets']: structlist = self.datasets
        elif what in ['s', 'scen', 'scens', 'scenario', 'scenarios']: structlist = self.scens
        elif what in ['o', 'opt', 'opts', 'optim', 'optims', 'optimization', 'optimization', 'optimizations', 'optimizations']: structlist = self.optims
        elif what in ['r', 'res', 'result', 'results']: structlist = self.results
        else: raise Exception("Item not found")
        return structlist

    #######################################################################################################
    ### Utilities
    #######################################################################################################

    def dataset(self, key=None, verbose=2):
        ''' Shortcut for getting the latest model, i.e. self.datasets[-1] '''
        if key is None: key = -1
        try:    return self.datasets[key]
        except: return sc.printv('Warning, dataset set not found!', 1, verbose) # Returns None
    
    def scen(self, key=None, verbose=2):
        ''' Shortcut for getting the latest scenari, i.e. self.scen[-1] '''
        if key is None: key = -1
        try:    return self.scens[key]
        except: return sc.printv('Warning, scenario not found!', 1, verbose) # Returns None
    
    def result(self, key=None, verbose=2):
        ''' Shortcut for getting the latest result, i.e. self.results[-1] '''
        if key is None: key = -1
        try:    return self.results[key]
        except: return sc.printv('Warning, result not found!', 1, verbose) # Returns None
    
    def cleanresults(self):
        ''' Remove all results '''
        for key,result in self.results.items():
            self.results.pop(key)
        
    def add_scen(self, json=None):
        ''' Super roundabout way to add a scenario '''
        scen_list = make_scens(project=self, json=json)
        self.add_scens(scen_list)
        return None
    
    def add_optim(self, json=None):
        ''' Super roundabout way to add a scenario '''
        optim_list = make_optims(project=self, json=json)
        self.add_optims(optim_list)
        return None

    def add_scens(self, scen_list, overwrite=False):
        if overwrite: self.scens = sc.odict() # remove exist scenarios
        for scen in scen_list:
            self.add(name=scen.name, item=scen, what='scen', overwrite=True)
        self.modified = sc.today()

    def add_optims(self, optim_list, overwrite=False):
        if overwrite: self.optims = sc.odict() # remove exist scenarios
        for optim in optim_list:
            self.add(name=optim.name, item=optim, what='optim', overwrite=True)
        self.modified = sc.today()

    def add_result(self, result, name=None):
        """Add result by name"""
        try:
            keyname = result.name
        except Exception as E:
            if name is None:
                print('WARNING, could not extract result name: %s' % repr(E))
                name = 'default_result'
            keyname = name
        self.add(name=keyname, item=result, what='result')

    def default_scens(self, key='default', dorun=None):
        defaults = ScenOptsTest(key, 'coverage')
        opts = [ScenOpts(**defaults.get_attr())] # todo: more than 1 default scen will require another key
        scen_list = make_scens(user_opts=opts, project=self)
        self.add_scens(scen_list)
        if dorun:
            self.run_scens()
        return None
    
    def default_optims(self, key='default', dorun=False):
        defaults = OptimOptsTest(key)
        opts = [OptimOpts(**defaults.get_attr())]
        optim_list = make_optims(user_opts=opts, project=self)
        self.add_optims(optim_list)
        if dorun:
            self.run_optims()
        return None
    
    def run_scens(self, scen_list=None):
        """Function for running scenarios"""
        if scen_list is not None: self.add_scens(scen_list) # replace existing scen list with new one
        scens = sc.dcp(self.scens)
        results = []
        for scen in scens.itervalues():
            scen.run_scen()
            result = ScenResult(scen)
            results.append(result)
        self.add_result(results, name='Scenarios')
        return None

    def run_optims(self, optim_list=None, name=None):
        if optim_list is not None: self.add_optims(optim_list)
        if name is None: name = 'optimizations'
        optims = sc.dcp(self.optims)
        for optim in optims.itervalues():
            optim.run_optim()
            result = OptimResult(optim)
            self.add_result(result)
    
    def get_results(self, result_keys):
        """ result_keys is a list of keys corresponding to the desired result.
        Return: a list of result objects """
        return [self.results[key] for key in result_keys]

    def sensitivity(self):
        print('Not implemented')
    
    
    def plot(self, key=None, toplot=None):
        figs = make_plots(self.result(key), toplot=toplot)
        return figs

def demo():
    ''' Create a demo project with default settings '''
    
    # Parameters
    name = 'Demo project'
    country = 'default'
    region = 'default'
    
    # Create project and data
    P = Project(name)
    dataset = Dataset(country, region, doload=True)
    P.datasets[dataset.name] = dataset
    
    # Create scenarios and optimizations
    P.default_scens()
    P.default_optims()
    return P