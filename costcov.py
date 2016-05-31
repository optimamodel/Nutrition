
########################################################
# COST COVERAGE FUNCTIONS
########################################################
class Costcov():
    def __init__(self):
        self.foo = 0.

    def function(self, x, ccopar, popsize, eps=None):
        '''Returns coverage in a given year for a given spending amount.'''
        u = array(ccopar['unitcost'])
        s = array(ccopar['saturation'])
        if eps is None: eps = 1.e-3 #Settings().eps # Warning, use project-nonspecific eps
        if isnumber(popsize): popsize = array([popsize])

        nyrs,npts = len(u),len(x)
        eps = array([eps]*npts)
        if nyrs==npts: return maximum((2*s/(1+exp(-2*x/(popsize*s*u)))-s)*popsize,eps)
        else:
            y = zeros((nyrs,npts))
            for yr in range(nyrs):
                y[yr,:] = maximum((2*s[yr]/(1+exp(-2*x/(popsize[yr]*s[yr]*u[yr])))-s[yr])*popsize[yr],eps)
            return y

    def inversefunction(self, x, ccopar, popsize, eps=None):
        '''Returns coverage in a given year for a given spending amount.'''
        u = array(ccopar['unitcost'])
        s = array(ccopar['saturation'])
        if eps is None: eps = 1.e-3 #Settings().eps # Warning, use project-nonspecific eps
        if isnumber(popsize): popsize = array([popsize])

        nyrs,npts = len(u),len(x)
        eps = array([eps]*npts)
        if nyrs==npts: return maximum((2*s/(1+exp(-2*x/(popsize*s*u)))-s)*popsize,eps)
        else: raise OptimaException('coverage vector should be the same length as params.')
