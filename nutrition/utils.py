from scipy.special import ndtri, ndtr # these are much faster than calling scipy.stats.norm
from numpy import sqrt, isfinite, polyfit
import os, functools, traceback
from multiprocessing import Pool

def optimafolder(subfolder=None):
    if subfolder is None: subfolder='nutrition'
    parentfolder = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    folder = os.path.join(parentfolder, subfolder, '')
    return folder

############
# ODICT
#########
from collections import OrderedDict
from numpy import array
from numbers import Number
from copy import deepcopy as dcp

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



class odict(OrderedDict):
    def __init__(self, *args, **kwargs):
        ''' See collections.py '''
        if len(args)==1 and args[0] is None: args = [] # Remove a None argument
        OrderedDict.__init__(self, *args, **kwargs) # Standard init
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
            OrderedDict.__setitem__(self, key, value)
        elif isinstance(key, Number):  # Convert automatically from float...dangerous?
            thiskey = self.keys()[int(key)]
            OrderedDict.__setitem__(self, thiskey, value)
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
            OrderedDict.__setitem__(self, key, value)

    def __slicekey(self, key, slice_end):
        shift = int(slice_end=='stop')
        if isinstance(key, Number): return key
        elif type(key) is str: return self.index(key)+shift # +1 since otherwise confusing with names (CK)
        elif key is None: return len(self) if shift else 0
        else: raise Exception('To use a slice, %s must be either int or str (%s)' % (slice_end, key))

    def __is_odict_iterable(self, key):
        """ Check to see whether the "key" is actually an iterable """
        output = type(key)==list or type(key)==type(array([])) # Do *not* include dict, since that would be recursive
        return output


# ##############################################################################
# ### HELPER FUNCTIONS
# ##############################################################################
#

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

    p = Pool(processes=num_procs)
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
    det = sqrt(b ** 2 - 4. * a * c)
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
    invCDFalpha = ndtri(frac_yes)
    frac_high = ndtr(invCDFalpha - 1.)
    frac_mod = frac_yes - ndtr(invCDFalpha - 1.)
    frac_mild = ndtr(invCDFalpha + 1.) - frac_yes
    frac_norm = 1. - ndtr(invCDFalpha + 1.)
    restrat = {'Normal':frac_norm, 'Mild': frac_mild,
               'Moderate': frac_mod, 'High':frac_high}
    return restrat

def fit_poly(group_idx, trend):
    """ Calculates the trend over time in prevalence, mortality """
    prev = array(trend[group_idx])
    notNan = isfinite(prev)
    if sum(notNan) <= 1:  # static data
        return 1
    else:
        linReg = polyfit(range(len(prev[notNan])), prev[notNan], 1)
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

#
# def isiterable(obj):
#     '''
#     Simply determine whether or not the input is iterable, since it's too hard to remember this otherwise.
#     From http://stackoverflow.com/questions/1952464/in-python-how-do-i-determine-if-an-object-is-iterable
#     '''
#     try:
#         iter(obj)
#         return True
#     except:
#         return False
#
#
# def checktype(obj=None, objtype=None, subtype=None, die=False):
#     '''
#     A convenience function for checking instances. If objtype is a type,
#     then this function works exactly like isinstance(). But, it can also
#     be a string, e.g. 'array'.
#
#     If subtype is not None, then checktype will iterate over obj and check
#     recursively that each element matches the subtype.
#
#     Arguments:
#         obj     = the object to check the type of
#         objtype = the type to confirm the object belongs to
#         subtype = optionally check the subtype if the object is iterable
#         die     = whether or not to raise an exception if the object is the wrong type.
#
#     Examples:
#         checktype(rand(10), 'array', 'number') # Returns true
#         checktype(['a','b','c'], 'arraylike') # Returns false
#         checktype([{'a':3}], list, dict) # Returns True
#     '''
#     from numbers import Number
#     from numpy import array
#
#     # Handle "objtype" input
#     if objtype in ['str', 'string']:
#         objinstance = basestring
#     elif objtype in ['num', 'number']:
#         objinstance = Number
#     elif objtype in ['arr', 'array']:
#         objinstance = type(array([]))
#     elif objtype == 'arraylike':
#         objinstance = (list, tuple, type(array([])))  # Anything suitable as a numerical array
#     elif type(objtype) == type:
#         objinstance = objtype  # Don't need to do anything
#     elif objtype is None:
#         return None  # If not supplied, exit
#     else:
#         errormsg = 'Could not understand what type you want to check: should be either a string or a type, not "%s"' % objtype
#         raise Exception(errormsg)
#
#     # Do first-round checking
#     result = isinstance(obj, objinstance)
#
#     # Do second round checking
#     if result and objtype == 'arraylike':  # Special case for handling arrays which may be multi-dimensional
#         obj = promotetoarray(obj).flatten()  # Flatten all elements
#         if subtype is None: subtype = 'number'  # This is the default
#     if isiterable(obj) and subtype is not None:
#         for item in obj:
#             result = result and checktype(item, subtype)
#
#     # Decide what to do with the information thus gleaned
#     if die:  # Either raise an exception or do nothing if die is True
#         if not result:  # It's not an instance
#             errormsg = 'Incorrect type: object is %s, but %s is required' % (type(obj), objtype)
#             raise Exception(errormsg)
#         else:
#             return None  # It's fine, do nothing
#     else:  # Return the result of the comparison
#         return result
#
#
# def isnumber(obj):
#     ''' Simply determine whether or not the input is a number, since it's too hard to remember this otherwise '''
#     return checktype(obj, 'number')
#
#
# def promotetoarray(x):
#     ''' Small function to ensure consistent format for things that should be arrays '''
#     from numpy import ndarray, shape
#     if isnumber(x):
#         return array([x])  # e.g. 3
#     elif isinstance(x, (list, tuple)):
#         return array(x)  # e.g. [3]
#     elif isinstance(x, ndarray):
#         if shape(x):
#             return x  # e.g. array([3])
#         else:
#             return array([x])  # e.g. array(3)
#     else:  # e.g. 'foo'
#         raise Exception("Expecting a number/list/tuple/ndarray; got: %s" % flexstr(x))
#
#
# def promotetolist(obj=None, objtype=None):
#     ''' Make sure object is iterable -- used so functions can handle inputs like 'FSW' or ['FSW', 'MSM'] '''
#     if type(obj) != list:
#         obj = [obj]  # Listify it
#     if objtype is not None:  # Check that the types match -- now that we know it's a list, we can iterate over it
#         for item in obj:
#             checktype(obj=item, objtype=objtype, die=True)
#     if obj is None:
#         raise Exception('This is mathematically impossible')
#     return obj
#
#
# def promotetoodict(obj=None):
#     ''' Like promotetolist, but for odicts -- WARNING, could be made into a method for odicts '''
#     if isinstance(obj, odict):
#         return obj  # Don't need to do anything
#     elif isinstance(obj, dict):
#         return odict(obj)
#     elif isinstance(obj, list):
#         newobj = odict()
#         for i, val in enumerate(obj):
#             newobj['Key %i' % i] = val
#         return newobj
#     else:
#         return odict({'Key': obj})
#
#
# ##############################################################################
# ### ODICT CLASS
# ##############################################################################
#
# from collections import OrderedDict
# from numpy import array
# from numbers import Number
# from copy import deepcopy as dcp
#
#
# class odict(OrderedDict):
#     '''
#     An ordered dictionary, like the OrderedDict class, but supporting list methods like integer
#     referencing, slicing, and appending.
#
#     Version: 2017oct28
#     '''
#
#     def __init__(self, *args, **kwargs):
#         ''' See collections.py '''
#         if len(args) == 1 and args[0] is None: args = []  # Remove a None argument
#         OrderedDict.__init__(self, *args, **kwargs)  # Standard init
#         return None
#
#     def __slicekey(self, key, slice_end):
#         shift = int(slice_end == 'stop')
#         if isinstance(key, Number):
#             return key
#         elif type(key) is str:
#             return self.index(key) + shift  # +1 since otherwise confusing with names (CK)
#         elif key is None:
#             return (len(self) if shift else 0)
#         else:
#             raise Exception('To use a slice, %s must be either int or str (%s)' % (slice_end, key))
#         return None
#
#     def __is_odict_iterable(self, key):
#         ''' Check to see whether the "key" is actually an iterable '''
#         output = type(key) == list or type(key) == type(
#             array([]))  # Do *not* include dict, since that would be recursive
#         return output
#
#     def __sanitize_items(self, items):
#         ''' Try to convert the output of a slice to an array, but give up easily and return a list '''
#         try:
#             output = array(items)  # Try standard Numpy array...
#             if 'S' in str(output.dtype):  # ...but instead of converting to string, convert to object array
#                 output = array(items, dtype=object)
#         except:
#             output = items  # If that fails, just give up and return the list
#         return output
#
#     def __getitem__(self, key):
#         ''' Allows getitem to support strings, integers, slices, lists, or arrays '''
#         if isinstance(key, (str, tuple)):
#             try:
#                 output = OrderedDict.__getitem__(self, key)
#                 return output
#             except Exception as E:  # WARNING, should be KeyError, but this can't print newlines!!!
#                 if len(self.keys()):
#                     errormsg = '%s\nodict key "%s" not found; available keys are:\n%s' % (
#                     repr(E), flexstr(key), '\n'.join([flexstr(k) for k in self.keys()]))
#                 else:
#                     errormsg = 'Key "%s" not found since odict is empty' % key
#                 raise Exception(errormsg)
#         elif isinstance(key, Number):  # Convert automatically from float...dangerous?
#             thiskey = self.keys()[int(key)]
#             return OrderedDict.__getitem__(self, thiskey)
#         elif type(key) == slice:  # Handle a slice -- complicated
#             try:
#                 startind = self.__slicekey(key.start, 'start')
#                 stopind = self.__slicekey(key.stop, 'stop')
#                 if stopind < startind:
#                     print('Stop index must be >= start index (start=%i, stop=%i)' % (startind, stopind))
#                     raise Exception
#                 slicevals = [self.__getitem__(i) for i in range(startind, stopind)]
#                 output = self.__sanitize_items(slicevals)
#                 return output
#             except:
#                 print('Invalid odict slice... returning empty list...')
#                 return []
#         elif self.__is_odict_iterable(key):  # Iterate over items
#             listvals = [self.__getitem__(item) for item in key]
#             output = self.__sanitize_items(listvals)
#             return output
#         else:  # Handle everything else
#             return OrderedDict.__getitem__(self, key)
#
#     def __setitem__(self, key, value):
#         ''' Allows setitem to support strings, integers, slices, lists, or arrays '''
#         if isinstance(key, (str, tuple)):
#             OrderedDict.__setitem__(self, key, value)
#         elif isinstance(key, Number):  # Convert automatically from float...dangerous?
#             thiskey = self.keys()[int(key)]
#             OrderedDict.__setitem__(self, thiskey, value)
#         elif type(key) == slice:
#             startind = self.__slicekey(key.start, 'start')
#             stopind = self.__slicekey(key.stop, 'stop')
#             if stopind < startind:
#                 errormsg = 'Stop index must be >= start index (start=%i, stop=%i)' % (startind, stopind)
#                 raise Exception(errormsg)
#             slicerange = range(startind, stopind)
#             enumerator = enumerate(slicerange)
#             slicelen = len(slicerange)
#             if hasattr(value, '__len__'):
#                 if len(value) == slicelen:
#                     for valind, index in enumerator:
#                         self.__setitem__(index, value[valind])  # e.g. odict[:] = arr[:]
#                 else:
#                     errormsg = 'Slice "%s" and values "%s" have different lengths! (%i, %i)' % (
#                     slicerange, value, slicelen, len(value))
#                     raise Exception(errormsg)
#             else:
#                 for valind, index in enumerator:
#                     self.__setitem__(index, value)  # e.g. odict[:] = 4
#         elif self.__is_odict_iterable(key) and hasattr(value, '__len__'):  # Iterate over items
#             if len(key) == len(value):
#                 for valind, thiskey in enumerate(key):
#                     self.__setitem__(thiskey, value[valind])
#             else:
#                 errormsg = 'Keys "%s" and values "%s" have different lengths! (%i, %i)' % (
#                 key, value, len(key), len(value))
#                 raise Exception(errormsg)
#         else:
#             OrderedDict.__setitem__(self, key, value)
#         return None
#
#     def __repr__(self, maxlen=None, showmultilines=True, divider=False, dividerthresh=10, numindents=0, recurselevel=0,
#                  sigfigs=None, numformat=None):
#         ''' Print a meaningful representation of the odict '''
#
#         # Set primitives for display.
#         toolong = ' [...]'  # String to display at end of line when maximum value character length is overrun.
#         dividerstr = '*' * 40 + '\n'  # String to use as an inter-item divider.
#         indentstr = '    '  # Create string to use to indent.
#
#         # Only if we are in the root call, indent by the number of indents.
#         if recurselevel == 0:
#             theprefix = indentstr * numindents
#         else:  # Otherwise (if we are in a recursive call), indent only 1 indent.
#             theprefix = indentstr
#
#             # If the odict is empty, make the string just indicate it's an odict.
#         if len(self.keys()) == 0:
#             output = 'odict()'
#         else:
#             output = ''  # Initialize the output to nothing.
#             keystrs = []  # Start with an empty list which we'll save key strings in.
#             valstrs = []  # Start with an empty list which we'll save value strings in.
#             vallinecounts = []  # Start with an empty list which we'll save line counts in.
#             for i in range(len(self)):  # Loop over the dictionary values
#                 thiskeystr = flexstr(self.keys()[i])  # Grab a str representation of the current key.
#                 thisval = self.values()[i]  # Grab the current value.
#
#                 # If it's another odict, make a call increasing the recurselevel and passing the same parameters we received.
#                 if isinstance(thisval, odict):
#                     thisvalstr = flexstr(thisval.__repr__(maxlen=maxlen, showmultilines=showmultilines, divider=divider,
#                                                           dividerthresh=dividerthresh, numindents=numindents,
#                                                           recurselevel=recurselevel + 1, sigfigs=sigfigs,
#                                                           numformat=numformat))
#                 elif isnumber(thisval):  # Flexibly print out numbers, since they're largely why we're here
#                     if numformat is not None:
#                         thisvalstr = numformat % thisval
#                     elif sigfigs is not None:
#                         thisvalstr = sigfig(thisval, sigfigs=sigfigs)
#                     else:
#                         thisvalstr = str(thisval)  # To avoid numpy's stupid 0.4999999999945
#                 else:  # Otherwise, do the normal repr() read.
#                     thisvalstr = repr(thisval)
#
#                 # Add information to the lists to retrace afterwards.
#                 keystrs.append(thiskeystr)
#                 valstrs.append(thisvalstr)
#                 vallinecounts.append(thisvalstr.count('\n') + 1)  # Count the number of lines in the value.
#             maxvallinecounts = max(
#                 vallinecounts)  # Grab the maximum count of lines in the dict values.
#
#             maxkeylen = max([len(keystr) for keystr in keystrs])
#             for i in range(len(keystrs)):  # Loop over the lists
#                 keystr = keystrs[i]
#                 valstr = valstrs[i]
#                 vallinecount = vallinecounts[i]
#
#                 if (divider or (maxvallinecounts > dividerthresh)) and \
#                         showmultilines and recurselevel == 0 and i != 0:  # Add a divider line if we should.
#                     newoutput = indent(prefix=theprefix, text=dividerstr, width=80)
#                     if newoutput[-1] == '\n':
#                         newoutput = newoutput[:-1]
#                     output += newoutput
#
#                     # Trim the length of the entry if we need to.
#                 if not showmultilines:
#                     valstr = valstr.replace('\n', '\\n')  # Replace line breaks with characters
#
#                 # Trim long entries
#                 if maxlen and len(valstr) > maxlen:
#                     valstr = valstr[:maxlen - len(toolong)] + toolong
#
#                     # Create the the text to add, apply the indent, and add to the output
#                 spacer = ' ' * (maxkeylen - len(keystr))
#                 if vallinecount == 1 or not showmultilines:
#                     rawoutput = '#%i: "%s":%s %s\n' % (i, keystr, spacer, valstr)
#                 else:
#                     rawoutput = '#%i: "%s":%s \n%s\n' % (i, keystr, spacer, valstr)
#
#                 # Perform the indentation.
#                 newoutput = indent(prefix=theprefix, text=rawoutput, width=80)
#
#                 # Strip ot any terminal newline.
#                 if newoutput[-1] == '\n':
#                     newoutput = newoutput[:-1]
#
#                     # Add the new output to the full output.
#                 output += newoutput
#
#                 # Trim off any terminal '\n'.
#         if output[-1] == '\n':
#             output = output[:-1]
#
#         # Return the formatted string.
#         return output
#
#     def _repr_pretty_(self, p, cycle):
#         ''' Function to fix __repr__ in IPython'''
#         print(self.__repr__())
#
#     def disp(self, maxlen=None, showmultilines=True, divider=False, dividerthresh=10, numindents=0, sigfigs=5,
#              numformat=None):
#         '''
#         Print out flexible representation, short by default.
#
#         Example:
#             import optima as op
#             import pylab as pl
#             z = op.odict().make(keys=['a','b','c'], vals=(10*pl.rand(3)).tolist())
#             z.disp(sigfigs=3)
#             z.disp(numformat='%0.6f')
#         '''
#         print(self.__repr__(maxlen=maxlen, showmultilines=showmultilines,
#                             divider=divider, dividerthresh=dividerthresh,
#                             numindents=numindents, recurselevel=0, sigfigs=sigfigs, numformat=None))
#
#     def export(self, doprint=True):
#         ''' Export the odict in a form that is valid Python code '''
#         start = 'odict(['
#         end = '])'
#         output = start
#
#         for key in self.keys():
#             output += '(' + repr(key)
#             output += ', '
#             child = self.get(key)
#             if isinstance(child, odict):
#                 output += child.export(
#                     doprint=False)  # Handle nested odicts -- WARNING, can't doesn't work for e.g. lists of odicts!
#             else:
#                 output += repr(child)
#             output += '), '
#
#         output += end
#         if doprint:
#             print(output)
#             return None
#         else:
#             return output
#
#     def pop(self, key, *args, **kwargs):
#         ''' Allows pop to support strings, integers, slices, lists, or arrays '''
#         if isinstance(key, basestring):
#             return OrderedDict.pop(self, key, *args, **kwargs)
#         elif isinstance(key, Number):  # Convert automatically from float...dangerous?
#             thiskey = self.keys()[int(key)]
#             return OrderedDict.pop(self, thiskey, *args, **kwargs)
#         elif type(key) == slice:  # Handle a slice -- complicated
#             try:
#                 startind = self.__slicekey(key.start, 'start')
#                 stopind = self.__slicekey(key.stop, 'stop')
#                 if stopind < startind:
#                     print('Stop index must be >= start index (start=%i, stop=%i)' % (startind, stopind))
#                     raise Exception
#                 slicevals = [self.pop(i, *args, **kwargs) for i in range(startind, stopind)]  # WARNING, not tested
#                 try:
#                     return array(slicevals)  # Try to convert to an array
#                 except:
#                     return slicevals
#             except:
#                 print('Invalid odict slice... returning empty list...')
#                 return []
#         elif self.__is_odict_iterable(key):  # Iterate over items
#             listvals = [self.pop(item, *args, **kwargs) for item in key]
#             try:
#                 return array(listvals)
#             except:
#                 return listvals
#         else:  # Handle string but also everything else
#             try:
#                 return OrderedDict.pop(self, key, *args, **kwargs)
#             except:  # WARNING, should be KeyError, but this can't print newlines!!!
#                 if len(self.keys()):
#                     errormsg = 'odict key "%s" not found; available keys are:\n%s' % (flexstr(key),
#                                                                                       '\n'.join([flexstr(k) for k in
#                                                                                                  self.keys()]))
#                 else:
#                     errormsg = 'Key "%s" not found since odict is empty' % key
#                 raise Exception(errormsg)
#
#     def index(self, value):
#         ''' Return the index of a given key '''
#         return self.keys().index(value)
#
#     def valind(self, value):
#         ''' Return the index of a given value '''
#         return self.items().index(value)
#
#     def append(self, key=None, value=None):
#         ''' Support an append method, like a list '''
#         needkey = False
#         if value is None:  # Assume called with a single argument
#             value = key
#             needkey = True
#         if key is None or needkey:
#             keyname = 'key' + flexstr(len(self))  # Define the key just to be the current index
#         else:
#             keyname = key
#         self.__setitem__(keyname, value)
#         return None
#
#     def insert(self, pos=None, key=None, value=None):
#         '''
#         Stupid, slow function to do insert -- WARNING, should be able to use approach more like rename...
#
#         Usage:
#             z = odict()
#             z['foo'] = 1492
#             z.insert(1604)
#             z.insert(0, 'ganges', 1444)
#             z.insert(2, 'midway', 1234)
#         '''
#
#         # Handle inputs
#         realpos, realkey, realvalue = pos, key, value
#         if key is None and value is None:  # Assume it's called like odict.insert(666)
#             realvalue = pos
#             realkey = 'key' + flexstr(len(self))
#             realpos = 0
#         elif value is None:  # Assume it's called like odict.insert('devil', 666)
#             realvalue = key
#             realkey = pos
#             realpos = 0
#         if pos is None:
#             realpos = 0
#         if realpos > len(self):
#             errormsg = 'Cannot insert %s at position %i since length of odict is %i ' % (key, pos, len(self))
#             raise Exception(errormsg)
#
#         # Create a temporary dictionary to hold all of the items after the insertion point
#         tmpdict = odict()
#         origkeys = self.keys()
#         originds = range(len(origkeys))
#         if not len(originds) or realpos == len(originds):  # It's empty or in the final position, just append
#             self.__setitem__(realkey, realvalue)
#         else:  # Main usage case, it's not empty
#             try:
#                 insertind = originds.index(realpos)  # Figure out which index we're inseting at
#             except:
#                 errormsg = 'Could not insert item at position %i in odict with %i items' % (realpos, len(originds))
#                 raise Exception(errormsg)
#             keystopop = origkeys[insertind:]  # Pop these keys until we get far enough back
#             for keytopop in keystopop:
#                 tmpdict.__setitem__(keytopop, self.pop(keytopop))
#             self.__setitem__(realkey, realvalue)  # Insert the new item at the right location
#             for keytopop in keystopop:  # Insert popped items back in
#                 self.__setitem__(keytopop, tmpdict.pop(keytopop))
#
#         return None
#
#     def rename(self, oldkey, newkey):
#         ''' Change a key name -- WARNING, very inefficient! '''
#         nkeys = len(self)
#         if isinstance(oldkey, Number):
#             index = oldkey
#             keystr = self.keys()[index]
#         else:  # Forge ahead for strings and anything else!
#             index = self.keys().index(oldkey)
#             keystr = oldkey
#         self.__setitem__(newkey, self.pop(keystr))
#         if index < nkeys - 1:
#             for i in range(index + 1, nkeys):
#                 key = self.keys()[index]
#                 value = self.pop(key)
#                 self.__setitem__(key, value)
#         return None
#
#     def sort(self, sortby=None, reverse=False, copy=False):
#         '''
#         Create a sorted version of the odict. Sorts by order of sortby, if provided, otherwise alphabetical.
#         If copy is True, then returns a copy (like sorted()).
#
#         Note that you can also use this to do filtering.
#
#         Note: very slow, do not use for serious computations!!
#         '''
#         origkeys = self.keys()
#         if sortby is None:
#             allkeys = sorted(origkeys)
#         else:
#             if not isiterable(sortby): raise Exception('Please provide a list to determine the sort order.')
#             if all([isinstance(x, basestring) for x in sortby]):  # Going to sort by keys
#                 allkeys = sortby  # Assume the user knows what s/he is doing
#             elif all([isinstance(x, bool) for x in sortby]):  # Using Boolean values
#                 allkeys = []
#                 for i, x in enumerate(sortby):
#                     if x: allkeys.append(origkeys[i])
#             elif all([isinstance(x, Number) for x in sortby]):  # Going to sort by numbers
#                 if not set(sortby) == set(range(len(self))):
#                     errormsg = 'List to sort by "%s" is not compatible with length of odict "%i"' % (sortby, len(self))
#                     raise Exception(errormsg)
#                 else:
#                     allkeys = [y for (x, y) in sorted(zip(sortby, origkeys))]
#             else:
#                 raise Exception('Cannot figure out how to sort by "%s"' % sortby)
#         tmpdict = odict()
#         if reverse: allkeys.reverse()  # If requested, reverse order
#         if copy:
#             for key in allkeys: tmpdict[key] = self[key]
#             return tmpdict
#         else:
#             for key in allkeys: tmpdict.__setitem__(key, self.pop(key))
#             for key in allkeys: self.__setitem__(key, tmpdict.pop(key))
#             return None
#
#     def sorted(self, sortby=None, reverse=False):
#         ''' Shortcut for making a copy of the sorted odict '''
#         return self.sort(sortby=sortby, copy=True, reverse=reverse)
#
#     def reverse(self, copy=False):
#         ''' Reverse the order of an odict '''
#         reversedkeys = self.keys()
#         reversedkeys.reverse()
#         output = self.sort(sortby=reversedkeys, copy=copy)
#         return output
#
#     def reversed(self):
#         ''' Shortcut for making a copy of the sorted odict '''
#         return self.reverse(copy=True)
#
#     def make(self, keys=None, vals=None, keys2=None, keys3=None):
#         '''
#         An alternate way of making or adding to an odict. Examples:
#             a = odict().make(5) # Make an odict of length 5, populated with Nones and default key names
#             b = odict().make('foo',34) # Make an odict with a single key 'foo' of value 34
#             c = odict().make(['a','b']) # Make an odict with keys 'a' and 'b'
#             d = odict().make(['a','b'],0) # Make an odict with keys 'a' and 'b', initialized to 0
#             e = odict().make(keys=['a','b'], vals=[1,2]) # Make an odict with 'a':1 and 'b':2
#             f = odict({'a':34, 'b':58}).make(['c','d'],[99,45]) # Add extra keys to an exising odict
#             g = odict().make(keys=['a','b','c'], keys2=['A','B','C'], keys3=['x','y','z'], vals=0) # Make a triply nested odict
#         '''
#         # Handle keys
#         keylist = []
#         if keys is None and vals is None:
#             return None  # Nothing to do if nothing supplied
#         if keys is None and vals is not None:
#             keys = len(promotetolist(vals))  # Values are supplied but keys aren't: use default keys
#         if isinstance(keys, Number):  # It's a single number: pre-generate
#             keylist = ['%i' % i for i in range(keys)]  # Generate keylist
#         elif isinstance(keys, basestring):  # It's a single string
#             keylist = [flexstr(keys)]
#         elif isinstance(keys, list):  # It's a list: use directly
#             keylist = keys
#         else:
#             errormsg = 'Could not understand keys "%s": must be number, string, or list' % keys
#             raise Exception(errormsg)
#         nkeys = len(keylist)
#
#         # Handle values
#         vals = promotetolist(vals)
#         nvals = len(vals)
#         if nvals == 0:  # Special case: it's an empty list
#             vallist = [dcp(vals) for _ in range(nkeys)]
#         elif nvals == 1:  # Only a single value: duplicate it
#             vallist = [dcp(vals[0]) for _ in range(nkeys)]
#         elif nvals == nkeys:  # Lengths match, can use directly
#             vallist = vals
#         else:
#             errormsg = 'Must supply either a single value or a list of same length as the keys (%i keys, %i values supplied)' % (
#             nkeys, nvals)
#             raise Exception(errormsg)
#
#         # Handle nested keys -- warning, would be better to not hard-code this, but does the brain in as it is!
#         if keys2 is not None and keys3 is not None:  # Doubly nested
#             self.make(keys=keys, vals=odict().make(keys=keys2, vals=odict().make(keys=keys3, vals=vals)))
#         elif keys2 is not None:  # Singly nested
#             self.make(keys=keys, vals=odict().make(keys=keys2, vals=vals))
#         else:  # Not nested -- normal case of making an odict
#             for key, val in zip(keylist, vallist):  # Update odict
#                 self.__setitem__(key, val)
#
#         return self  # A bit weird, but usually would use this return an odict
#
#     def makefrom(self, source=None, keys=None, keynames=None, *args, **kwargs):
#         '''
#         Create an odict from entries in another dictionary. If keys is None, then
#         use all keys from the current dictionary.
#
#         Examples:
#             a = 'cat'; b = 'dog'; o = odict().makefrom(source=locals(), keys=['a','b']) # Make use of fact that variables are stored in a dictionary
#             d = {'a':'cat', 'b':'dog'}; o = odict().makefrom(d) # Same as odict(d)
#             l = ['cat', 'monkey', 'dog']; o = odict().makefrom(source=l, keys=[0,2], keynames=['a','b'])
#         '''
#
#         # Make sure it's iterable
#         if source is not None:  # Don't do anything if there's nothing there
#             if not (isiterable(source)):  # Make sure it's iterable
#                 source = promotetolist(source)
#             elif isinstance(source, basestring):
#                 source = [source]  # Special case -- strings are iterable, but we don't want to
#
#             if len(source) == 0:
#                 return self  # Nothing to do here
#             else:
#                 # Handle cases where keys or keynames are not supplied
#                 if keys is None:
#                     if isinstance(source, (list, tuple)):
#                         keys = range(len(source))
#                     elif isinstance(source, dict):
#                         keys = source.keys()
#                     else:
#                         raise Exception('Unable to guess keys for object of type %s' % type(source))
#                 keys = promotetolist(keys)  # Make sure it's a list
#                 if keynames is None: keynames = keys  # Use key names
#
#                 # Loop over supplied keys
#                 for key, keyname in zip(keys, keynames):
#                     try:
#                         self.__setitem__(str(keyname), source[key])
#                     except Exception as E:
#                         raise Exception('Key "%s" not found: %s' % (key, repr(E)))
#
#         return self  # As with make()
#
#     def map(self, func=None):
#         '''
#         Apply a function to each element of the odict, returning
#         a new odict with the same keys.
#
#         Example:
#             cat = odict({'a':[1,2], 'b':[3,4]})
#             def myfunc(mylist): return [i**2 for i in mylist]
#             dog = cat.map(myfunc) # Returns odict({'a':[1,4], 'b':[9,16]})
#         '''
#         output = odict()
#         for key in self.keys():
#             output[key] = func(self.__getitem__(key))
#         return output
#
#     def fromeach(self, ind=None, asdict=True):
#         '''
#         Take a "slice" across all the keys of an odict, applying the same
#         operation to entry. The simplest usage is just to pick an index.
#         However, you can also use it to apply a function to each key.
#
#         Example:
#             z = odict({'a':array([1,2,3,4]), 'b':array([5,6,7,8])})
#             z.fromeach(2) # Returns array([3,7])
#             z.fromeach(ind=[1,3], asdict=True) # Returns odict({'a':array([2,4]), 'b':array([6,8])})
#         '''
#         output = odict()
#         for key in self.keys():
#             output[key] = self.__getitem__(key)[ind]
#         if asdict:
#             return output  # Output as a slimmed-down odict
#         else:
#             return output[:]  # Output as just the entries
#
#     def toeach(self, ind=None, val=None):
#         '''
#         The inverse of fromeach: partially reset elements within
#         each odict key.
#
#         Example:
#             z = odict({'a':[1,2,3,4], 'b':[5,6,7,8]})
#             z.toeach(2, [10,20])    # z is now odict({'a':[1,2,10,4], 'b':[5,6,20,8]})
#             z.toeach(ind=3,val=666) #  z is now odict({'a':[1,2,10,666], 'b':[5,6,20,666]})
#         '''
#         nkeys = len(self.keys())
#         if not (isiterable(val)):  # Assume it's meant to be populated in each
#             val = [val] * nkeys  # Duplicated
#         if len(val) != nkeys:
#             errormsg = 'To map values onto each key, they must be the same length (%i vs. %i)' % (len(val), nkeys)
#             raise Exception(errormsg)
#         for k, key in self.enumkeys():
#             self.__getitem__(key)[ind] = val[k]
#         return None
#
#     def enumkeys(self):
#         ''' Shortcut for enumerate(odict.keys()) '''
#         iterator = enumerate(self.keys())
#         return iterator
#
#     def enumvals(self):
#         ''' Shortcut for enumerate(odict.values()) '''
#         iterator = enumerate(self.values())
#         return iterator
#
#     def enumitems(self):
#         ''' Returns tuple of 3 things: index, key, value '''
#         iterator = []  # Would be better to not pre-allocate but what can you do...
#         for ind, item in enumerate(self.items()):
#             thistuple = (ind,) + item  # Combine into one tuple
#             iterator.append(thistuple)
#         return iterator
#
#
#
#
#
