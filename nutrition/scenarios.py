class Scen(object):
    """ Scenario base class -- use only through Parscen or Progscen"""
    def __init__(self, name, parsetname, progsetname, t, active):
        self.name = name
        self.parsetname = parsetname
        self.progsetname = progsetname
        self.t = t
        self.active = active
        self.resultsref = None
        self.scenparset = None

    def get_results(self):
        """ Returns the results"""
        if self.resultsref is not None and self.projectref() is not None: # TODO: ways around projectref?
            results = getresults(project=self.projectref(), pointer=self.resultsref) # TODO: from results.py
            return results
        else:
            print "WARNING, no results associated with this scenario"


# TODO: Looks like any one of these classes defines a separate scenario. For now, implement just the budgetscen and coveragescen, and parscen for later
class Parscen(Scen):
    """ Object for storing a single parameter scenario"""
    def __init__(self, pars, **defaultargs):
        Scen.__init__(self, **defaultargs)
        self.pars = pars

class Progscen(Scen):
    """ Program scenario base class -- don't use indirectly?"""
    def __init__(self, progsetname, **defaultargs):
        Scen.__init__(self, **defaultargs)
        self.progsetname = progsetname # programset

class Budgetscen(Progscen):
    """ Stores a single budget scenario. Initialised with a budget. Coverage added during makescenarios()"""
    def __init__(self, budget, **defaultargs):
        Progscen.__init__(self, **defaultargs)
        self.budget = budget

class Coveragescn(Progscen):
    """ Stores a single coverage scenario. Initialised with a coverage. Budget added during makescenarios()"""
    def __init__(self, coverage, **defaultargs):
        Progscen.__init__(self, **defaultargs)
        self.coverage = coverage



# TODO they have a 'make scenarios' function that does all the work







