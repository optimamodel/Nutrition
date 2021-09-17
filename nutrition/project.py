#######################################################################################################
#%% Imports
#######################################################################################################

import os
import sciris as sc
from .version import version
from .utils import default_trackers, add_dummy_prog_data
from .data import Dataset
from .model import Model
from .scenarios import Scen, run_scen, convert_scen, make_default_scen
from .optimization import Optim
from .geospatial import Geospatial
from .results import write_to_excel
from .plotting import make_plots, get_costeff, plot_costcurve
from .demo import demo_scens, demo_optims, demo_geos
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

    Version: 2018oct02
    """



    #######################################################################################################
    ### Built-in methods -- initialization, and the thing to print if you call a project
    #######################################################################################################

    def __init__(self, name='default', loadsheets=True, inputspath=None, defaultspath=None):
        ''' Initialize the project '''

        ## Define the structure sets
        self.datasets     = sc.odict()
        self.models       = sc.odict()
        self.scens        = sc.odict()
        self.optims       = sc.odict()
        self.geos         = sc.odict()
        self.results      = sc.odict()
        self.spreadsheets = sc.odict()
        if loadsheets:
            if not inputspath:
                template_name = 'template_input.xlsx'
                inputspath = sc.makefilepath(filename=template_name, folder=settings.ONpath('inputs'))
                self.templateinput = sc.Spreadsheet(filename=inputspath)
            else:
                self.load_data(inputspath=inputspath, defaultspath=defaultspath, fromfile=True)

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
        output += '        Geospatial: %i\n'    % len(self.geos)
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
    
    
    @staticmethod
    def _sanitizename(name=None, country=None, region=None, inputspath=None):
        ''' Get the most valid name '''
        if name is None:
            try:    
                name = country+'_'+region
            except: 
                if inputspath is not None:
                    name = os.path.basename(inputspath)
                    if name.endswith('.xlsx'):
                        name = name[:-5]
                else:
                    name = 'Default'
        return name
    
    
    def storeinputs(self, inputspath=None, country=None, region=None, name=None):
        ''' Reload the input spreadsheet into the project '''
        if inputspath is None:
            inputspath = settings.data_path(country, region)
        name = self._sanitizename(name, country, region, inputspath)
        self.spreadsheets[name] = sc.Spreadsheet(filename=inputspath)
        return self.inputsheet(name)
    
        
    def load_data(self, country=None, region=None, name=None, inputspath=None, defaultspath=None, fromfile=True, validate=True):
        '''Load the data, which can mean one of two things: read in the spreadsheets, and/or use these data to make a model '''
        
        # Generate name odict key for Spreadsheet, Dataset, and Model odicts.
        name = self._sanitizename(name, country, region, inputspath)
        if fromfile:
            name = sc.uniquename(name, self.datasets.keys())
        
        # Optionally (but almost always) reload the spreadsheets from file.
        if fromfile:
            if inputspath or country or not self.inputsheet:
                self.storeinputs(inputspath=inputspath, country=country, region=region, name=name)
        
        # Optionally (but almost always) use these to make a model (do not do if blank sheets).
        dataset = Dataset(country=country, region=region, name=name, fromfile=False, doload=True, project=self)
        self.datasets[name] = dataset
        dataset.name = name
        self.add_model(name) # add model associated with the dataset
    
        # Do validation to insure that Dataset and Model objects are loaded in for each of the spreadsheets that are
        # in the project.
        if validate:
            missingdatasets = list(set(self.spreadsheets.keys()) - set(self.datasets.keys()))
            missingmodels =   list(set(self.spreadsheets.keys()) - set(self.models.keys()))
            missingsets = list(set(missingdatasets+missingmodels))
            if len(missingsets):
                print('Warning: the following datasets/models are missing and are being regenerated: %s' % missingdatasets)
                for key in missingsets:
                    self.load_data(name=key, fromfile=False, validate=False)
        
        return None

    def add_data(self, data=None):
        """ Add a new dataset object to Project """
        if data is None:
            self.load_data()
        else:
            try:
                name = data.name
                self.datasets[name] = data
                self.add_model(name)
            except:
                raise Exception("No name for data object")

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

    def write_results(self, filename=None, folder=None, key=None):
        """ Blargh, this really needs some tidying """
        if key is None:
            key = -1
        results = self.result(key)
        write_to_excel(results, projname=self.name, filename=filename, folder=folder)
        return

    def add(self, name, item, what=None):
        """ Add an entry to a structure list, overwriting with abandon """
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
        if what in ['d', 'ds', 'dataset', 'datasets']:
            structlist = self.datasets
        elif what in ['m', 'mod', 'model', 'models']:
            structlist = self.models
        elif what in ['s', 'scen', 'scens', 'scenario', 'scenarios']:
            structlist = self.scens
        elif what in ['o', 'opt', 'opts', 'optim', 'optims', 'optimization', 'optimizations']:
            structlist = self.optims
        elif what in ['g', 'geo', 'geos', 'geospatial']:
            structlist = self.geos
        elif what in ['r', 'res', 'result', 'results']:
            structlist = self.results
        else:
            raise settings.ONException("Item not found")
        return structlist

    #######################################################################################################
    ### Utilities
    #######################################################################################################

    def inputsheet(self, key=None, verbose=2):
        if key is None:
            key = -1
        try:
            return self.spreadsheets[key]
        except:
            return sc.printv('Warning, input sheet "%s" set not found!' %key, 1, verbose)

    def dataset(self, key=None, verbose=2):
        ''' Shortcut for getting the latest model, i.e. self.datasets[-1] '''
        if key is None:
            key = -1
        try:
            return self.datasets[key]
        except:
            return sc.printv('Warning, dataset "%s" set not found!' %key, 1, verbose) # Returns None
        
    def model(self, key=None, verbose=2):
        ''' Shortcut for getting the latest model, i.e. self.datasets[-1] '''
        if key is None:
            key = -1
        try:
            return self.models[key]
        except:
            return sc.printv('Warning, model "%s" set not found!' %key, 1, verbose) # Returns None
    
    def scen(self, key=None, verbose=2):
        ''' Shortcut for getting the latest scenario, i.e. self.scen[-1] '''
        if key is None:
            key = -1
        try:
            return self.scens[key]
        except:
            return sc.printv('Warning, scenario "%s" not found!' %key, 1, verbose) # Returns None
    
    def optim(self, key=None, verbose=2):
        ''' Shortcut for getting the latest optim, i.e. self.optims[-1] '''
        if key is None:
            key = -1
        try:
            return self.optims[key]
        except:
            return sc.printv('Warning, optimization "%s" not found!' %key, 1, verbose) # Returns None
    
    def geo(self, key=None, verbose=2):
        ''' Shortcut for getting the latest geo, i.e. self.geos[-1] '''
        if key is None:
            key = -1
        try:
            return self.geos[key]
        except:
            return sc.printv('Warning, geospatial analysis "%s" not found!' %key, 1, verbose) # Returns None
    
    def result(self, key=None, verbose=2):
        ''' Shortcut for getting the latest result, i.e. self.results[-1] '''
        if key is None:
            key = -1
        try:
            return self.results[key]
        except:
            return sc.printv('Warning, result "%s" not found!' %key, 1, verbose) # Returns None
    
    def cleanresults(self):
        ''' Remove all results '''
        for key,result in self.results.items():
            self.results.pop(key)
        
    def add_scen(self, json=None):
        ''' Super roundabout way to add a scenario '''
        scens = [Scen(**json)]
        self.add_scens(scens)
        return scens

    def add_optim(self, json=None):
        ''' Super roundabout way to add an optimization '''
        optims = [Optim(**json)]
        self.add_optims(optims)
        return optims
    
    def add_geo(self, json=None):
        ''' Super roundabout way to add a geospatial optimization '''
        geos = [Geospatial(**json)]
        self.add_geos(geos)
        return geos

    def add_model(self, name=None):
        """ Adds a model to the self.models odict.
        A new model should only be instantiated if new input data is uploaded to the Project.
        For the same input data, one model instance is used for all scenarios.
        """
        dataset = self.dataset(name)
        pops = dataset.pops
        prog_info = dataset.prog_info
        t = dataset.t
        model = Model(pops, prog_info, t)
        self.add(name=name, item=model, what='model')
        # Loop over all Scens and create a new default scenario for any that depend on the dataset which has been reloaded.
        # for scen_name in self.scens.keys():  # Loop over all Scen keys in the project
        #     if self.scens[scen_name].model_name == name:
        #         defaults = make_default_scen(name, model, self.scens[scen_name].scen_type, scen_name)
        #         self.add_scens(defaults)
        # Only, if there is no 'Baseline' scenario, make a default baseline scenario.
        basename = 'Baseline'
        if basename not in self.scens.keys():
            defaults = make_default_scen(name, model, 'coverage', basename)
            self.add_scens(defaults)
        self.modified = sc.now()
        return model

    def add_scens(self, scens, overwrite=False):
        """ Adds scenarios to the Project's self.scens odict.
        Scenarios point to a corresponding model, accessed by key in self.models.
        Not all model parameters initialized until model.setup() is called.
        :param scens: a list of Scen objects, but individual Scen object will be listified.
        :param overwrite: boolean, True removes all previous scenarios.
        :return: None
        """
        if overwrite:
            self.scens = sc.odict()
        scens = sc.promotetolist(scens)
        for scen in scens:
            self.add(name=scen.name, item=scen, what='scen')
        self.modified = sc.now()
        return scens

    def convert_scen(self, key=-1):
        """ Converts one scenario type to another.
        Retains the original and adds the converted scenario in the project.
         :param key: the key of the scen to convert"""
        scen = self.scen(key=key)
        model = self.model(scen.model_name)
        converted = convert_scen(scen, model)
        self.add_scens(converted)
        return

    def run_baseline(self, model_name, prog_set, dorun=True):
        model = sc.dcp(self.model(model_name))
        progvals = sc.odict({prog: [] for prog in prog_set})
        if 'Excess budget not allocated' in prog_set:
            excess_spend = {'name': 'Excess budget not allocated',
                            'all_years': model.prog_info.all_years,
                            'prog_data': add_dummy_prog_data(model.prog_info, 'Excess budget not allocated')}
            model.prog_info.add_prog(excess_spend, model.pops)
            model.prog_info.prog_data = excess_spend['prog_data']
        base = Scen(name='Baseline', model_name=model_name, scen_type='coverage', progvals=progvals)
        if dorun:
            return run_scen(base, model, multi_run=False)
        else:
            return base

    def add_optims(self, optims, overwrite=False):
        if overwrite:
            self.optims = sc.odict() # remove exist scenarios
        optims = sc.promotetolist(optims)
        for optim in optims:
            self.add(name=optim.name, item=optim, what='optim')
        self.modified = sc.now()
        return optims
    
    def add_geos(self, geos, overwrite=False):
        if overwrite:
            self.geos = sc.odict() # remove exist scenarios
        geos = sc.promotetolist(geos)
        for geo in geos:
            self.add(name=geo.name, item=geo, what='geo')
        self.modified = sc.now()
        return geos

    def add_result(self, result, name=None):
        """Add result by name"""
        if name is None:
            try:
                name = result.name
            except Exception as E:
                print('WARNING, could not extract result name: %s' % repr(E))
                name = 'default_result'
        self.add(name=name, item=result, what='result')
        return result

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
    
    def demo_geos(self, dorun=False, doadd=True):
        geos = demo_geos()
        if doadd:
            self.add_geos(geos)
            if dorun:
                self.run_geo()
            return None
        else:
            return geos

    def run_scens(self, scens=None):
        """Function for running scenarios
        If scens is specified, they are added to self.scens """
        results = []
        if scens is not None:
            self.add_scens(scens)
        for scen in self.scens.values():
            if scen.active:
                if (scen.model_name is None) or (scen.model_name not in self.datasets.keys()):
                    raise Exception('Could not find valid dataset for %s.  Edit the scenario and change the dataset' % scen.name)
                model = self.model(scen.model_name)
                res = run_scen(scen, model)
                results.append(res)
        self.add_result(results, name='scens')
        return None

    def run_optim(self, optim=None, key=-1, maxiter=20, swarmsize=None, maxtime=300, parallel=True, dosave=True, runbaseline=True):
        if optim is not None:
            self.add_optims(optim)
            key = optim.name # this to handle parallel calls of this function
        optim = self.optim(key)
        results = []
        # run baseline
        if runbaseline:
            optim.prog_set.append('Excess budget not allocated')
            base = self.run_baseline(optim.model_name, optim.prog_set)
            results.append(base)
            optim.prog_set.remove('Excess budget not allocated')
        # run optimization
        if (optim.model_name is None) or (optim.model_name not in self.datasets.keys()):
            raise Exception(
                'Could not find valid dataset for %s.  Edit the scenario and change the dataset' % optim.name)
        model = sc.dcp(self.model(optim.model_name))
        model.setup(optim, setcovs=False)
        model.get_allocs(optim.add_funds, optim.fix_curr, optim.rem_curr)
        results += optim.run_optim(model, maxiter=maxiter, swarmsize=swarmsize, maxtime=maxtime, parallel=parallel)
        # add by optim name
        if dosave:
            self.add_result(results, name=optim.name)
        return results

    def run_geo(self, geo=None, key=-1, maxiter=20, swarmsize=None, maxtime=400, dosave=True, parallel=False):
        """ Regions cannot be parallelised because daemon processes cannot have children.
        Two options: Either can parallelize regions and not the budget or run
        regions in series while parallelising each budget multiple. """
        if geo is not None:
            self.add_geos(geo)
            key = geo.name # this to handle parallel calls of this function
        geo = self.geo(key)
        results = geo.run_geo(self, maxiter, swarmsize, maxtime, parallel)
        if dosave:
            self.add_result(results, name='geospatial')
        return results

    def get_output(self, outcomes=None):
        results = self.result(-1)
        if not outcomes:
            outcomes = default_trackers()
        outcomes = sc.promotetolist(outcomes)
        outputs = []
        for i, res in enumerate(results):
            outputs.append(res.get_outputs(outcomes, seq=False))
        return outputs

    def sensitivity(self):
        print('Not implemented')

    def plot(self, key=-1, toplot=None, optim=False, geo=False):
        figs = make_plots(self.result(key), toplot=toplot, optim=optim, geo=geo)
        return figs

    def get_costeff(self, resultname=None):
        """ 
        Returns a nested odict with keys (scenario/optim name, child name, pretty outcome) 
        and value (output). Output is type string. Will work for both scenarios and optimizations, 
        using whatever results were last generated
        """
        if resultname is None:
            resultname = 'scens'
        results = self.result(resultname)       
        costeff = get_costeff(self, results)
        return costeff

    def plot_costcurves(self, key=-1):
        """ For backend diagnostic use only """
        results = self.result(key)
        plot_costcurve(results)
        return



def demo(scens=False, optims=False, geos=False):
    """ Create a demo project with demo settings """
    
    # Parameters
    name = 'Demo project'
    country = 'demo'
    region = 'national'
    
    # Create project and load in demo databook spreadsheet file into 'demo' Spreadsheet, Dataset, and Model.
    P = Project(name)
    P.load_data(country, region, name='demo')
    P.load_data(country, 'region1', name='demoregion1')
    P.load_data(country, 'region2', name='demoregion2')
    P.load_data(country, 'region3', name='demoregion3')

    # Create demo scenarios and optimizations
    if scens:
        P.demo_scens()
    if optims:
        P.demo_optims()
    if geos:
        P.demo_geos()
    return P