# -*- coding: utf-8 -*-
"""
Created on Mon Feb 15 16:26:24 2016

@author: Nick
"""

# just deleting variables quickly while I play with file
for name in dir():
    if not name.startswith('_'):
        del globals()[name]


import numpy as np
import pylab as pl
from nutrition.model import steps
from likelihood import lnlike, model_outcomes
from inputs import get_data, get_params, get_initial_conditions
from mcmc import mcmc

pops = ['fertile_women', '0-1', '1-6', '6-12', '12-24', '24-72']
D = get_data()
P = get_params()
C0 = get_initial_conditions()

t_steps = 1000  # model run time (months)

# Run the model
y = steps(P, C0, t_steps)

LL = lnlike(C0, P, D, t_steps, pops)


# Parameters to calibrate
meta_prefit = dict()
meta_prefit['mortality, 0-1, non-stunted'] = P['mortality']['0-1']['non-stunted']
meta_prefit['mortality, 0-1, stunted'] = P['mortality']['0-1']['stunted']
meta_prefit['mortality, 1-6, non-stunted'] = P['mortality']['1-6']['non-stunted']
meta_prefit['mortality, 1-6, stunted'] = P['mortality']['1-6']['stunted']
meta_prefit['mortality, 6-12, non-stunted'] = P['mortality']['6-12']['non-stunted']
meta_prefit['mortality, 6-12, stunted'] = P['mortality']['6-12']['stunted']
meta_prefit['mortality, 12-24, non-stunted'] = P['mortality']['12-24']['non-stunted']
meta_prefit['mortality, 12-24, stunted'] = P['mortality']['12-24']['stunted']
meta_prefit['mortality, 24-72, non-stunted'] = P['mortality']['24-72']['non-stunted']
meta_prefit['mortality, 24-72, stunted'] = P['mortality']['24-72']['stunted']

nwalkers=20
nsteps=50
nburn=10
storage="mcmc"

mc = mcmc(meta_prefit, C0, P, D, t_steps, pops, nwalkers=20, nsteps=50, nburn=10, storage="mcmc")

P['mortality']['0-1']['non-stunted'] = np.mean(mc[:,0])
P['mortality']['0-1']['stunted'] = np.mean(mc[:,1])
P['mortality']['1-6']['non-stunted'] = np.mean(mc[:,2])
P['mortality']['1-6']['stunted'] = np.mean(mc[:,3])
P['mortality']['6-12']['non-stunted'] = np.mean(mc[:,4])
P['mortality']['6-12']['stunted'] = np.mean(mc[:,5])
P['mortality']['12-24']['non-stunted'] = np.mean(mc[:,6])
P['mortality']['12-24']['stunted'] = np.mean(mc[:,7])
P['mortality']['24-72']['non-stunted'] = np.mean(mc[:,8])
P['mortality']['24-72']['stunted'] = np.mean(mc[:,9])

y = steps(P, C0, t_steps)

M = model_outcomes(C0, P, D, t_steps, pops)



pl.subplot(211)
pl.plot(y['0-1'][:, 0], 'g-', label='0-1')
pl.plot(y['1-6'][:, 0], 'r-', label='1-6')
pl.plot(y['6-12'][:, 0], 'b-', label='6-12')
pl.plot(y['12-24'][:, 0], 'y-', label='12-24')
pl.plot(y['24-72'][:, 0], 'c-', label='24-72')
pl.ylabel("Population size")
pl.xlabel('Time (months)')
pl.legend(loc='best')
#pl.ylim(0, 50)
pl.title('Non-stunted')
pl.subplot(212)
pl.plot(y['0-1'][:, 1], 'g-', label='0-1')
pl.plot(y['1-6'][:, 1], 'r-', label='1-6')
pl.plot(y['6-12'][:, 1], 'b-', label='6-12')
pl.plot(y['12-24'][:, 1], 'y-', label='12-24')
pl.plot(y['24-72'][:, 1], 'c-', label='24-72')
pl.ylabel("Population size")
pl.xlabel('Time (months)')
pl.legend(loc='best')
#pl.ylim(0, 50)
pl.title('Stunted')
pl.show()


width = 0.5      # the width of the bars: can also be len(x) sequence
p1 = pl.bar([0, 1], y['0-1'][t_steps-1,:], width, color='g')
p2 = pl.bar([0, 1], y['1-6'][t_steps-1,:], width, color='r', bottom=y['0-1'][t_steps-1,:])
p3 = pl.bar([0, 1], y['6-12'][t_steps-1,:], width, color='b', bottom=y['0-1'][t_steps-1,:] + y['1-6'][t_steps-1,:])
p4 = pl.bar([0, 1], y['12-24'][t_steps-1,:], width, color='y', bottom=y['0-1'][t_steps-1,:] + y['1-6'][t_steps-1,:] + + y['6-12'][t_steps-1,:])
p5 = pl.bar([0, 1], y['24-72'][t_steps-1,:], width, color='c', bottom=y['0-1'][t_steps-1,:] + y['1-6'][t_steps-1,:] + y['6-12'][t_steps-1,:] + y['12-24'][t_steps-1,:])
pl.ylabel('Number of people')
pl.title('Population decomposition')
pl.xticks([0+width/2, 1+width/2], ('Non-stunted', 'Stunted'))
#pl.yticks(np.arange(0, 81, 10))
pl.legend((p1[0], p2[0], p3[0], p4[0], p5[0]), ('0-1', '1-6', '6-12', '12-24', '24-72'), loc='best')
pl.show()


