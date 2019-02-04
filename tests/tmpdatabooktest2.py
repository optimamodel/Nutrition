#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  5 09:08:56 2019

@author: cliffk
"""

#%%
#from nutrition import ui as nu
#proj = nu.demo()
#proj.save('tmp.prj')

import sciris as sc
proj = sc.loadobj('tmp.prj')
wb = proj.inputsheet()
wb.writecells(sheetname='Baseline year population inputs', cells=[], vals=[], verbose=False, wbargs={'data_only': False})
proj.load_data(fromfile=False)