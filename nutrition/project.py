#######################################################################################################
#%% Imports
#######################################################################################################

import numpy as np
import sciris as sc
from .version import version
from .optimization import Optim
from functools import partial
from .data import Dataset
from .scenarios import Scen, run_scen
from .plotting import make_plots, get_costeff
from .model import Model
from .utils import trace_exception, default_trackers, pretty_labels, run_parallel
from .demo import demo_scens, demo_optims
from .defaults import get_defaults
from . import settings


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

    def __init__(self, name='default', loadsheets=True, inputspath=None, defaultspath=None):
        ''' Initialize the project '''

        ## Define the structure sets
        self.datasets = sc.odict()
        self.models   = sc.odict()
        self.scens    = sc.odict()
        self.optims   = sc.odict()
        self.results  = sc.odict()
        self.input_sheet    = None
        self.defaults_sheet = None
        if loadsheets:
            if not inputspath:
                template_name = 'template_input.xlsx'
                inputspath = sc.makefilepath(filename=template_name, folder=settings.ONpath('applications'))
            self.load_data(inputspath=inputspath, defaultspath=defaultspath, fromfile=True, makemodel=False)

        ## Define other quantities
        self.name     = name
        self.uid      = sc.uuid()
        self.created  = sc.now()
        self.modified = sc.now()
        self.version  = version
        self.gitinfo  = sc.gitinfo(__file__)
        self.filename = None # File path, only present if self.save() is used

        return None

    def __repr__(self):
        ''' Print out useful information when called '''
        output = sc.objrepr(self)
        output += '      Project name: %s\n'    % self.name
        output += '\n'
        output += '          Datasets: %i\n'    % len(self.datasets)
        output += '            Models: %i\n'    % len(self.models)
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
        return output
    
    def getinfo(self):
        ''' Return an odict with basic information about the project'''
        info = sc.odict()
        attrs = ['name', 'version', 'created', 'modified', 'gitbranch', 'gitversion', 'uid']
        for attr in attrs:
            info[attr] = getattr(self, attr) # Populate the dictionary
        return info
    
    def load_inputs(self, inputspath=None, country=None, region=None):
        ''' Reload the input spreadsheet into the project '''
        if inputspath is None: inputspath = settings.data_path(country, region)
        self.input_sheet    = sc.Spreadsheet(filename=inputspath)
        return self.input_sheet
    
    def load_defaults(self, defaultspath=None):
        ''' Reload the defaults spreadsheet into the project '''
        if defaultspath is None: defaultspath = settings.default_params_path()
        self.defaults_sheet = sc.Spreadsheet(filename=defaultspath)
        return self.defaults_sheet
        
    def load_data(self, country=None, region=None, name=None, inputspath=None, defaultspath=None, overwrite=False, fromfile=True, makemodel=True):
        '''Load the data, which can mean one of two things: read in the spreadsheets, and/or use these data to make a model '''
        
        # Optionally (but almost always) reload the spreadsheets from file
        if fromfile:
            if inputspath or country or not self.input_sheet:
                self.load_inputs(inputspath=inputspath, country=country, region=region)
            if defaultspath or not self.defaults_sheet:
                self.load_defaults(defaultspath=defaultspath)
        
        # Optionally (but almost always) use these to make a model (do not do if blank sheets)
        if makemodel:
            dataset = Dataset(country=country, region=region, name=name, fromfile=False, doload=True, project=self)
            if name is None: name = sc.uniquename(dataset.name, self.datasets.keys())
            self.datasets[name] = dataset
            self.add_model(name, overwrite=overwrite) # add model associated with the dataset
        
        return None

    def save(self, filename=None, folder=None, saveresults=False, verbose=0):
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

    def write_results(self, filename=None, folder=None, keys=None):
        outcomes = default_trackers()
        labs = pretty_labels()
        headers = [labs[out] for out in outcomes]
        if keys is None: keys = self.results.keys()
        keys = sc.promotetolist(keys)
        if filename is None: filename = 'outputs.xlsx'
        filepath = sc.makefilepath(filename=filename, folder=folder, ext='xlsx', default='%s outputs.xlsx' % self.name)
        outputs = []
        for key in keys:
            reslist = self.result(key)
            reslist = sc.promotetolist(reslist)
            for res in reslist:
                out = list(res.get_outputs(outcomes, seq=False, pretty=True))
                outputs.append([res.name] + out) # gets all outputs
        data = [['Result name'] + headers] + outputs
        
        # Formatting
        formats = {
            'header':{'bold':True, 'bg_color':'#3c7d3e', 'color':'#ffffff'},
            'plain': {},
            'bold':   {'bold':True}}
        nrows = len(data)
        ncols = len(data[0])
        formatdata = np.zeros((nrows, ncols), dtype=object)
        formatdata[:,:] = 'plain' # Format data as plain
        formatdata[:,0] = 'bold' # Left side bold
        formatdata[0,:] = 'header' # Top with green header
        sc.savespreadsheet(filename=filename, data=data, formats=formats, formatdata=formatdata)
        return filepath

    def add(self, name, item, what=None):
        """ Add an entry to a structure list """
        structlist = self.getwhat(what=what)
        structlist[name] = item
        print('Item "{}" added to "{}"'.format(name, what))
        self.modified = sc.now()

    def remove(self, what, name=None):
        structlist = self.getwhat(what=what)
        if name is None: # remove all
            structlist.clear()
            name = 'all'
        else:
            structlist.pop(name)
        print('{} "{}" removed'.format(what, name))
        self.modified = sc.now()

    def getwhat(self, what):
        '''
        Return the requested item ('what')
            structlist = getwhat('parameters')
        will return P.parset.
        '''
        if what in ['d', 'ds', 'dataset', 'datasets']: structlist = self.datasets
        elif what in ['m', 'mod', 'model', 'models']: structlist = self.models
        elif what in ['s', 'scen', 'scens', 'scenario', 'scenarios']: structlist = self.scens
        elif what in ['o', 'opt', 'opts', 'optim', 'optims', 'optimization', 'optimization', 'optimizations', 'optimizations']: structlist = self.optims
        elif what in ['r', 'res', 'result', 'results']: structlist = self.results
        else: raise settings.ONException("Item not found")
        return structlist

    #######################################################################################################
    ### Utilities
    #######################################################################################################

    def dataset(self, key=None, verbose=2):
        ''' Shortcut for getting the latest model, i.e. self.datasets[-1] '''
        if key is None: key = -1
        try:    return self.datasets[key]
        except: return sc.printv('Warning, dataset "%s" set not found!' %key, 1, verbose) # Returns None
        
    def model(self, key=None, verbose=2):
        ''' Shortcut for getting the latest model, i.e. self.datasets[-1] '''
        if key is None: key = -1
        try:    return self.models[key]
        except: return sc.printv('Warning, model "%s" set not found!' %key, 1, verbose) # Returns None
    
    def scen(self, key=None, verbose=2):
        ''' Shortcut for getting the latest scenario, i.e. self.scen[-1] '''
        if key is None: key = -1
        try:    return self.scens[key]
        except: return sc.printv('Warning, scenario "%s" not found!' %key, 1, verbose) # Returns None
    
    def optim(self, key=None, verbose=2):
        ''' Shortcut for getting the latest optim, i.e. self.scen[-1] '''
        if key is None: key = -1
        try:    return self.optims[key]
        except: return sc.printv('Warning, optimization "%s" not found!' %key, 1, verbose) # Returns None
    
    def result(self, key=None, verbose=2):
        ''' Shortcut for getting the latest result, i.e. self.results[-1] '''
        if key is None: key = -1
        try:    return self.results[key]
        except: return sc.printv('Warning, result "%s" not found!' %key, 1, verbose) # Returns None
    
    def cleanresults(self):
        ''' Remove all results '''
        for key,result in self.results.items():
            self.results.pop(key)
        
    def add_scen(self, json=None):
        ''' Super roundabout way to add a scenario '''
        scens = [Scen(**json)]
        self.add_scens(scens)
        return None

    def add_optim(self, json=None):
        ''' Super roundabout way to add a scenario '''
        optims = [Optim(**json)]
        self.add_optims(optims)
        return None

    def add_model(self, name=None, overwrite=True):
        """ Adds a model to the self.models odict.
        A new model should only be instantiated if new input data is uploaded to the Project.
        For the same input data, one model instance is used for all scenarios.
        :param name:
        :param pops:
        :param prog_info:
        :param overwrite:
        :return:
        """
        dataset = self.dataset(name)
        pops = dataset.pops
        prog_info = dataset.prog_info
        t = dataset.t
        if overwrite: self.models = sc.odict()
        model = Model(pops, prog_info, t)
        self.add(name=name, item=model, what='model')
        # get default scenarios
        defaults = get_defaults(name, model)
        self.add_scens(defaults)
        self.modified = sc.now()

    def add_scens(self, scens, overwrite=False):
        """ Adds scenarios to the Project's self.scens odict.
        Scenarios point to a corresponding model, accessed by key in self.models.
        Not all model parameters initialized until model.setup() is called.
        :param scens: a list of Scen objects, but individual Scen object will be listified.
        :param overwrite: boolean, True removes all previous scenarios.
        :return: None
        """
        if overwrite: self.scens = sc.odict()
        scens = sc.promotetolist(scens)
        for scen in scens:
            self.add(name=scen.name, item=scen, what='scen')
        self.modified = sc.now()

    def run_baseline(self, model_name, prog_set, dorun=True):
        model = sc.dcp(self.model(model_name))
        progvals = sc.odict({prog: [] for prog in prog_set})
        base = Scen(name='Baseline', model_name=model_name, scen_type='coverage', progvals=progvals)
        if dorun:
            return run_scen(base, model)
        else:
            return base

    def add_optims(self, optims, overwrite=False):
        if overwrite: self.optims = sc.odict() # remove exist scenarios
        optims = sc.promotetolist(optims)
        for optim in optims:
            self.add(name=optim.name, item=optim, what='optim')
        self.modified = sc.now()

    def add_result(self, result, name=None):
        """Add result by name"""
        if name is None:
            try:
                name = result.name
            except Exception as E:
                print('WARNING, could not extract result name: %s' % repr(E))
                name = 'default_result'
        self.add(name=name, item=result, what='result')

    def demo_scens(self, dorun=None, doadd=True):
        scens = demo_scens()
        if doadd:
            self.add_scens(scens)
            if dorun:
                self.run_scens()
            return None
        else:
            return scens

    def demo_optims(self, dorun=False, doadd=True):
        optims = demo_optims()
        if doadd:
            self.add_optims(optims)
            if dorun:
                self.run_optim()
            return None
        else:
            return optims

    def run_scens(self, scens=None):
        """Function for running scenarios
        If scens is specified, they are added to self.scens """
        results = []
        if scens is not None: self.add_scens(scens)
        for scen in self.scens.itervalues():
            if scen.active:
                model = self.model(scen.model_name)
                res = run_scen(scen, model)
                results.append(res)
        self.add_result(results, name='scens')
        return None

    def run_optim(self, optim=None, key=-1, maxiter=15, swarmsize=20, maxtime=140, parallel=True, dosave=True, runbaseline=True):
        if optim is not None:
            self.add_optims(optim)
            key = optim.name # this to handle parallel calls of this function
        optim = self.optim(key)
        results = []
        # run baseline
        if runbaseline:
            base = self.run_baseline(optim.model_name, optim.prog_set)
            results.append(base)
        # run optimization
        model = sc.dcp(self.model(optim.model_name))
        model.setup(optim, setcovs=False)
        model.get_allocs(optim.add_funds, optim.fix_curr, optim.rem_curr)
        results += optim.run_optim(model, maxiter=maxiter, swarmsize=swarmsize, maxtime=maxtime, parallel=parallel)
        # add by optim name
        if dosave: self.add_result(results, name=optim.name)
        return results

    @trace_exception
    def run_geospatial(self, geo=None, maxiter=30, swarmsize=25, maxtime=20, dosave=True):
        """ Regions cannot be parallelised because daemon processes cannot have children.
        Two options: Either can parallelize regions and not the budget or run
        regions in series while parallelising each budget multiple. """
        regions = geo.make_regions()
        run_optim = partial(self.run_optim, key=-1, maxiter=maxiter, swarmsize=swarmsize, maxtime=maxtime,
                            parallel=True, dosave=True, runbaseline=False)
        optimized = sc.odict(sc.odict({region.name: run_optim(optim=region) for region in regions}))
        regional_allocs = geo.gridsearch(optimized)
        # now optimize these allocations within each region
        regions = geo.make_regions(add_funds=regional_allocs, mults=[1])
        run_optim = partial(self.run_optim, key=-1, maxiter=maxiter, swarmsize=swarmsize, maxtime=maxtime,
                            parallel=False, dosave=True, runbaseline=False)
        # can run in parallel b/c child processes in series
        results = run_parallel(run_optim, regions, num_procs=len(regions))
        # flatten list
        results = [item for sublist in results for item in sublist]
        # remove multiple to plot by name (total hack)
        for res in results:
            res.mult = None
            res.name = res.name.replace('(x1)', '')
        if dosave: self.add_result(results, name='geospatial')
        return results

    def get_output(self, outcomes=None):
        results = self.result(-1)
        if not outcomes: outcomes = default_trackers()
        outcomes = sc.promotetolist(outcomes)
        outputs = []
        for i, res in enumerate(results):
            outputs.append(res.get_outputs(outcomes, seq=False))
        return outputs

    def sensitivity(self):
        print('Not implemented')

    @trace_exception
    def plot(self, key=-1, toplot=None, optim=False, geo=False):
        figs = make_plots(self.result(key), toplot=toplot, optim=optim, geo=geo)
        return figs

    def get_costeff(self, resultname=None):
        """ 
        Returns a nested odict with keys (scenario/optim name, child name, pretty outcome) 
        and value (output). Output is type string. Will work for both scenarios and optimizations, 
        using whatever results were last generated
        """
        if resultname is None: resultname = 'scens'
        results = self.result(resultname)       
        costeff = get_costeff(self, results)
        return costeff

def demo(scens=False, optims=False):
    """ Create a demo project with demo settings """
    
    # Parameters
    name = 'Demo project'
    country = 'demo'
    region = 'demo'
    
    # Create project and data
    P = Project(name)
    P.load_data(country, region, name='demo')

    # Create scenarios and optimizations
    if scens:
        P.demo_scens()
    if optims:
        P.demo_optims()
    return P