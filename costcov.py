
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
        
        
        
    def plotExampleCurves(self):
        # CURRENTLY THESE EXAMPLE NUMBERS COME FROM BANGLADESH        
        import matplotlib.pyplot as plt
        import numpy as np
        xvals = np.arange(0, 1e8, 1000)
        s = 0.85
        p = 14537500.
        u = 5.
        y =[]
        for x in xvals:
            y.append( (2.*s/(1.+np.exp(-2.*x/(s*u*p))) - s)*p )
        plt.plot(xvals, y)
        plt.xlabel('spending')
        plt.ylabel('coverage')
        plt.title('FUNCTION:  pop x saturation ~ 1.2e7')
        plt.show()
        
        yvals = np.arange(0, 1, 1e-2)
        s = 0.85
        p = 14537500.
        u = 5.
        x =[]
        for y in yvals:
            x.append( -0.5*p*s*u* np.log(2.*s/(y*s*p)) )
        plt.plot(yvals, x)
        plt.ylabel('spending')
        plt.xlabel('coverage')
        plt.title('INVERSE FUNCTION')
        plt.show()
 