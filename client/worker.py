#!/usr/bin/env python

# Imports
import os
import sys
import multiprocessing as mp
import nutrition_app.apptasks as at

nworkers = max(1,mp.cpu_count()//2)
args = [__file__, '-l', 'info', '-P', 'solo']
iswin = 'win' in sys.platform
if iswin:
    nworkers = 1

# Run Celery
print('Starting %s workers...' % nworkers)
for i in range(nworkers):
    if not iswin: pid = os.fork()
    else:         pid = 0
    if pid == 0:
        my_pid = os.getpid()
        workername = 'worker_%s' % my_pid
        print('  Starting forked worker %s' % workername)
        args.extend(['-n', workername]) # Still get warnings, but seems to work
        at.celery_instance.worker_main(args)