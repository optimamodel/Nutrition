# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import numpy as np

pops = ['fertile_women', '0-1', '1-6', '6-12', '12-24', '24-72']

def steps(P, C0, t_steps):
    y = dict()
    for i in pops:
        y[i] = np.zeros((t_steps + 1, 2))
        y[i][0] = C0[i]
    for t in range(t_steps):
        for i in pops:
            y[i][t + 1] = y[i][t]  # move compartments forward in time
            if i not in {'fertile_women'}:
                y[i][t + 1][0] -= P['mortality'][i]['non-stunted'] * y[i][t + 1][0]  # mortality for non-stunted group
                y[i][t + 1][1] -= P['mortality'][i]['stunted'] * y[i][t + 1][1]  # mortality for stunted group
                y[i][t + 1][0] -= P['stunting_rate'][i] * y[i][t + 1][0]  # children become stunted
                y[i][t + 1][1] += P['stunting_rate'][i] * y[i][t + 1][0]
                y[i][t + 1][0] += P['stunting_recovery_rate'][i] * y[i][t + 1][1]  # children recover from stunting
                y[i][t + 1][1] -= P['stunting_recovery_rate'][i] * y[i][t + 1][1]         
        # ageing and births
        y['0-1'][t + 1] += P['birth_rate'] * y['fertile_women'][t + 1] - \
            P['ageing']['0-1'] * y['0-1'][t + 1]
        y['1-6'][t + 1] +=  P['ageing']['0-1'] * y['0-1'][t + 1] -  P['ageing']['1-6']* y['1-6'][t + 1]
        y['6-12'][t + 1] +=  P['ageing']['1-6'] * y['1-6'][t + 1] -  P['ageing']['6-12']* y['6-12'][t + 1]
        y['12-24'][t + 1] +=  P['ageing']['6-12'] * y['6-12'][t + 1] -  P['ageing']['12-24']* y['12-24'][t + 1]
        y['24-72'][t + 1] +=  P['ageing']['12-24'] * y['12-24'][t + 1] -  P['ageing']['24-72']* y['24-72'][t + 1]

    return y  # output
