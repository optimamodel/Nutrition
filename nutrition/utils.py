import os
import functools
import traceback
import multiprocessing
import numpy as np
import scipy.special
from scipy.optimize import brentq
import sciris as sc



def optimafolder(subfolder=None):
    if subfolder is None: subfolder='nutrition'
    parentfolder = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    folder = os.path.join(parentfolder, subfolder, '')
    return folder


# ##############################################################################
# ### HELPER FUNCTIONS
# ##############################################################################
#

def default_trackers(prev=None, rate=None):
    """
    The names of model outcomes that are tracked. The order of this list is important, so alter with caution.
    :param prev: return just prev (True) or everything else (False) or the entire list (None)
    :param rate: return just rates (True) or everything else (False) or the entire list (None)
    :return: a list of outcome variable names
    """
    outcomes = [
        'thrive',
        'child_deaths',
        'stunted',
        'wasted',
        'child_anaemic',
        'stunted_prev',
        'wasted_prev',
        'child_anaemprev',
        'pw_deaths',
        'pw_anaemic',
        'pw_anaemprev',
        'nonpw_anaemic',
        'nonpw_anaemprev',
        'child_mortrate',
        'pw_mortrate'
    ]
    if prev is not None:
        if prev:
            outcomes = [out for out in outcomes if 'prev' in out]
        else:
            outcomes = [out for out in outcomes if 'prev' not in out]
    if rate is not None:
        if rate:
            outcomes = [out for out in outcomes if 'rate' in out]
        else:
            outcomes = [out for out in outcomes if 'rate' not in out]
    return outcomes

def pretty_labels(direction=False):
    """
    Prettifies the variable names
    :param direction: Include max/min of the objective
    :return:
    """
    # pretty must correspond to the labels in 'default_trackers'
    pretty = [
        'Number of alive, non-stunted children',
        'Number of child deaths',
        'Number of stunted children',
        'Number of wasted children',
        'Number of anaemic children',
        'Prevalence of stunting in children',
        'Prevalence of wasting in children',
        'Prevalence of anaemia in children',
        'Number of pregnant women deaths',
        'Number of anaemic pregnant women',
        'Prevalence of anaemia in pregnant women',
        'Number of anaemic non-pregnant women',
        'Prevalence of anaemia in non-pregnant women',
        'Child mortality rate',
        'Pregnant women mortality rate'
    ]
    if direction: # for use in weighted objective
        pretty = direc_outcomes(pretty)
    labs = sc.odict(zip(default_trackers(), pretty))
    labs['Baseline'] = 'Est. spending \n baseline year' # this is for allocation
    return labs

def direc_outcomes(pretty):
    prefix = ['Maximize the '] + ['Minimize the '] * (len(pretty)-3) + ['Minimize '] * 2
    newlabs = [pre+lab.lower() for pre,lab in zip(prefix, pretty)]
    return newlabs

def relabel(old, direction=False): # todo: take and return list of labels, will be faster
    labs = pretty_labels(direction=direction)
    try:
        new = labs[str(old)] # do not allow indexing
    except:
        new = old
    return new

def get_obj_sign(obj):
    max_obj = ['thrive']
    if obj in max_obj:
        return -1
    else:
        return 1

def get_vector(obj):
    """ If a pre-defined objective is passed, this will create the corresponding weights """
    outcomes = default_trackers()
    try:
        i = outcomes.index(obj)
    except ValueError:
        raise Exception('ERROR: objective string not found')
    weights = np.zeros(len(outcomes))
    sign = get_obj_sign(obj)
    weights[i] = sign
    return weights

def get_weights(obj):
    """ Function to process weights """
    if isinstance(obj, str):
        # a pre-defined objective
        return get_vector(obj)
    elif isinstance(obj, np.ndarray):
        # custom weights, assume order as in default_trackers()
        return obj
    else:
        raise Exception("ERROR: cannot get weights for this object type")

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

def add_fixed_alloc(fixed, alloc, indx):
    """ Adds optimized allocations (for programs included in indx) to the fixed costs """
    total = np.copy(fixed)
    total[indx] += alloc
    return total

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