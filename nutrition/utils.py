import os, functools, traceback, scipy.special, multiprocessing, numbers, copy, collections
import numpy as np
import sciris.core as sc
from scipy.optimize import brentq


def optimafolder(subfolder=None):
    if subfolder is None: subfolder='nutrition'
    parentfolder = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    folder = os.path.join(parentfolder, subfolder, '')
    return folder

############
# ODICT
#########

def today(timezone='utc', die=False):
    ''' Get the current time, in UTC time '''
    import datetime # today = datetime.today
    try:
        import dateutil
        if timezone=='utc':                           tzinfo = dateutil.tz.tzutc()
        elif timezone is None or timezone=='current': tzinfo = None
        else:                                         raise Exception('Timezone "%s" not understood' % timezone)
    except:
        errormsg = 'Timezone information not available'
        if die: raise Exception(errormsg)
        tzinfo = None
    now = datetime.datetime.now(tzinfo)
    return now

class odict(collections.OrderedDict):
    def __init__(self, *args, **kwargs):
        ''' See collections.py '''
        if len(args)==1 and args[0] is None: args = [] # Remove a None argument
        collections.OrderedDict.__init__(self, *args, **kwargs) # Standard init
        return None



    def append(self, key=None, value=None):
        """ Support an append method, like a list """
        needkey = False
        if value is None: # Assume called with a single argument
            value = key
            needkey = True
        if key is None or needkey:
            keyname = 'key'+flexstr(len(self))  # Define the key just to be the current index
        else:
            keyname = key
        self.__setitem__(keyname, value)

    def __setitem__(self, key, value):
        """ Allows setitem to support strings, integers, slices, lists, or arrays """
        if isinstance(key, (str, tuple)):
            collections.OrderedDict.__setitem__(self, key, value)
        elif isinstance(key, numbers.Number):  # Convert automatically from float...dangerous?
            thiskey = self.keys()[int(key)]
            collections.OrderedDict.__setitem__(self, thiskey, value)
        elif type(key) == slice:
            startind = self.__slicekey(key.start, 'start')
            stopind = self.__slicekey(key.stop, 'stop')
            if stopind < startind:
                errormsg = 'Stop index must be >= start index (start=%i, stop=%i)' % (startind, stopind)
                raise Exception(errormsg)
            slicerange = range(startind, stopind)
            enumerator = enumerate(slicerange)
            slicelen = len(slicerange)
            if hasattr(value, '__len__'):
                if len(value) == slicelen:
                    for valind, index in enumerator:
                        self.__setitem__(index, value[valind])  # e.g. odict[:] = arr[:]
                else:
                    errormsg = 'Slice "%s" and values "%s" have different lengths! (%i, %i)' % (
                        slicerange, value, slicelen, len(value))
                    raise Exception(errormsg)
            else:
                for valind, index in enumerator:
                    self.__setitem__(index, value)  # e.g. odict[:] = 4
        elif self.__is_odict_iterable(key) and hasattr(value, '__len__'):  # Iterate over items
            if len(key) == len(value):
                for valind, thiskey in enumerate(key):
                    self.__setitem__(thiskey, value[valind])
            else:
                errormsg = 'Keys "%s" and values "%s" have different lengths! (%i, %i)' % (
                    key, value, len(key), len(value))
                raise Exception(errormsg)
        else:
            collections.OrderedDict.__setitem__(self, key, value)

    def __slicekey(self, key, slice_end):
        shift = int(slice_end=='stop')
        if isinstance(key, numbers.Number): return key
        elif type(key) is str: return self.index(key)+shift # +1 since otherwise confusing with names (CK)
        elif key is None: return len(self) if shift else 0
        else: raise Exception('To use a slice, %s must be either int or str (%s)' % (slice_end, key))

    def __is_odict_iterable(self, key):
        """ Check to see whether the "key" is actually an iterable """
        output = type(key)==list or type(key)==type(np.array([])) # Do *not* include dict, since that would be recursive
        return output

# ##############################################################################
# ### HELPER FUNCTIONS
# ##############################################################################
#

def default_trackers():
    output = [
        'stunting_prev',
        'wasting_prev',
        'anaemia_prev',
        'child_deaths',
        'pw_deaths',
        'thrive']
    return output

def read_sheet(spreadsheet, name, cols=None, dict_orient=None, skiprows=None, to_odict=False):
    df = spreadsheet.parse(name, index_col=cols, skiprows=skiprows).dropna(how='all')
    if dict_orient:
        df = df.to_dict(dict_orient)
    elif to_odict:
        df = df.to_dict(into=sc.odict)
    return df

def scale_alloc(free, allocation):
    new = np.sum(allocation)
    if new == 0:
        scaled_alloc = allocation.copy()
    else:
        scale = free / new
        scaled_alloc = allocation * scale
    return scaled_alloc

def add_fixed_alloc(fixed, alloc, indxList):
    """Assumes order is preserved from original list"""
    total_allocs = np.concatenate(([fixed[indxList]], [alloc]), axis=0)
    total_allocs = np.sum(total_allocs, axis=0)
    return total_allocs

def get_obj_sign(obj):
    max_obj = ['thrive_notanaemic', 'thrive', 'thrive2', 'healthy_children', 'nonstunted_nonwasted', 'not_anaemic',
                  'not_anaemic2', 'no_conditions']
    if obj in max_obj:
        return -1
    else:
        return 1

def trace_exception(func):
    """
    Allows stacktrace in processes.

    HOW TO USE: Decorate any function you wish to call with runParallel (the function func
    references) with '@trace_exception'. Whenever an exception is thrown by the decorated function when executed
    parallel, a stacktrace is printed; the thread terminates but the execution of other threads is not affected.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            traceback.print_exc()
    return wrapper

def run_parallel(func, args_list, num_procs):
    """ Uses pool.map() to distribute parallel processes.
    args_list: an iterable of args (also iterable)
    func: function to parallelise, must have single explicit argument (i.e an iterable) """

    p = multiprocessing.Pool(processes=num_procs)
    res = p.map(func, args_list)
    return res

def get_new_prob(coverage, probCovered, probNotCovered):
    return coverage * probCovered + (1.-coverage) * probNotCovered

def get_change(old, new):
    if abs(old-new) < 1e-3:
        return 0
    else:
        return (new - old)/old

def solve_quad(oddsRatio, fracA, fracB):
    # solves quadratic to calculate probabilities where e.g.:
    # fracA is fraction covered by intervention
    # fracB is fraction of pop. in a particular risk status
    A = (1. - fracA) * (1. - oddsRatio)
    B = (oddsRatio - 1) * fracB - oddsRatio * fracA - (1. - fracA)
    C = fracB
    f = lambda x,a,b,c: a*x**2 + b*x + c
    p0 = brentq(f, 0, 1, args=(A,B,C))
    p1 = p0 * oddsRatio / (1. - p0 + oddsRatio * p0)
    return p0, p1

def restratify(frac_yes):
    # Going from binary stunting/wasting to four fractions
    # Yes refers to more than 2 standard deviations below the global mean/median
    # in our notes, frac_yes = alpha
    if frac_yes > 1:
        frac_yes = 1
    invCDFalpha = scipy.special.ndtri(frac_yes)
    frac_high = scipy.special.ndtr(invCDFalpha - 1.)
    frac_mod = frac_yes - scipy.special.ndtr(invCDFalpha - 1.)
    frac_mild = scipy.special.ndtr(invCDFalpha + 1.) - frac_yes
    frac_norm = 1. - scipy.special.ndtr(invCDFalpha + 1.)
    restrat = {'Normal':frac_norm, 'Mild': frac_mild,
               'Moderate': frac_mod, 'High':frac_high}
    return restrat

def fit_poly(group_idx, trend):
    """ Calculates the trend over time in prevalence, mortality """
    prev = np.array(trend[group_idx])
    notNan = np.isfinite(prev)
    if sum(notNan) <= 1:  # static data
        return 1
    else:
        linReg = np.polyfit(range(len(prev[notNan])), prev[notNan], 1)
        return 1 + linReg[0]

def system(odds, bo, p0, x):
    x0 = x[0]
    f1 = odds[1]*x0 / (1 - x0  + odds[1]*x0 ) - x[1]
    f2 = odds[2]*x0 / (1 - x[0] + odds[2]*x0) - x[2]
    f3 = odds[3]*x0 / (1 - x0 + odds[3]*x0) - x[3]
    f4 = sum(frac * x for frac, x in zip(bo, x)) - p0
    return [f1, f2, f3, f4]

def check_sol(sol):
    try:
        ((sol > 0) & (sol < 1)).all()
    except:
        raise Exception(':: Error:: birth outcome probabilities outside interval (0,1)')

# ##############################################################################
# ### TYPE FUNCTIONS
# ##############################################################################
#
def flexstr(arg):
    ''' Try converting to a regular string, but try unicode if it fails '''
    try:
        output = str(arg)
    except:
        output = unicode(arg)
    return output