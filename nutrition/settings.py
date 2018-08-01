import os
import itertools
import sciris.core as sc
from .version import version

class Settings(object):
    """ Store all the statis data for a project that won't change except between Optima versions
    WARNING: Do not change the order of these lists without checking the potential consequences within the code """
    def __init__(self):
        self.t = [2017, 2025]
        self.years = sc.inclusiverange(self.t[0], self.t[1])
        self.n_years = len(self.years)
        self.timestep = 1./12. # in months
        self.stunting_list = ['High', 'Moderate', 'Mild', 'Normal']
        self.stunted_list = self.stunting_list[:2]
        self.non_stunted_list = self.stunting_list[2:]
        self.anaemia_list = ['Anaemic', 'Not anaemic']
        self.anaemic_list = self.anaemia_list[:1]
        self.non_anaemic_list = self.anaemia_list[1:]
        self.wasting_list = ['SAM', 'MAM', 'Mild', 'Normal']
        self.wasted_list = self.wasting_list[:2]
        self.non_wasted_list = self.wasting_list[2:]
        self.bf_list = ['Exclusive', 'Predominant', 'Partial', 'None']
        list_cats = [self.stunting_list, self.wasting_list, self.anaemia_list, self.bf_list]
        self.all_cats = list(itertools.product(*list_cats))
        self.n_cats = len(self.all_cats)
        self.correct_bf = {'<1 month': 'Exclusive', '1-5 months': 'Exclusive', '6-11 months':'Partial',
                           '12-23 months': 'Partial', '24-59 months': 'None'}
        self.optimal_space = '24 months or greater'
        self.birth_outcomes = ['Term AGA', 'Term SGA', 'Pre-term AGA','Pre-term SGA']
        self.all_risks = [self.stunting_list, self.wasting_list, self.bf_list, self.anaemia_list]
        self.child_ages = ['<1 month', '1-5 months', '6-11 months', '12-23 months', '24-59 months']
        self.pw_ages = ['PW: 15-19 years', 'PW: 20-29 years', 'PW: 30-39 years', 'PW: 40-49 years']
        self.wra_ages = ['WRA: 15-19 years', 'WRA: 20-29 years', 'WRA: 30-39 years', 'WRA: 40-49 years']
        self.all_ages = self.child_ages + self.pw_ages + self.wra_ages
        self.risks = ['Stunting', 'Wasting', 'Breastfeeding', 'Anaemia'] # todo: even use this?
        self.child_age_spans = [1., 5., 6., 12., 36.] # in months
        self.women_age_rates = [1./5., 1./10., 1./10., 1./10.] # in years
    
    def __repr__(self):
        output  = sc.desc(self)
        return output

def data_path(country, region, sim_type):
    parentfolder = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    demoname = '{}_input.xlsx'.format(region)
    subdir = os.path.join('applications', country, 'data', sim_type, demoname)
    demopath = os.path.join(parentfolder, subdir)
    return demopath

def default_params_path():
    parentfolder = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    filename = 'default_params.xlsx'
    childpath = os.path.join('nutrition', filename)
    filepath = os.path.join(parentfolder, childpath)
    return filepath



#####################################################################################################################
### Define debugging and exception functions/classes
#####################################################################################################################

# Tool path
def ONpath(subdir=None, trailingsep=True):
    ''' Returns the parent path of the Optima Nutrition module. If subdir is not None, include it in the path '''
    import os
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    if subdir is not None:
        tojoin = [path, subdir]
        if trailingsep: tojoin.append('') # This ensures it ends with a separator
        path = os.path.join(*tojoin) # e.g. ['/home/optima', 'tests', '']
    return path


# Debugging information
def debuginfo(output=False):
    import sciris.core as sc
    outstr = '\nOptima Nutrition debugging info:\n'
    outstr += '   Version: %s\n' % version
    outstr += '   Branch:  %s\n' % sc.gitinfo()['branch']
    outstr += '   SHA:     %s\n' % sc.gitinfo()['hash']
    outstr += '   Date:    %s\n' % sc.gitinfo()['date']
    outstr += '   Path:    %s\n' % ONpath()
    if output:
        return outstr
    else: 
        print(outstr)
        return None

class ONException(Exception):
    ''' A tiny class to allow for Optima-specific exceptions -- define this here to allow for Optima-specific info '''
    
    def __init__(self, errormsg, *args, **kwargs):
        if isinstance(errormsg, basestring): errormsg = errormsg+debuginfo(output=True) # If it's not a string, not sure what it is, but don't bother with this
        Exception.__init__(self, errormsg, *args, **kwargs)