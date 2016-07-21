# -*- coding: utf-8 -*-
"""
Created on Tue Feb 16 08:39:09 2016

@author: Nick
"""

import numpy as np

def get_data():
    # D stores data to calibrate to
    data_vars = ['population_size', 'mortality_per_month', 'percent_stunted']
    D = dict()
    for i in data_vars:
        D[i] = dict()
    
    D['population_size']['fertile_women'] = 100000
    D['mortality_per_month']['fertile_women'] = 100
    D['percent_stunted']['fertile_women'] = 0.1
    D['population_size']['0-1'] = 100000
    D['mortality_per_month']['0-1'] = 10
    D['percent_stunted']['0-1'] = 0.1
    D['population_size']['1-6'] = 100000
    D['mortality_per_month']['1-6'] = 1
    D['percent_stunted']['1-6'] = 0.1
    D['population_size']['6-12'] = 100000
    D['mortality_per_month']['6-12'] = 1
    D['percent_stunted']['6-12'] = 0.1
    D['population_size']['12-24'] = 100000
    D['mortality_per_month']['12-24'] = 1
    D['percent_stunted']['12-24'] = 0.1
    D['population_size']['24-72'] = 100000
    D['mortality_per_month']['24-72'] = 1
    D['percent_stunted']['24-72'] = 0.1
    
    return D


def get_params():
    # P stores the parameters
    pars = ['mortality', 'ageing', 'stunting_rate', 'stunting_recovery_rate']
    P = dict()
    for i in pars:
        P[i] = dict()
    
    pops = ['fertile_women', '0-1', '1-6', '6-12', '12-24', '24-72']
    # assumes the end of the month is the cutoff between ages
    for i in pops:
        P['mortality'][i] = dict()
    
    P['mortality']['fertile_women'] = 0.01
    P['mortality']['0-1']['non-stunted'] = 0.01
    P['mortality']['0-1']['stunted'] = 0.05
    P['mortality']['1-6']['non-stunted'] = 0.001
    P['mortality']['1-6']['stunted'] = 0.005
    P['mortality']['6-12']['non-stunted'] = 0.001
    P['mortality']['6-12']['stunted'] = 0.005
    P['mortality']['12-24']['non-stunted'] = 0.001
    P['mortality']['12-24']['stunted'] = 0.005
    P['mortality']['24-72']['non-stunted'] = 0.001
    P['mortality']['24-72']['stunted'] = 0.005
    
    P['birth_rate'] = 0.1  # birth rate per month
    
    P['ageing']['fertile_women'] = 1 / (20 * 12)  # 20 years of fertility
    P['ageing']['0-1'] = 1 / 1
    P['ageing']['1-6'] = 1 / 5
    P['ageing']['6-12'] = 1 / 6
    P['ageing']['12-24'] = 1 / 12
    P['ageing']['24-72'] = 1 / 48
    
    
    P['stunting_rate']['0-1'] = 0.01
    P['stunting_rate']['1-6'] = 0.01
    P['stunting_rate']['6-12'] = 0.01
    P['stunting_rate']['12-24'] = 0.01
    P['stunting_rate']['24-72'] = 0.01
    P['stunting_recovery_rate']['0-1'] = 0.001
    P['stunting_recovery_rate']['1-6'] = 0.001
    P['stunting_recovery_rate']['6-12'] = 0.001
    P['stunting_recovery_rate']['12-24'] = 0.001
    P['stunting_recovery_rate']['24-72'] = 0.001
    
    return P


def get_initial_conditions():
    pops = ['fertile_women', '0-1', '1-6', '6-12', '12-24', '24-72']
    # Setup compartments
    C0 = dict()
    for i in pops:
        C0[i] = np.array([0., 0.])

    # initial population sizes. Non-stunted and stunted. For pregnant women,
    # this is not at risk and at risk of giving birth to stunted children.
    C0['fertile_women'] = [1000., 100.]
    C0['0-1'] = [100., 10.]
    C0['1-6'] = [500., 50.]
    C0['6-12'] = [600., 60.]
    C0['12-24'] = [1200., 120.]
    C0['24-72'] = [4800., 480.]

    return C0
