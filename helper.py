# -*- coding: utf-8 -*-
"""
Created on Mon Feb 29 11:35:02 2016

@author: madhura
"""

class Helper:
    def __init__(self):
        self.foo = 0.

    # Going from binary stunting/wasting to four fractions
    # Yes refers to more than 2 standard deviations below the global mean/median
    # in our notes, fractionYes = alpha
    def restratify(self,fractionYes):
        from scipy.stats import norm
        invCDFalpha = norm.ppf(fractionYes)
        fractionHigh     = norm.cdf(invCDFalpha - 1.)
        fractionModerate = fractionYes - norm.cdf(invCDFalpha - 1.)
        fractionMild     = norm.cdf(invCDFalpha + 1.) - fractionYes
        fractionNormal   = 1. - norm.cdf(invCDFalpha + 1.)
        restratification = {}
        restratification["normal"] = fractionNormal
        restratification["mild"] = fractionMild
        restratification["moderate"] = fractionModerate
        restratification["high"] = fractionHigh
        return restratification
        
        
    def quartic(self,coefficients,p0):
        from math import pow
        A,B,C,D,E = coefficients
        return A*pow(p0,4) + B*pow(p0,3) + C*pow(p0,2) + D*p0 + E
