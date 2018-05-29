from utils import odict, today
from copy import deepcopy as dcp

class Project(object):
    def __init__(self, country='master', region='master', sim_type='national'):
        if country==region: sim_type='national'

        ## Define the structure sets
        self.popsets = {}
        self.parsets = {}
        self.progsets = {}
        self.scens = {}
        self.optims = {}
        self.results = {}

        ## Read in the data
        self.name = country if sim_type == 'national' else region

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

    def add_result(self, scen):
        """Add result by name"""
        keyname = scen.name
        self.add(name=keyname, item=scen, what='result')
        return

    def run_scens(self, scen_list=None, name=None):
        """Function for running scenarios"""
        if scen_list is not None: self.add_scens(scen_list) # replace existing scen list with new one
        if name is None: name = 'scenarios'
        scens = dcp(self.scens)
        for scen in scens.itervalues():
            scen.run_scen()
            self.add_result(scen=scen)

    def get_results(self, result_key):
        return self.results[result_key]

    def optimise(self):

        return


    def sensitivity(self):
        return

    










