#!/usr/bin/env python

'''
Small script to reset the user database -- WARNING, deletes everything!!!

Version: 2018mar17
'''

import sciris.datastore as ds
from hptool.webapp import config

answer = raw_input('Are you sure you want to reset the database for "%s"? (y/[n]): ' % (config.ROOT_DIR))
if answer == 'y':
	ds.theDataStore = ds.DataStore(redisDbURL=config.REDIS_URL)
	ds.theDataStore.deleteAll()
	print('Database reset.')
else:
	print('Database not reset.')