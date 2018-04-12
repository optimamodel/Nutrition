
########################################################
# COST COVERAGE FUNCTIONS
########################################################
from numpy import exp, log

class Costcov():
    def __init__(self):
        self.foo = 0.

    def getCostCoverageCurve(self, costCoverageInfo, targetPopSize, totalPopSize, curveType):
        unitCost = costCoverageInfo['unitcost']
        saturation = costCoverageInfo['saturation']
        if curveType == 'linear':
            curve = self.linearCostCurve(unitCost, saturation, popSize)
        else: # defaults to this
            curve = self.increasingCostsLogisticCurve(unitCost, saturation, popSize)
        return curve

    def increasingCostsLogisticCurve(self, unitCost, saturation, popSize, totalPopSize):
        '''Produces the logistic function for increasing marginal costs, passing through origin'''
        B = saturation * popSize
        A = -B
        C = 0.
        D = unitCost*B/2.
        curve = self.getCostCoverageCurveSpecifyingParameters(A, B, C, D) / totalPopSize
        return curve

    def getCostCoverageCurveSpecifyingParameters(self, A, B, C, D):
        '''This is a logistic curve with each parameter (A,B,C,D) provided by the user'''
        if D == 0.: # this is for the special case when saturation/unitcost = 0.
            logisticCurve = lambda x: 0.
        else:
            logisticCurve = lambda x: (A + (B - A) / (1 + exp(-(x - C) / D)))
        return logisticCurve

    def linearCostCurve(self, unitCost, saturation, popSize):
        m = 1. / unitCost
        x0, y0 = [0.,0.] #extra point
        if x0 == 0.:
            c = y0
        else:
            c = y0 / (m * x0)
        maxCoverage = popSize * saturation
        linearCurve = lambda x: (min(m * x + c, maxCoverage))
        return linearCurve

    def getSpending(self, coverage, costCoverageInfo, popSize):
        '''Assumes standard increasing marginal costs curve '''
        unitCost = costCoverageInfo['unitcost']
        saturation = costCoverageInfo['saturation']
        B = saturation * popSize
        A = -B
        C = 0.
        D = unitCost * B / 2.
        curve = self.inverseLogistic(A, B, C, D)
        spending = curve(coverage)
        return spending

    def inverseLogistic(self, A, B, C, D):
        if D == 0.: # this is a temp fix for removing interventions
            inverseCurve = lambda y: 0.
        else:
            inverseCurve = lambda y: -D * log((B - y) / (y - A)) + C
        return inverseCurve

    def saveCurvesToPNG(self, curves, name, interventionList, popSize, resultsFileStem, budget, cascade, scale=True):
        import os
        import numpy as np
        import matplotlib.pyplot as plt
        path = resultsFileStem + '/cost_curves'
        if not os.path.exists(path):
            os.makedirs(path)
        plt.figure()
        # map colors to match excel colours
        colorDict = {'Vitamin A supplementation': 'g', 'Public provision of complementary foods': 'cornflowerblue',
                  'Complementary feeding education': 'gold', 'Breastfeeding promotion': 'grey',
                  'Balanced energy-protein supplementation': 'darkorange',
                  'Antenatal micronutrient supplementation': 'darkblue'}
        xvals = np.arange(0, 1e7, 1000)
        for intervention in interventionList:
            curveThisIntervention = curves[intervention]
            y = []
            for x in xvals:
                if scale: # rescale by popsize
                    y.append(curveThisIntervention(x) * popSize[intervention])
                else:
                    y.append(curveThisIntervention(x))
            plt.plot(xvals, y, label = str(intervention), color = colorDict[intervention])
        # add dotted lines for each cascade
        for cascadeValue in cascade:
            thisBudget = budget * cascadeValue
            plt.axvline(x=thisBudget, color = 'black', linestyle = 'dotted')
        plt.xlabel("spending")
        plt.ylabel("coverage")
        lgnd = plt.legend(bbox_to_anchor=(1.03,1), loc = 2, prop = {'size':10}, ncol=1, fancybox=True, shadow=True)
        plt.savefig(path + '/' + str(name) + '_'+ 'scale'+str(scale) + '.png', bbox_extra_artists=(lgnd,), bbox_inches = 'tight')
        plt.close()
        return
