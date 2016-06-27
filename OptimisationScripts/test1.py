# -*- coding: utf-8 -*-
"""
Created on Mon Jun 27 16:54:14 2016

@author: ruth
"""

import pickle as pickle
# put it in a file    
filename = 'test1.pkl'
outfile = open(filename, 'wb')
pickle.dump('test', outfile)
outfile.close()