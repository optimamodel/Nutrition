# -*- coding: utf-8 -*-
"""
Created on Mon Jun 27 16:44:30 2016

@author: ruth
"""

#!/usr/bin/python
#PBS -l nodes=N:ppn=PPN
#PBS -l walltime=48:00:00
#PBS -N Nutrition optimisations
#PBS -A account
#PBS -o filename
#PBS -j oe
#PBS -m ea    

cd /home/ruthpearson/Nutrition/OptimisationScripts

import os
if os.environ.has_key('PBS_O_WORKDIR'):
    os.chdir(os.environ['PBS_O_WORKDIR'])

# body of script here …
python test1.py
python test2.py
