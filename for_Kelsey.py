# -*- coding: utf-8 -*-
"""
Created on Wed Jun 15 15:21:03 2016

@author: ruth
"""

#  BAR PLOTS

# output of the form that is used in getBudgetPieChartComparison() function in output.py
# this is a dictionary:  keys are the interventions/programs, values are the investement
budgetDict = {u'Balanced energy supplementation': 0.0,
 u'Breastfeeding promotion (dual delivery)': 17912252.785727482,
 u'Complementary feeding (education)': 14456379.117452756,
 u'Complementary feeding (supplementation)': 0.0,
 u'Multiple micronutrient supplementation': 0.0,
 u'Vitamin A supplementation': 3672812.6745154802,
 u'Zinc supplementation': 0.0}
 
# example:
print budgetDict.keys()
print budgetDict.values()


#  X Y PLOTS

# list of years
x = range(2017, 2030, 1)
# list of number of deaths baseline case
y1 = [9493.1515302878943,
 101880.28456989137,
 105200.65680258311,
 105696.22029377249,
 105529.90142284974,
 105107.26798423484,
 104516.83241802966,
 103804.9693094159,
 103006.82617124997,
 102149.1455600115,
 101251.6481524104,
 100328.59060645255,
 99390.169369857991,
 98443.63304088125]
# list of number of deaths optimised case
y2 = [9189.8432064944609,
 98430.890111563291,
 101507.43519598321,
 101882.02174558074,
 101643.62232500245,
 101180.94898359658,
 100573.48038126883,
 99861.031173957395,
 99073.926344394567,
 98235.425318791415,
 97362.761779475375,
 96468.427031416912,
 95561.368048689095,
 94647.950437817257]