
########################################################
# COST COVERAGE FUNCTIONS
########################################################
class Costcov():
#class Costcov(CCOF):
    '''
    Cost-coverage object - used to calculate the coverage for a certain
    budget in a program. Best initialized with empty parameters,
    and later, add cost-coverage parameters with self.addccopar.

    Methods:

        addccopar(ccopar, overwrite=False, verbose=2)
            Adds a set of cost-coverage parameters for a budget year

            Args:
                ccopar: {
                            't': [2015,2016],
                            'saturation': [.90,1.],
                            'unitcost': [40,30]
                        }
                        The intervals in ccopar allow a randomization
                        to explore uncertainties in the model.

                overwrite: whether it should be added or replaced for
                           interpolation

        getccopar(t, verbose=2, sample='best')
            Returns an odict of cost-coverage parameters
                { 'saturation': [..], 'unitcost': [...], 't':[...] }
            used for self.evaulate.

            Args:
                t: a number/list of years to interpolate the ccopar
                randseed: used to randomly generate a varying set of parameters
                          to help determine the sensitivity/uncertainty of
                          certain parameters

        evaluate(x, popsize, t, toplot, inverse=False, randseed=None, bounds=None, verbose=2)
            Returns coverage if x=cost, or cost if x=coverage, this is defined by inverse.

            Args
                x: number, or list of numbers, representing cost or coverage
                t: years for each value of cost/coverage
                inverse: False - returns a coverage, True - returns a cost
                randseed: allows a randomization of the cost-cov parameters within
                    the given intervals

    '''

    def function(self, x, ccopar, popsize, eps=None):
        '''Returns coverage in a given year for a given spending amount.'''
        u = array(ccopar['unitcost'])
        s = array(ccopar['saturation'])
        if eps is None: eps = Settings().eps # Warning, use project-nonspecific eps
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
        if eps is None: eps = Settings().eps # Warning, use project-nonspecific eps
        if isnumber(popsize): popsize = array([popsize])

        nyrs,npts = len(u),len(x)
        eps = array([eps]*npts)
        if nyrs==npts: return maximum((2*s/(1+exp(-2*x/(popsize*s*u)))-s)*popsize,eps)
        else: raise OptimaException('coverage vector should be the same length as params.')
