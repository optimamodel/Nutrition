# -*- coding: utf-8 -*-
"""
Created on Wed Feb 24 13:49:18 2016

@author: ruthpearson
"""

import new_design as code

#make the fertile women
mothers = code.FertileWomen(0.2, 500)

#make all the boxes for 0 to 1 month age (all combinations of stunting and wasting = 16 total)
# mild - up to 1 SD less than mean
# moderate - between 1 and 2 SD less than mean
# high - between 2 and 3 SD less than mean
# severe - more than 3 SD less than mean

"""
# Madhura's suggested code for Boxes
allBoxes = {}
for stuntingStatus in ["mild","moderate","high","severe"]:
    allBoxes{key=stuntingStatus} = code.Box(stuntingStatus,....)
"""

a1 = code.Box("mild", "mild", 200, 0.1)
a2 = code.Box("mild", "moderate", 200, 0.1)
a3 = code.Box("mild", "high", 200, 0.1)
a4 = code.Box("mild", "severe", 200, 0.1)

a5 = code.Box("moderate", "mild", 200, 0.1)
a6 = code.Box("moderate", "moderate", 200, 0.1)
a7 = code.Box("moderate", "high", 200, 0.1)
a8 = code.Box("moderate", "severe", 200, 0.1)

a9 = code.Box("high", "mild", 200, 0.1)
a10 = code.Box("high", "moderate", 200, 0.1)
a11 = code.Box("high", "high", 200, 0.1)
a12 = code.Box("high", "severe", 200, 0.1)

a13 = code.Box("severe", "mild", 200, 0.1)
a14 = code.Box("severe", "moderate", 200, 0.1)
a15 = code.Box("severe", "high", 200, 0.1)
a16 = code.Box("severe", "severe", 200, 0.1)

#put them all in a list
listOfBoxes0to1Month = [a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12, a13, a14, a15, a16 ]

#make the 0-1 month age group object
Month0to1 = code.AgeCompartment("0-1 month", listOfBoxes0to1Month, 1)

#make the 1-6 month age group object (just reuse 0-1 month list for now)
Month1to6 = code.AgeCompartment("1-6 month", listOfBoxes0to1Month, 0.2)

#make the list of age compartments
listOfAgeCompartments = [Month0to1, Month1to6]

#make the model object
model = code.Model("Main model", mothers, listOfAgeCompartments)



