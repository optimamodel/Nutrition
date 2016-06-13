
########################################################
# COST COVERAGE FUNCTIONS
########################################################
from numpy import array, maximum, exp, zeros, log

class Costcov():
    def __init__(self):
        self.foo = 0.

    def function(self, x, costCovInfo, popsize, eps=None):
        '''Returns coverage in a given year for a given spending amount.'''
        u = array(costCovInfo['unitcost'])
        s = array(costCovInfo['saturation'])
        if eps is None: eps = 1.e-3 #Settings().eps # Warning, use project-nonspecific eps
        popsize = array([popsize])

        nyrs,npts = len(u),len(x)
        eps = array([eps]*npts)
        if nyrs==npts: return maximum((2*s/(1+exp(-2*x/(popsize*s*u)))-s)*popsize,eps)
        else:
            y = zeros((nyrs,npts))
            for yr in range(nyrs):
                y[yr,:] = maximum((2*s[yr]/(1+exp(-2*x/(popsize[yr]*s[yr]*u[yr])))-s[yr])*popsize[yr],eps)
            return y


    def inversefunction(self, y, costCovInfo, popsize):
        '''Returns cost in a given year for a given coverage amount.'''
        u = array(costCovInfo['unitcost'])
        s = array(costCovInfo['saturation'])
        if isinstance(popsize,(float,int)): popsize = array([popsize])
        
        nyrs,npts = len(u),len(y)
        if nyrs==npts: return -0.5*popsize*s*u*log(2*s/(y+s*popsize))
        else: raise Exception('y should be the same length as params.')
 