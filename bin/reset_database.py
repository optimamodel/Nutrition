#!/usr/bin/env python

'''
Small script to reset the user database -- WARNING, deletes everything!!!

Duplicate of hptool/bin/reset_database.py

Version: 2018jun04
'''

import sciris.web as sw
import hptool as hp

answer = raw_input('Are you sure you want to reset the database for "%s"? (y/[n]): ' % (hp.webapp.config.CLIENT_DIR))
if answer == 'y':
	ds.theDataStore = sw.DataStore(redis_db_URL=hp.webapp.config.REDIS_URL)
	ds.theDataStore.delete_all()
	print('Database reset.')
else:
	print('Database not reset.')