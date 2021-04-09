import os
import functools
import traceback
import multiprocessing
import numpy as np
import scipy.special
from scipy.optimize import brentq
import sciris as sc
import pathlib
import gettext

def optimafolder(subfolder=None):
    if subfolder is None: subfolder='nutrition'
    parentfolder = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    folder = os.path.join(parentfolder, subfolder, '')
    return folder

    #
    # path = pathlib.Path(__file__).parent.parent
    # for d in sc.promotetolist(subdir):
    #     path /= d
    # return path.resolve()

LOCALE_PATH = pathlib.Path(__file__).parent/"locale"

def get_translator(locale):
    translator = gettext.translation('nutrition', LOCALE_PATH, fallback=False, languages=[locale])
    return translator.gettext

# ##############################################################################
# ### HELPER FUNCTIONS
# ##############################################################################
#

def format_costtypes(oldlabs):
    maps = {'Linear (constant marginal cost) [default]': 'linear',
     'Curved with increasing marginal cost': 'increasing',
     'Curved with decreasing marginal cost': 'decreasing',
     'S-shaped (decreasing then increasing marginal cost)': 's-shaped'}
    newlabs = []
    for lab in oldlabs:
        newlabs.append(maps[lab])
    return newlabs

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
    Prettifies the variable names.
    Note that the order of pretty must match the order returned by default_trackers().
    :param direction: Include max/min of the objective
    :return:
    """
    if direction:
        # for use in weighted objective
        pretty = [
            'Maximize the number of alive, non-stunted children',
            'Minimize the number of child deaths',
            'Minimize the number of stunted children',
            'Minimize the number of wasted children',
            'Minimize the number of anaemic children',
            'Minimize the prevalence of stunting in children',
            'Minimize the prevalence of wasting in children',
            'Minimize the prevalence of anaemia in children',
            'Minimize the number of pregnant women deaths',
            'Minimize the number of anaemic pregnant women',
            'Minimize the prevalence of anaemia in pregnant women',
            'Minimize the number of anaemic non-pregnant women',
            'Minimize the prevalence of anaemia in non-pregnant women',
            'Minimize child mortality rate',
            'Minimize pregnant women mortality rate'
        ]
    else:
        pretty = [
            'Number of alive, non-stunted children turning age 5',
            'Number of child deaths',
            'Number of stunted children turning age 5',
            'Number of wasted children turning age 5',
            'Number of anaemic children turning age 5',
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
    labs = sc.odict(zip(default_trackers(), pretty))
    return labs

def relabel(old, direction=False):
    """ Can be given a string or a list of strings.
    Will return corresponding pretty label as a string or a list of strings """
    pretty = pretty_labels(direction=direction)
    pretty['Baseline'] = 'Est. spending \n baseline year' # this is for allocation
    if isinstance(old, list):
        new = []
        for lab in old:
            try:
                new.append(pretty[str(lab)])  # do not allow indexing
            except:
                new.append(lab)
    else:
        try:
            new = pretty[str(old)] # do not allow indexing
        except:
            new = old
    return new

def get_sign(obj):
    max_obj = ['thrive']
    if obj in max_obj:
        return -1
    else:
        return 1

def process_weights(weights):
    """ Creates an array of weights with the order corresponding to default_trackers().
    If conditions for the max/min problem is violated, will correct these by flipping sign.
    :param weights: an odict of (outcome, weight) pairs. Also allowing a string for single objectives.
    :return an array of floats """
    default = default_trackers()
    pretty1 = pretty_labels(direction=False)
    # reverse mapping to find outcome
    inv_pretty1 = {v: k for k, v in pretty1.items()}
    pretty2 = pretty_labels(direction=True)
    inv_pretty2 = {v: k for k, v in pretty2.items()}
    newweights = np.zeros(len(default))
    # if user just enters a string from the pre-defined objectives
    if sc.isstring(weights): weights = sc.odict({weights:1})
    if isinstance(weights, np.ndarray):
        newweights[:len(weights)] = weights
        return newweights
    for out, weight in weights.items():
        if out in default:
            thisout = out
            ind = default.index(out)
        elif out in inv_pretty1:
            thisout = inv_pretty1[out]
            ind = default.index(thisout)
        elif out in inv_pretty2:
            thisout = inv_pretty2[out]
            ind = default.index(thisout)
        else:
            print('Warning: "%s" is an invalid weighted outcome, removing'%out)
            continue
        sign = get_sign(thisout)
        newweights[ind] = abs(weight) * sign
    if np.all(newweights==0):
        raise Exception('All objective weights are zero. Process aborted.')
    return newweights

def read_sheet(spreadsheet, name, cols=None, dict_orient=None, skiprows=None, to_odict=False, dropna=None, debug_file_pfx=None):
    if dropna is None:
        dropna = 'all'
    df = spreadsheet.parse(name, index_col=cols, skiprows=skiprows)  # Grab the raw spreadsheet DataFrame
    if debug_file_pfx is not None:
        df.to_csv('%s_parse.csv' % debug_file_pfx)
    if dropna:
        df = df.dropna(how=dropna)
        if debug_file_pfx is not None:
            df.to_csv('%s_dropna.csv' % debug_file_pfx)
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

def scale_end_alloc(free, allocation, prog_info, inds, fixed):
    """
    Scales up spending allocations, limited by program coverage saturation and dependencies on other program coverages.
    :param free: total budget which can be allocated
    :param allocation: current budget allocations
    :param prog_info: a program information object from a relevant model instance to pull costcov data from
    :param inds: the indices of the programs to be checked
    :return: array of maximum spending for each program
    """
    new = np.sum(allocation)
    if new == 0:
        scaled_alloc = allocation.copy()
    else:
        scale = free / new
        scaled_alloc = allocation * scale
    max_allocation = get_max_spend(prog_info, inds, scaled_alloc, fixed)
    excess = 0
    over_count = 0
    for a, alloc in enumerate(scaled_alloc):
        if alloc >= max_allocation[a]:
            excess += alloc - max_allocation[a]
            scaled_alloc[a] = max_allocation[a]
            over_count += 1
    while excess > 1e-3 and over_count < len(scaled_alloc):
        redistribute = excess / (len(scaled_alloc) - over_count)
        for a, alloc in enumerate(scaled_alloc):
            if alloc < max_allocation[a] - redistribute:
                scaled_alloc[a] += redistribute
                excess -= redistribute
            elif alloc < max_allocation[a]:
                excess -= (max_allocation[a] - alloc)
                scaled_alloc[a] = max_allocation[a]
                over_count += 1
            elif alloc > max_allocation[a]:
                excess += alloc - max_allocation[a]
                scaled_alloc[a] = max_allocation[a]
                over_count += 1
        max_allocation = get_max_spend(prog_info, inds, scaled_alloc, fixed)
        for val in (scaled_alloc - max_allocation):
            if val > 0:
                over_count -= 1
    covs, max_covs = [], []
    prog_list = [prog_info.programs[i].name for i, ind in enumerate(inds) if ind]
    for p, prog in enumerate(prog_list):
        if inds[p]:
            max_covs.append(prog_info.programs[prog].func(np.ones(1)*max_allocation[p])[0])
            covs.append(prog_info.programs[prog].func(np.ones(1) * scaled_alloc[p])[0])
    if excess > 1e-3:
        scaled_alloc = np.append(scaled_alloc, excess)
    else:
        scaled_alloc = np.append(scaled_alloc, 0.0)

    return scaled_alloc


def get_max_spend(prog_info, keep_inds, curr_spends, fixed):
    """
    Checks if current spending allocations are above saturation or should be limited by dependency.
    :param prog_info: a program information object from a relevant model instance to pull costcov data from
    :param keep_inds: the indices of the programs to be checked
    :param curr_spends: the spending allocations to be checked
    :return: array of maximum spending for each program
    """
    rel_progs = sc.dcp(prog_info)
    max_spends = np.zeros(np.sum(keep_inds))
    list_max_covs = np.zeros(np.sum(keep_inds))
    keep_progs = [prog for p, prog in enumerate(rel_progs.programs) if keep_inds[p]]
    for p, prog in enumerate(keep_progs):
        max_covs = np.ones(np.sum(keep_inds))
        trigger = False
        # threshold
        if prog in [threshprog.name for threshprog in rel_progs.thresholdOrder]:
            child = rel_progs.thresholdOrder[[threshprog.name for threshprog in rel_progs.thresholdOrder].index(prog)]
            for parname in child.thresh_deps:
                par = next(prog for prog in rel_progs.programs.values() if prog.name == parname)
                # assuming uniform coverage across age bands, we can use the unrestricted coverage (NOT restricted)
                maxcov_child = min(par.func(np.ones(len(rel_progs.all_years))*curr_spends[keep_progs.index(par.name)])[0]/par.sat_unrestr, child.sat) * child.sat_unrestr

            trigger = True
        # exclusion
        if prog in [excludeprog.name for excludeprog in rel_progs.exclusionOrder]:
            child = rel_progs.exclusionOrder[[excludeprog.name for excludeprog in rel_progs.exclusionOrder].index(prog)]
            for parname in child.excl_deps:
                par = next((prog for prog in rel_progs.programs.values() if prog.name == parname))
                # assuming uniform coverage across age bands, we can use the unrestricted coverage (NOT restricted)
                maxcov_child = min(max(1.0 - par.func(np.ones(len(rel_progs.all_years))*curr_spends[keep_progs.index(par.name)])[0]/par.sat_unrestr, 0), child.sat) * child.sat_unrestr  # if coverage of parent exceeds child sat

            trigger = True
        if trigger:
            max_covs *= maxcov_child
            cpy_covs = sc.dcp(max_covs)  # this needs to be here because max_covs gets overwritten in the next step for no apparent reason...
            max_spends[p] = rel_progs.programs[prog].get_spending(max_covs)[0]
            list_max_covs[p] = cpy_covs[0]
        else:
            max_covs *= rel_progs.programs[prog].sat
            cpy_covs = sc.dcp(max_covs)  # this needs to be here because max_covs gets overwritten in the next step for no apparent reason...
            max_spends[p] = rel_progs.programs[prog].get_spending(max_covs)[0]
            list_max_covs[p] = cpy_covs[0]
        if max_spends[p] - fixed[keep_inds][p] >= 0:
            max_spends[p] -= fixed[keep_inds][p]
        else:
            max_spends[p] = 0
    return max_spends

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

def add_dummy_prog_data(prog_info, name):
    thisprog_data = sc.dcp(prog_info.prog_data)
    thisprog_data.base_cov[name] = 0.0
    thisprog_data.base_prog_set.append(name)
    thisprog_data.costs[name] = 1e12
    thisprog_data.costtype[name] = 'linear'
    thisprog_data.impacted_pop[name] = {pop: 1.0 for pop in thisprog_data.settings.all_ages} # so that it covers everyone in the model
    thisprog_data.prog_deps[name] = {'Exclusion dependency': [], 'Threshold dependency': []} # so that it has no dependencies
    thisprog_data.prog_target[name] = {pop: 1.0 for pop in thisprog_data.settings.all_ages} # so that it covers everyone in the model
    thisprog_data.sat[name] = 1.0
    return thisprog_data


