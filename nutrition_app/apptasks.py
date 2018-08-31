"""
apptasks.py -- The Celery tasks module for this webapp
    
Last update: 7/31/18 (gchadder3)
"""

#
# Imports
#

import config
import scirisweb as sw
import projects as prj
import mpld3
from . import rpcs
import matplotlib.pyplot as ppl
ppl.switch_backend(config.MATPLOTLIB_BACKEND)


#
# Globals
#

task_func_dict = {} # Dictionary to hold all of the registered task functions in this module.
register_async_task = sw.make_async_tag(task_func_dict) # Task function registration decorator created using call to make_register_async_task().
celery_instance = sw.make_celery_instance(config=config) # Create the Celery instance for this module.

# This is needed in Windows using celery Version 3.1.25 in order for the
# add_task_funcs() function below to successfully add the asynchronous task 
# functions defined in this module to tasks.py.  Why these lines enable this 
# I do not understand.
#@celery_instance.task
#def dummy_result():
#    return 'here be dummy result'

@register_async_task
def run_optim(project_id, optim_name=None, online=True):
    # Load the projects from the DataStore.
    print('Running optimization...')
    if online:
        prj.apptasks_load_projects(config)
        proj = rpcs.load_project(project_id, raise_exception=True)
    else:
        proj = project_id
    
    proj.results.clear() # Remove any existing results
    proj.run_optim(key=optim_name, parallel=False)
    figs = proj.plot(key=optim_name, optim=True) # Only plot allocation
    graphs = []
    for f,fig in enumerate(figs.values()):
        for ax in fig.get_axes():
            ax.set_facecolor('none')
        graph_dict = mpld3.fig_to_dict(fig)
        graphs.append(graph_dict)
        print('Converted figure %s of %s' % (f+1, len(figs)))
    
    print('Saving project...')
    rpcs.save_project(proj) 
    
    # Return the graphs.
    return {'graphs': graphs}

# Add the asynchronous task functions in this module to the tasks.py module so run_task() can call them.
sw.add_task_funcs(task_func_dict)