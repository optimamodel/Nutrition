# -*- coding: utf-8 -*-
"""
Created on Tue Jul 19 11:34:05 2016

@author: ruth
"""
import pymp
#import numpy as np

#ex_array = np.zeros((100,), dtype='uint8')
#for index in range(0, 100):
#    ex_array[index] = 1
#    print('Yay! {} done!'.format(index))

ex_array = pymp.shared.array((100,), dtype='uint8')
with pymp.Parallel(4) as p:
    for index in p.range(0, 100):
        ex_array[index] = 1
        print p.num_threads
        # The parallel print function takes care of asynchronous output.
        #p.print('Yay! {} done!'.format(index))
        
with pymp.Parallel(4) as p:
    print(p.num_threads, p.thread_num)
    
    
from math import sqrt
from joblib import Parallel, delayed
thing = Parallel(n_jobs=2)(delayed(sqrt)(i**2) for i in range(10))

