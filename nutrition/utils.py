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

def default_trackers(prev=None):
    """ Prevalence tracker names MUST contains the string 'prev' """
    outcomes = [
        'stunting_prev',
        'wasting_prev',
        'child_anaemprev',
        'pw_anaemprev',
        'nonpw_anaemprev',
        'child_deaths',
        'pw_deaths',
        'thrive',
        'stunted',
        'wasted']
    if prev is not None:
        if prev:
            outcomes = [out for out in outcomes if 'prev' in out]
        else:
            outcomes = [out for out in outcomes if 'prev' not in out]
    return outcomes

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

def pretty_labels():
    labs = sc.odict()
    labs['thrive'] = 'Number of alive, non-stunted children'
    labs['stunting_prev'] = 'Prevalence of stunting in children'
    labs['child_deaths'] = 'Child deaths'
    labs['pw_deaths'] = 'Pregnant women deaths'
    labs['child_anaemprev'] = 'Prevalence of anaemia in children'
    labs['pw_anaemprev'] = 'Prevalence of anaemia in pregnant women'
    labs['nonpw_anaemprev'] = 'Prevalence of anaemia in non-pregnant women'
    labs['wasting_prev'] = 'Prevalence of wasting in children'
    labs['Baseline'] = 'Est. spending \n baseline year' # this is for allocation
    return labs

def relabel(old):
    """ Turn a variable label into a user-friendly version """
    labs = pretty_labels()
    try:
        new = labs[str(old)] # do not allow indexing
    except:
        new = old
    return new

def read_sheet(spreadsheet, name, cols=None, dict_orient=None, skiprows=None, to_odict=False, dropna=None):
    if dropna is None: dropna = 'all'
    df = spreadsheet.parse(name, index_col=cols, skiprows=skiprows)
    if dropna:
        df = df.dropna(how=dropna)
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