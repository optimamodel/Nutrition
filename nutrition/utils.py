import os, numpy, functools, traceback, scipy.special, multiprocessing, numbers, copy, collections

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
        output = type(key)==list or type(key)==type(numpy.array([])) # Do *not* include dict, since that would be recursive
        return output

########################
### USER OPTIONS STORAGE CLASSES
########################

class Opts(object):
    def __init__(self, name, prog_set, t):
        self.name = name
        self.prog_set = prog_set
        self.t = t

    def get_attr(self):
        return self.__dict__

class ScenOpts(Opts):
    def __init__(self, name, prog_set, t, scen, scen_type):
        Opts.__init__(self, name, prog_set, t)
        self.scen = scen
        self.scen_type = scen_type

class OptimOpts(Opts):
    def __init__(self, name, prog_set, t, mults, fix_curr, add_funds, objs, filter_progs=False):
        Opts.__init__(self, name, prog_set, t)
        # self.optim_type = optim_type
        self.mults = mults
        self.fix_curr = fix_curr
        self.add_funds = add_funds
        self.objs = objs
        self.filter_progs = filter_progs

# ##############################################################################
# ### HELPER FUNCTIONS
# ##############################################################################
#

def scale_alloc(totalBudget, allocation):
    new = sum(allocation)
    if new == 0:
        scaled_alloc = copy.deepcopy(allocation)
    else:
        scaleRatio = totalBudget / new
        scaled_alloc = [x * scaleRatio for x in allocation]
    return scaled_alloc

def add_fixed_alloc(allocations, fixed, indxList):
    """Assumes order is preserved from original list"""
    modified = copy.deepcopy(allocations)
    for i, j in enumerate(indxList):
        modified[j] += fixed[i]
    return modified

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

def solve_quad(oddsRatio, fracA, fracB):
    # solves quadratic to calculate probabilities where e.g.:
    # fracA is fraction covered by intervention
    # fracB is fraction of pop. in a particular risk status
    eps = 1.e-5
    a = (1. - fracA) * (1. - oddsRatio)
    b = (oddsRatio - 1) * fracB - oddsRatio * fracA - (1. - fracA)
    c = fracB
    det = numpy.sqrt(b ** 2 - 4. * a * c)
    if (abs(a) < eps):
        p0 = -c / b
    else:
        soln1 = (-b + det) / (2. * a)
        soln2 = (-b - det) / (2. * a)
        if (soln1 > 0.) and (soln1 < 1.): p0 = soln1
        if (soln2 > 0.) and (soln2 < 1.): p0 = soln2
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
    prev = numpy.array(trend[group_idx])
    notNan = numpy.isfinite(prev)
    if sum(notNan) <= 1:  # static data
        return 1
    else:
        linReg = numpy.polyfit(range(len(prev[notNan])), prev[notNan], 1)
        return 1 + linReg[0]

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