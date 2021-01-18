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
        'sam_prev',
        'child_anaemprev',
        'pw_deaths',
        'pw_anaemic',
        'pw_anaemprev',
        'nonpw_anaemic',
        'nonpw_anaemprev',
        'child_mortrate',
        'pw_mortrate',
        'young_bf',
        'old_bf',
        'stunted_prev_tot',
        'SAM_prev_tot',
        'wasted_prev_tot'
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
            'Minimize the prevalence of SAM in children',
            'Minimize the prevalence of anaemia in children',
            'Minimize the number of pregnant women deaths',
            'Minimize the number of anaemic pregnant women',
            'Minimize the prevalence of anaemia in pregnant women',
            'Minimize the number of anaemic non-pregnant women',
            'Minimize the prevalence of anaemia in non-pregnant women',
            'Minimize child mortality rate',
            'Minimize pregnant women mortality rate',
            'Maximize the prevalence of exclusive breastfeeding < 6 months',
            'Maximize the prevalence of age-appropriate breastfeeding 6-23 months',
            'Minimize the total number of stunted children under 5',
            'Minimize the total number of SAM children under 5',
            'Minimize the total number of wasted children under 5'
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
            'Prevalence of SAM in children',
            'Prevalence of anaemia in children',
            'Number of pregnant women deaths',
            'Number of anaemic pregnant women',
            'Prevalence of anaemia in pregnant women',
            'Number of anaemic non-pregnant women',
            'Prevalence of anaemia in non-pregnant women',
            'Child mortality rate',
            'Pregnant women mortality rate',
            'Prevalence of exclusive breastfeeding < 6 months',
            'Prevalence of age-appropriate breastfeeding 6-23 months',
            'Total number of stunted children under 5',
            'Total number of SAM children under 5',
            'Total number of wasted children under 5'
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
        if max_spends[p] - fixed[p] >= 0:
            max_spends[p] -= fixed[p]
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

def write_results_collected(results, combs, countries, projname=None, filename=None, folder=None, short_names=None):
    """ Writes outputs and program allocations to an xlsx book.
    For each scenario, book will include:
        - sheet called 'outcomes' which contains all outputs over time
        - sheet called 'budget and coverage' which contains all program cost and coverages over time """
    num_combs = combs
    num_countries = countries
    if projname is None: projname = ''
    outcomes = [
        'child_deaths',
        'stunted',
        'wasted',
        'child_anaemic'
    ]
    labs = pretty_labels()
    rows = [labs[out] for out in outcomes]
    if filename is None: filename = 'outputs.xlsx'
    filepath = sc.makefilepath(filename=filename, folder=folder, ext='xlsx', default='%s outputs.xlsx' % projname)
    outputs = []
    sheetnames = []
    for name in short_names:
        if isinstance(name, str):
            sheetnames.append(name)
        elif len(name) == 2:
            concat = name[0] + '_' + name[1]
            sheetnames.append(concat)
        else:
            concat = name[0] + '_' + name[1] + '_' + name[2]
            sheetnames.append(concat)
    alldata = []
    allformats = []
    years = results[0].years
    nullrow = [''] * len(years)

    ### Outcomes sheet
    for comb_num in list(range(num_combs)):
        headers = [['Country', 'Outcome'] + years + ['Cumulative']]
        for r, res in enumerate(results[comb_num * num_countries: (comb_num + 1) * num_countries]):
            out = res.get_outputs(outcomes, seq=True, pretty=True)
            for o, outcome in enumerate(rows):
                name = [res.name] if o == 0 else ['']
                thisout = out[o]
                if 'prev' in outcome.lower():
                    cumul = 'N/A'
                elif 'mortality' in outcome.lower():
                    cumul = 'N/A'
                else:
                    cumul = sum(thisout)
                outputs.append(name + [outcome] + list(thisout) + [cumul])
            outputs.append(nullrow)
        data = headers + outputs
        alldata.append(data)
        outputs = []

        # Formatting
        nrows = len(data)
        ncols = len(data[0])
        formatdata = np.zeros((nrows, ncols), dtype=object)
        formatdata[:, :] = 'plain'  # Format data as plain
        formatdata[:, 0] = 'bold'  # Left side bold
        formatdata[0, :] = 'header'  # Top with green header
        allformats.append(formatdata)
        del data
    '''
    ### Cost & coverage sheet
    # this is grouped not by program, but by coverage and cost (within each scenario)
    outputs = []
    headers = [['Scenario', 'Program', 'Type'] + years]
    for r, res in enumerate(results):
        rows = res.programs.keys()
        spend = res.get_allocs(ref=True)
        cov = res.get_covs(unrestr=False)
        # collate coverages first
        for r, prog in enumerate(rows):
            name = [res.name] if r == 0 else ['']
            thiscov = cov[prog]
            outputs.append(name + [prog] + ['Coverage'] + list(thiscov))
        # collate spending second
        for r, prog in enumerate(rows):
            thisspend = spend[prog]
            outputs.append([''] + [prog] + ['Budget'] + list(thisspend))
        outputs.append(nullrow)
    data = headers + outputs
    alldata.append(data)

    # Formatting
    nrows = len(data)
    ncols = len(data[0])
    formatdata = np.zeros((nrows, ncols), dtype=object)
    formatdata[:, :] = 'plain'  # Format data as plain
    formatdata[:, 0] = 'bold'  # Left side bold
    formatdata[0, :] = 'header'  # Top with green header
    allformats.append(formatdata)
    '''
    formats = {
        'header': {'bold': True, 'bg_color': '#3c7d3e', 'color': '#ffffff'},
        'plain': {},
        'bold': {'bold': True}}
    sc.savespreadsheet(filename=filename, data=alldata, sheetnames=sheetnames, formats=formats, formatdata=allformats)
    return filepath

def write_cost_effectiveness(cost_effectiveness_data, projname=None, filename=None, folder=None):
    filepath = sc.makefilepath(filename=filename, folder=folder, ext='xlsx', default='%s outputs.xlsx' % projname)
    outputs = []
    sheetnames = 'Cost effectiveness'
    alldata = []
    allformats = []

    ### Outcomes sheet
    headers = [['Scenario', 'Outcome']]
    for r, res in enumerate(cost_effectiveness_data.keys()):
        for o, outcome in enumerate(res):
            if o == 0:
                outputs.append([res] + [outcome])
            else:
                outputs.append([''] + [outcome])
    data = headers + outputs
    alldata.append(data)

    # Formatting
    nrows = len(data)
    ncols = len(data[0])
    formatdata = np.zeros((nrows, ncols), dtype=object)
    formatdata[:, :] = 'plain'  # Format data as plain
    formatdata[:, 0] = 'bold'  # Left side bold
    formatdata[0, :] = 'header'  # Top with green header
    allformats.append(formatdata)
    formats = {
        'header': {'bold': True, 'bg_color': '#3c7d3e', 'color': '#ffffff'},
        'plain': {},
        'bold': {'bold': True}}
    sc.savespreadsheet(filename=filename, data=alldata, sheetnames=sheetnames, formats=formats, formatdata=allformats)
    return filepath

def run_analysis(country):
    from . import project
    cov = 1.0
    progval = sc.odict(
        {'Balanced energy-protein supplementation': cov, 'Calcium supplementation': cov, 'Cash transfers': cov,
         'Delayed cord clamping': cov, 'IFA fortification of maize': cov, 'IFAS (community)': cov,
         'IFAS for pregnant women (community)': cov, 'IPTp': cov, 'Iron and iodine fortification of salt': cov,
         'IYCF 1': cov, 'Kangaroo mother care': cov, 'Lipid-based nutrition supplements': cov,
         'Long-lasting insecticide-treated bednets': cov, 'Mg for eclampsia': cov, 'Mg for pre-eclampsia': cov,
         'Micronutrient powders': cov, 'Multiple micronutrient supplementation': cov,
         'Oral rehydration salts': cov, 'Public provision of complementary foods': cov, 'Treatment of SAM': cov,
         'Vitamin A supplementation': cov, 'Zinc for treatment + ORS': cov, 'Zinc supplementation': cov})

    prog_list = sc.dcp(progval.keys())

    stunt_progs = sc.odict({'Balanced energy-protein supplementation': cov, 'Cash transfers': cov,
                            'IFAS for pregnant women (community)': cov, 'IPTp': cov,
                            'IYCF 1': cov, 'Kangaroo mother care': cov, 'Lipid-based nutrition supplements': cov,
                            'Long-lasting insecticide-treated bednets': cov,
                            'Multiple micronutrient supplementation': cov,
                            'Oral rehydration salts': cov, 'Public provision of complementary foods': cov,
                            'Treatment of SAM': cov,
                            'Vitamin A supplementation': cov, 'Zinc for treatment + ORS': cov,
                            'Zinc supplementation': cov})
    wast_progs = sc.odict({'Balanced energy-protein supplementation': cov, 'Cash transfers': cov,
                           'IFAS for pregnant women (community)': cov, 'IPTp': cov,
                           'IYCF 1': cov, 'Kangaroo mother care': cov, 'Lipid-based nutrition supplements': cov,
                           'Long-lasting insecticide-treated bednets': cov,
                           'Multiple micronutrient supplementation': cov,
                           'Oral rehydration salts': cov, 'Public provision of complementary foods': cov,
                           'Treatment of SAM': cov,
                           'Vitamin A supplementation': cov, 'Zinc for treatment + ORS': cov,
                           'Zinc supplementation': cov})
    anaem_progs = sc.odict({'Cash transfers': cov,
                            'Delayed cord clamping': cov, 'IFA fortification of maize': cov,
                            'Iron and iodine fortification of salt': cov,
                            'IYCF 1': cov, 'Kangaroo mother care': cov, 'Lipid-based nutrition supplements': cov,
                            'Long-lasting insecticide-treated bednets': cov,
                            'Micronutrient powders': cov, 'Oral rehydration salts': cov,
                            'Public provision of complementary foods': cov,
                            'Treatment of SAM': cov, 'Vitamin A supplementation': cov, 'Zinc for treatment + ORS': cov,
                            'Zinc supplementation': cov})
    mort_progs = sc.odict({'Cash transfers': cov, 'IFA fortification of maize': cov,
                           'IFAS for pregnant women (community)': cov, 'IPTp': cov,
                           'IYCF 1': cov, 'Kangaroo mother care': cov, 'Lipid-based nutrition supplements': cov,
                           'Long-lasting insecticide-treated bednets': cov,
                           'Multiple micronutrient supplementation': cov,
                           'Oral rehydration salts': cov, 'Public provision of complementary foods': cov,
                           'Treatment of SAM': cov,
                           'Vitamin A supplementation': cov, 'Zinc for treatment + ORS': cov,
                           'Zinc supplementation': cov})

    tol = [20000, 200000, 50000, 150000]
    p = project.Project(country + ' scaled up')
    p.load_data(country='costed_baseline_' + country, name=country, time_trend=False)
    baseline = p.run_baseline(country, prog_list)
    stunting_CE, stunting_cost, stunting_impact, best_stunting_progs = calc_CE(country, 'stunting', p, baseline,
                                                                               stunt_progs, prog_list, tol[0])
    wasting_CE, wasting_cost, wasting_impact, best_wasting_progs = calc_CE(country, 'wasting', p, baseline,
                                                                           wast_progs, prog_list, tol[1])
    anaemia_CE, anaemia_cost, anaemia_impact, best_anaemia_progs = calc_CE(country, 'anaemia', p, baseline,
                                                                               anaem_progs, prog_list, tol[2])
    mortality_CE, mortality_cost, mortality_impact, best_mortality_progs = calc_CE(country, 'mortality', p, baseline,
                                                                               mort_progs, prog_list, tol[3])
    CE_data = [[stunting_CE[:-1], stunting_cost[:-1], stunting_impact[:-1], best_stunting_progs[:-1]],
               [wasting_CE[:-1], wasting_cost[:-1], wasting_impact[:-1], best_wasting_progs[:-1]],
               [anaemia_CE[:-1], anaemia_cost[:-1], anaemia_impact[:-1], best_anaemia_progs[:-1]],
               [mortality_CE[:-1], mortality_cost[:-1], mortality_impact[:-1], best_mortality_progs[:-1]]]
    return CE_data

def run_total_analysis(country_list):
    from . import ui
    from . import project
    cov = 1.0
    progval = sc.odict(
        {'Balanced energy-protein supplementation': cov, 'Calcium supplementation': cov, 'Cash transfers': cov,
         'Delayed cord clamping': cov, 'IFA fortification of maize': cov, 'IFAS (community)': cov,
         'IFAS for pregnant women (community)': cov, 'IPTp': cov, 'Iron and iodine fortification of salt': cov,
         'IYCF 1': cov, 'Kangaroo mother care': cov, 'Lipid-based nutrition supplements': cov,
         'Long-lasting insecticide-treated bednets': cov, 'Mg for eclampsia': cov, 'Mg for pre-eclampsia': cov,
         'Micronutrient powders': cov, 'Multiple micronutrient supplementation': cov,
         'Oral rehydration salts': cov, 'Public provision of complementary foods': cov, 'Treatment of SAM': cov,
         'Vitamin A supplementation': cov, 'Zinc for treatment + ORS': cov, 'Zinc supplementation': cov})

    prog_list = sc.dcp(progval.keys())

    stunt_progs = sc.odict({'IFAS for pregnant women (community)': cov, 'IPTp': cov,
                            'IYCF 1': cov, 'Multiple micronutrient supplementation': cov,
                            'Public provision of complementary foods': cov,
                            'Treatment of SAM': cov,
                            'Vitamin A supplementation': cov, 'Zinc supplementation': cov})
    wast_progs = sc.odict({'Cash transfers': cov, 'Vitamin A supplementation': cov, 'Zinc supplementation': cov})
    anaem_progs = sc.odict({'IFA fortification of maize': cov, 'Iron and iodine fortification of salt': cov,
                            'Long-lasting insecticide-treated bednets': cov,
                            'Micronutrient powders': cov})
    mort_progs = sc.odict({'IFA fortification of maize': cov,
                           'IFAS for pregnant women (community)': cov, 'IPTp': cov,
                           'IYCF 1': cov, 'Kangaroo mother care': cov, 'Long-lasting insecticide-treated bednets': cov,
                           'Multiple micronutrient supplementation': cov,
                           'Oral rehydration salts': cov, 'Public provision of complementary foods': cov,
                           'Treatment of SAM': cov,
                           'Vitamin A supplementation': cov, 'Zinc for treatment + ORS': cov,
                           'Zinc supplementation': cov})


    programs = [stunt_progs, wast_progs, anaem_progs, mort_progs]
    tol = [20000, 200000, 50000, 150000]
    p = project.Project('scaled up')
    iptp_trigger = sc.odict()
    for country in country_list:
        p.load_data(country='costed_baseline_' + country, name=country, time_trend=False)
        if p.datasets[-1].demo_data.demo['Percentage of population at risk of malaria'] <= 0.005:
            iptp_trigger[country] = True
        else:
            iptp_trigger[country] = False
    for o, outcome in enumerate(['stunting', 'wasting']):#, 'anaemia', 'mortality']):
        effectiveness = 1.0
        baseline = 0
        objective_cost = []
        objective_impact = []
        objective_CE = []
        for country in country_list:
            if outcome == 'stunting':
                baseline += np.sum(p.run_baseline(country, prog_list).model.stunted)
            elif outcome == 'wasting':
                baseline += np.sum(p.run_baseline(country, prog_list).model.wasted)
            elif outcome == 'anaemia':
                baseline += np.sum(p.run_baseline(country, prog_list).model.child_anaemic)
            elif outcome == 'mortality':
                baseline += np.sum(p.run_baseline(country, prog_list).model.child_deaths)
        effective_progs = sc.odict()
        while effectiveness < tol[o] and programs[o]:
            trials = []
            trial = np.zeros(len(programs[o]))
            cost = np.zeros(len(programs[o]))
            for prog_num, prog in enumerate(programs[o].keys()):
                if prog == 'IPTp' or prog == 'Long-lasting insecticide-treated bednets':
                    trial_progs = sc.dcp(effective_progs)
                    trial_progs.append(prog, interp_cov(p, prog, [2018, 2024], cov))
                    scen_list = []
                    for c, country in enumerate(country_list):
                        kwargs = {'name': country + prog,
                                  'model_name': country,
                                  'scen_type': 'coverage',
                                  'progvals': trial_progs}
                        scen_list.append(ui.make_scens([kwargs]))
                    p.add_scens(scen_list)
                    p.run_scens_plus(prog_list, trial_progs)
                    for c, country in enumerate(country_list):
                        if not iptp_trigger[country]:
                            if outcome == 'stunting':
                                trial[prog_num] += np.sum(p.results['scens'][c].model.stunted)
                            elif outcome == 'wasting':
                                trial[prog_num] += np.sum(p.results['scens'][c].model.wasted)
                            elif outcome == 'anaemia':
                                trial[prog_num] += np.sum(p.results['scens'][c].model.child_anaemic)
                            elif outcome == 'mortality':
                                trial[prog_num] += np.sum(p.results['scens'][c].model.child_deaths)
                            cost[prog_num] += np.sum(p.results['scens'][c].programs[prog].annual_spend) - \
                                              (len(p.results['scens'][c].programs[prog].annual_spend)) * \
                                              p.results['scens'][c].programs[prog].annual_spend[0]
                        else:
                            if outcome == 'stunting':
                                trial[prog_num] += np.sum(p.run_baseline(country, prog_list).model.stunted)
                            elif outcome == 'wasting':
                                trial[prog_num] += np.sum(p.run_baseline(country, prog_list).model.wasted)
                            elif outcome == 'anaemia':
                                trial[prog_num] += np.sum(p.run_baseline(country, prog_list).model.child_anaemic)
                            elif outcome == 'mortality':
                                trial[prog_num] += np.sum(p.run_baseline(country, prog_list).model.child_deaths)

                else:
                    trial_progs = sc.dcp(effective_progs)
                    trial_progs.append(prog, interp_cov(p, prog, [2018, 2024], cov))
                    scen_list = []
                    for c, country in enumerate(country_list):
                        kwargs = {'name': country + prog,
                                  'model_name': country,
                                  'scen_type': 'coverage',
                                  'progvals': trial_progs}
                        scen_list.append(ui.make_scens([kwargs]))
                    p.add_scens(scen_list)
                    p.run_scens_plus(prog_list, trial_progs)
                    for c, country in enumerate(country_list):
                        if outcome == 'stunting':
                            trial[prog_num] += np.sum(p.results['scens'][c].model.stunted)
                        elif outcome == 'wasting':
                            trial[prog_num] += np.sum(p.results['scens'][c].model.wasted)
                        elif outcome == 'anaemia':
                            trial[prog_num] += np.sum(p.results['scens'][c].model.child_anaemic)
                        elif outcome == 'mortality':
                            trial[prog_num] += np.sum(p.results['scens'][c].model.child_deaths)
                        cost[prog_num] += np.sum(p.results['scens'][c].programs[prog].annual_spend) - \
                                          (len(p.results['scens'][c].programs[prog].annual_spend)) * \
                                          p.results['scens'][c].programs[prog].annual_spend[0]
                try:
                    trial_effectiveness = cost[prog_num] / (baseline - trial[prog_num])
                except RuntimeWarning:
                    trial_effectiveness = np.nan
                if trial_effectiveness >= 0:
                    trials.append(trial_effectiveness)
                    print(baseline, trial[prog_num], cost[prog_num], trial_effectiveness)
                else:
                    trials.append(np.nan)
            try:
                location = np.nanargmin(trials)
            except ValueError:
                break
            effective_progs.append(programs[o].keys()[location], interp_cov(p, programs[o].keys()[location], [2018, 2024], cov))
            effectiveness = trials[location]
            print(effectiveness, programs[o].keys()[location])
            objective_CE.append(effectiveness)
            objective_cost.append(cost[location])
            objective_impact.append(trial[location])
            baseline = trial[location]
            del programs[o][programs[o].keys()[location]]
        objective_progs = effective_progs.keys()
        if outcome == 'stunting':
            stunting_CE = objective_CE
            stunting_cost = objective_cost
            stunting_impact = objective_impact
            best_stunting_progs = objective_progs
        elif outcome == 'wasting':
            wasting_CE = objective_CE
            wasting_cost = objective_cost
            wasting_impact = objective_impact
            best_wasting_progs = objective_progs
        elif outcome == 'anaemia':
            anaemia_CE = objective_CE
            anaemia_cost = objective_cost
            anaemia_impact = objective_impact
            best_anaemia_progs = objective_progs
        elif outcome == 'mortality':
            mortality_CE = objective_CE
            mortality_cost = objective_cost
            mortality_impact = objective_impact
            best_mortality_progs = objective_progs
    CE_data = [[stunting_CE[:-1], stunting_cost[:-1], stunting_impact[:-1], best_stunting_progs[:-1]],
               [wasting_CE[:-1], wasting_cost[:-1], wasting_impact[:-1], best_wasting_progs[:-1]],
               [anaemia_CE[:-1], anaemia_cost[:-1], anaemia_impact[:-1], best_anaemia_progs[:-1]],
               [mortality_CE[:-1], mortality_cost[:-1], mortality_impact[:-1], best_mortality_progs[:-1]]]
    return CE_data


def calc_CE(country, objective, proj, baseline, progs, prog_list, tol):
    from . import ui
    new_baseline = sc.dcp(baseline)
    p = proj
    effectiveness = 1.0
    programs = sc.dcp(progs)
    effective_progs = sc.odict()
    objective_cost = []
    objective_impact = []
    objective_CE = []
    while effectiveness < tol and programs:
        trials = []
        for prog in programs.keys():
            if prog == 'IPTp' or prog == 'Long-lasting insecticide-treated bednets':
                if p.datasets[-1].demo_data.demo['Percentage of population at risk of malaria'] <= 0.005:
                    trial_progs = sc.dcp(effective_progs)
                    trial_progs.append(prog, interp_cov(p, prog, [2018, 2024], 0.95))
                    trials.append(np.nan)
                    continue
            trial_progs = sc.dcp(effective_progs)
            trial_progs.append(prog, interp_cov(p, prog, [2018, 2024], 0.95))
            kwargs = {'name': country,
                      'model_name': country,
                      'scen_type': 'coverage',
                      'progvals': trial_progs}
            scen_list = ui.make_scens([kwargs])
            p.add_scens(scen_list)
            p.run_scens_plus(prog_list, trial_progs)
            if objective == 'stunting':
                try:
                    trial_effectiveness = (np.sum(p.results['scens'][-1].programs[prog].annual_spend) - \
                                          (len(p.results['scens'][-1].programs[prog].annual_spend)) * \
                                          p.results['scens'][-1].programs[prog].annual_spend[0]) /\
                                          (np.sum(new_baseline.model.stunted) - np.sum(p.results['scens'][-1].model.stunted))
                except RuntimeWarning:
                    trial_effectiveness = np.nan
            elif objective == 'wasting':
                try:
                    trial_effectiveness = (np.sum(p.results['scens'][-1].programs[prog].annual_spend) - \
                                          (len(p.results['scens'][-1].programs[prog].annual_spend)) * \
                                          p.results['scens'][-1].programs[prog].annual_spend[0]) /\
                                          (np.sum(new_baseline.model.wasted) - np.sum(p.results['scens'][-1].model.wasted))
                except RuntimeWarning:
                    trial_effectiveness = np.nan
            elif objective == 'anaemia':
                try:
                    trial_effectiveness = (np.sum(p.results['scens'][-1].programs[prog].annual_spend) - \
                                          (len(p.results['scens'][-1].programs[prog].annual_spend)) * \
                                          p.results['scens'][-1].programs[prog].annual_spend[0]) /\
                                          (np.sum(new_baseline.model.child_anaemic) - np.sum(p.results['scens'][-1].model.child_anaemic))
                except RuntimeWarning:
                    trial_effectiveness = np.nan
            elif objective == 'mortality':
                try:
                    trial_effectiveness = (np.sum(p.results['scens'][-1].programs[prog].annual_spend) - \
                                          (len(p.results['scens'][-1].programs[prog].annual_spend)) * \
                                          p.results['scens'][-1].programs[prog].annual_spend[0]) /\
                                          (np.sum(new_baseline.model.child_deaths) - np.sum(p.results['scens'][-1].model.child_deaths))
                except RuntimeWarning:
                    trial_effectiveness = np.nan
            if trial_effectiveness >= 0:
                trials.append(trial_effectiveness)
            else:
                trials.append(np.nan)
        try:
            location = np.nanargmin(trials)
        except ValueError:
            break
        effective_progs.append(programs.keys()[location], interp_cov(p, programs.keys()[location], [2018, 2024], 0.95))
        kwargs = {'name': country,
                  'model_name': country,
                  'scen_type': 'coverage',
                  'progvals': effective_progs}
        scen_list = ui.make_scens([kwargs])
        p.add_scens(scen_list)
        p.run_scens_plus(prog_list, effective_progs)
        effectiveness = trials[location]
        print(effectiveness, programs.keys()[location])
        objective_CE.append(effectiveness)
        objective_cost.append((np.sum(p.results['scens'][-1].programs[programs.keys()[location]].annual_spend) -
                              (len(p.results['scens'][-1].programs[programs.keys()[location]].annual_spend)) *
                              p.results['scens'][-1].programs[programs.keys()[location]].annual_spend[0]))
        if objective == 'stunting':
            objective_impact.append(np.sum(baseline.model.stunted) - np.sum(p.results['scens'][-1].model.stunted))
        elif objective == 'wasting':
            objective_impact.append(np.sum(baseline.model.wasted) - np.sum(p.results['scens'][-1].model.wasted))
        elif objective == 'anaemia':
            objective_impact.append(np.sum(baseline.model.child_anaemic) - np.sum(p.results['scens'][-1].model.child_anaemic))
        elif objective == 'mortality':
            objective_impact.append(np.sum(baseline.model.child_deaths) - np.sum(p.results['scens'][-1].model.child_deaths))
        new_baseline = p.results['scens'][-1]
        del programs[programs.keys()[location]]
    objective_progs = effective_progs.keys()
    return objective_CE, objective_cost, objective_impact, objective_progs

def interp_cov(project, program, years, target):
    interp = []
    timeskip = years[1] - years[0]
    baseline_cov = project.models[-1].prog_info.programs[program].base_cov
    if baseline_cov >= target:
        return baseline_cov
    else:
        diff = target - baseline_cov
        for year in list(range(timeskip + 1)):
            interp.append(baseline_cov + year * diff / timeskip)
        return interp

