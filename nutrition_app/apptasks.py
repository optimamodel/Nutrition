"""
apptasks.py -- The Celery tasks module for this webapp
    
Last update: 2018sep19
"""

import scirisweb as sw
from . import rpcs
from . import config
import matplotlib.pyplot as ppl
ppl.switch_backend(config.MATPLOTLIB_BACKEND)


#
# Globals
#

task_func_dict = {} # Dictionary to hold all of the registered task functions in this module.
async_task = sw.make_async_tag(task_func_dict) # Task function registration decorator created using call to make_register_async_task().
celery_instance = sw.make_celery_instance(config=config) # Create the Celery instance for this module.

# This is needed in Windows using celery Version 3.1.25 in order for the
# add_task_funcs() function below to successfully add the asynchronous task 
# functions defined in this module to tasks.py.  Why these lines enable this 
# I do not understand.
#@celery_instance.task
#def dummy_result():
#    return 'here be dummy result'

@async_task
def run_optim(project_id, cache_id, optim_name=None):
    # Load the projects from the DataStore.
    print('Running optimization...')

    prj.apptasks_load_projects(config)
    
    proj = rpcs.load_project(project_id, raise_exception=True)
    results = proj.run_optim(key=optim_name, dosave=False, parallel=False)
#    proj.results[cache_id] = results
    rpcs.put_results_cache_entry(cache_id, results, apptasks_call=True)
    print('Saving project...')
    proj = rpcs.load_project(project_id, raise_exception=True)
    proj.results[cache_id] = results
    rpcs.save_project(proj)
    return None

# Add the asynchronous task functions in this module to the tasks.py module so run_task() can call them.
sw.add_task_funcs(task_func_dict)