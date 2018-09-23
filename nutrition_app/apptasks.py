"""
apptasks.py -- The Celery tasks module for this webapp
    
Last update: 2018sep23
"""

import sys
import scirisweb as sw
from . import rpcs
from . import config
import matplotlib.pyplot as ppl
ppl.switch_backend(config.MATPLOTLIB_BACKEND)


print('')
print('#########################################')
print('Starting Cascade Analysis Tools Celery...')
print('#########################################')

# Process arguments
for i,arg in enumerate(sys.argv[1:]):
    try:
        if arg.find('=')>0:
            k = arg.split("=")[0]
            v = arg.split("=")[1]
            K = k.upper()
            if hasattr(config, K):
                setattr(config, K, v)
                print('Including kwarg: "%s" = %s' % (K,v))
                del sys.argv[i]
            else:
                print('Skipping attribute "%s" = %s, not found' % (K,v))
    except Exception as E:
        errormsg = 'Failed to parse argument key="%s", value="%s": %s' % (K, v, str(E))
        raise Exception(errormsg)

# Globals
task_func_dict = {} # Dictionary to hold all of the registered task functions in this module.
async_task = sw.taskwrapper(task_func_dict) # Task function registration decorator created using call to taskwrapper().
celery_instance = sw.make_celery(config=config) # Create the Celery instance for this module.


@async_task
def run_optim(project_id, cache_id, optim_name=None, runtype=None):
    # Load the projects from the DataStore.
    if runtype is None: runtype = 'full'
    print('Running %s optimization...' % runtype)
    datastore = sw.get_datastore(config=config)
    proj = datastore.loadblob(uid=project_id, objtype='project', die=True) # WARNING, rpcs.load_project() cause(d) crash
    if runtype == 'test': results = proj.run_optim(key=optim_name, dosave=False, parallel=False, maxiter=5, swarmsize=5, maxtime=5)
    else:                 results = proj.run_optim(key=optim_name, dosave=False, parallel=False)
    newproj = datastore.loadblob(uid=project_id, objtype='project', die=True)
    newproj.results[cache_id] = results
    newproj = rpcs.cache_results(newproj) # WARNING, causes crash
    key = datastore.saveblob(uid=project_id, objtype='project', obj=newproj)
    return key

# Add the asynchronous task functions in this module to the tasks.py module so run_task() can call them.
sw.add_task_funcs(task_func_dict)