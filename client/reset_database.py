#!/usr/bin/env python

'''
Small script to reset the user database -- WARNING, deletes everything!!!

Version: 2018jun04
'''

import scirisweb as sw
import nutrition_app as onwa
import os

try:    inputfunc = raw_input
except: inputfunc = input

webapp_dir = os.path.abspath(onwa.config.CLIENT_DIR)
redis_url = onwa.config.REDIS_URL
datastore = sw.DataStore(redis_url=redis_url)
prompt = 'Are you sure you want to reset the database for the following?\n  %s\n  %s\nAnswer (y/[n]): ' % (webapp_dir, redis_url)
answer = inputfunc(prompt)
if answer == 'y':
	datastore.flushdb()
else:
	print('Database not reset.')