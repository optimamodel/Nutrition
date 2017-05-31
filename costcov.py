
########################################################
# COST COVERAGE FUNCTIONS
########################################################
from numpy import array, maximum, exp, zeros, log

class Costcov():
    def __init__(self):
        self.foo = 0.

    def function(self, x, costCovInfo, popsize, eps=None):
        '''Returns coverage in a given year for a given spending amount.'''
        x = array([x])
        u = array([costCovInfo['unitcost']])
        s = array([costCovInfo['saturation']])
        if eps is None: eps = 1.e-3 #Settings().eps # Warning, use project-nonspecific eps
        popsize = array([popsize])

        nyrs,npts = len(u),len(x)
        eps = array([eps]*npts)
        if nyrs==npts: 
            y = maximum((2*s/(1+exp(-2*x/(popsize*s*u)))-s)*popsize,eps)
            return y[0]
        else:
            y = zeros((nyrs,npts))
            for yr in range(nyrs):
                y[yr,:] = maximum((2*s[yr]/(1+exp(-2*x/(popsize[yr]*s[yr]*u[yr])))-s[yr])*popsize[yr],eps)
            return y


    def inversefunction(self, y, costCovInfo, popsize):
        y = array([y])
        '''Returns cost in a given year for a given coverage amount.'''
        u = array([costCovInfo['unitcost']])
        s = array([costCovInfo['saturation']])
        if isinstance(popsize,(float,int)): popsize = array([popsize])
        
        nyrs,npts = len(u),len(y)
        if nyrs==npts: 
            x = -0.5*popsize*s*u*log((s*popsize-y)/(s*popsize+y))
            return x[0]    
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
        
        yvals = np.arange(0, 1.2e7, 1e2)
        s = 0.85
        p = 14537500.
        u = 5.
        x =[]
        for y in yvals:
            x.append( -0.5*p*s*u* np.log((s*p-y)/(s*p+y)))
        plt.plot(yvals, x)
        plt.ylabel('spending')
        plt.xlabel('coverage')
        plt.title('INVERSE FUNCTION')
        plt.show()
        
    def plotCurves(self, popSize, costCovInfo, plotTitle):
        import matplotlib.pyplot as plt
        import numpy as np
        #FUNCTION
        xvals = np.arange(0, 1e7, 1000)
        for intervention in costCovInfo.keys():
        
            s = costCovInfo[intervention]['saturation']
            p = popSize[intervention]
            u = costCovInfo[intervention]['unitcost']
            y = []
            for x in xvals:
                y.append( (2.*s/(1.+np.exp(-2.*x/(s*u*p))) - s)*p )
            plt.plot(xvals, y, label = intervention)
        plt.xlabel('spending')
        plt.ylabel('coverage')
        plt.title('FUNCTION: '+plotTitle)
        plt.legend(loc = 'upper center', bbox_to_anchor=(0.5, -0.15), ncol=1, fancybox=True, shadow=True)  #plt.legend()
        plt.show()
        #INVERSE FUNCTION
        yvals = np.arange(0, 1e6, 1e2)
        for intervention in costCovInfo.keys():
            s = costCovInfo[intervention]['saturation']
            p = popSize[intervention]
            u = costCovInfo[intervention]['unitcost']
            x = []
            for y in yvals:
                x.append( -0.5*p*s*u* np.log((s*p-y)/(s*p+y)))
            plt.plot(yvals, x, label = intervention)
        plt.ylabel('spending')
        plt.xlabel('coverage')
        plt.title('INVERSE FUNCTION: '+plotTitle)
        plt.legend(loc = 'upper center', bbox_to_anchor=(0.5, -0.15), ncol=1, fancybox=True, shadow=True)  #plt.legend()
        plt.show()    
 
 
 
    def outputCurvesToCSV(self, popSize, costCovInfo, filename):
        import numpy as np
        import csv
        #FUNCTION
        xvals = np.arange(0, 1e7, 1000)
        y = {}
        for intervention in costCovInfo.keys():
            s = costCovInfo[intervention]['saturation']
            p = popSize[intervention]
            u = costCovInfo[intervention]['unitcost']
            y[intervention] = [intervention]
            for x in xvals:
                y[intervention].append( (2.*s/(1.+np.exp(-2.*x/(s*u*p))) - s)*p )
        # write to csv
        x = ['spending'] + xvals.tolist()       
        outfile = filename + '_costCoverageCurves.csv'
        with open(outfile, "wb") as f:
            writer = csv.writer(f)
            writer.writerow(x)
            for key in y.keys():
                writer.writerow(y[key])  