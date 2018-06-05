#!/usr/bin/env python

'''
Small script to reset the user database -- WARNING, deletes everything!!!

Duplicate of hptool/bin/reset_database.py

Version: 2018jun04
'''

import sciris.web as sw
import nutrition as on

answer = raw_input('Are you sure you want to reset the database for "%s"? (y/[n]): ' % (on.webapp.config.CLIENT_DIR))
if answer == 'y':
	theDataStore = sw.DataStore(redis_db_URL=on.webapp.config.REDIS_URL)
	theDataStore.delete_all()
	print('Database reset.')
else:
	print('Database not reset.')