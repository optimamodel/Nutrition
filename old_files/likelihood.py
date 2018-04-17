# -*- coding: utf-8 -*-
"""
Created on Mon Feb 15 15:50:20 2016

@author: Nick
"""

import numpy as np
from scipy.stats import norm
from nutrition.model import steps


def model_outcomes(C0, P, D, t_steps, pops, verbose=2):

    y = steps(P, C0, t_steps)

    # M stores model outcomes to be calibrated
    data_vars = ['population_size', 'mortality_per_month', 'mortality_rate', 'percent_stunted']
    M = dict()
    for i in data_vars:
        M[i] = dict()

    M['population_size']['fertile_women'] = sum(y['fertile_women'][t_steps])
    M['mortality_per_month']['fertile_women'] = sum(y['fertile_women'][t_steps]) * P['mortality']['fertile_women']
    M['percent_stunted']['fertile_women'] = y['fertile_women'][t_steps][1] / sum(y['fertile_women'][t_steps])
    M['population_size']['0-1'] = sum(y['0-1'][t_steps])
    M['mortality_per_month']['0-1'] = y['0-1'][t_steps][0] * P['mortality']['0-1']['non-stunted'] + y['0-1'][t_steps][1] * P['mortality']['0-1']['stunted']
    M['percent_stunted']['0-1'] = y['0-1'][t_steps][1] / sum(y['0-1'][t_steps])
    M['population_size']['1-6'] = sum(y['1-6'][t_steps])
    M['mortality_per_month']['1-6'] = y['1-6'][t_steps][0] * P['mortality']['1-6']['non-stunted'] + y['1-6'][t_steps][1] * P['mortality']['1-6']['stunted']
    M['percent_stunted']['1-6'] = y['1-6'][t_steps][1] / sum(y['1-6'][t_steps])
    M['population_size']['6-12'] = sum(y['6-12'][t_steps])
    M['mortality_per_month']['6-12'] = y['6-12'][t_steps][0] * P['mortality']['6-12']['non-stunted'] + y['6-12'][t_steps][1] * P['mortality']['6-12']['stunted']
    M['percent_stunted']['6-12'] = y['6-12'][t_steps][1] / sum(y['6-12'][t_steps])
    M['population_size']['12-24'] = sum(y['12-24'][t_steps])
    M['mortality_per_month']['12-24'] = y['12-24'][t_steps][0] * P['mortality']['12-24']['non-stunted'] + y['12-24'][t_steps][1] * P['mortality']['12-24']['stunted']
    M['percent_stunted']['12-24'] = y['12-24'][t_steps][1] / sum(y['12-24'][t_steps])
    M['population_size']['24-72'] = sum(y['24-72'][t_steps])
    M['mortality_per_month']['24-72'] = y['24-72'][t_steps][0] * P['mortality']['24-72']['non-stunted'] + y['24-72'][t_steps][1] * P['mortality']['24-72']['stunted']
    M['percent_stunted']['24-72'] = y['24-72'][t_steps][1] / sum(y['24-72'][t_steps])

    return M


def lnlike(C0, P, D, t_steps, pops):    

    M = model_outcomes(C0, P, D, t_steps, pops, verbose=2)
    lnlike_total = 0
    # Log-Likelihood for Mortality
    for i in pops:
        lnlike_total += lnpoisson_rel(D['mortality_per_month'][i], M['mortality_per_month'][i])

    # Log-Likelihood for percent stunted
    for i in pops:
        stat_epi = logit(D['percent_stunted'][i]) - logit(M['percent_stunted'][i])
        lnlike_total += norm.logpdf(stat_epi)

    return lnlike_total


def lnpoisson_rel(k, lam):
    return k*np.log(lam) - lam


def logit(p):
    return np.log(p/(1.-p))
