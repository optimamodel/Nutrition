# -*- coding: utf-8 -*-
"""
Created on Mon Jun 27 16:56:24 2016

@author: ruth
"""

import pickle as pickle
# put it in a file    
filename = 'test2.pkl'
outfile = open(filename, 'wb')
pickle.dump('test', outfile)
outfile.close()