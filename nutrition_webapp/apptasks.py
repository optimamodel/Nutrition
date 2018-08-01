"""
apptasks.py -- The Celery tasks module for this webapp
    
Last update: 7/31/18 (gchadder3)
"""

#
# Imports
#

import time
import config
import matplotlib.pyplot as ppl
ppl.switch_backend(config.MATPLOTLIB_BACKEND)
from sciris.weblib.tasks import make_celery_instance, add_task_funcs, make_register_async_task
import projects as prj
from rpcs import load_project, save_project
import mpld3

#
# Globals
#

# Dictionary to hold all of the registered task functions in this module.
task_func_dict = {}

# Task function registration decorator created using call to 
# make_register_async_task().
register_async_task = make_register_async_task(task_func_dict)

# Create the Celery instance for this module.
celery_instance = make_celery_instance(config=config)

# This is needed in Windows using celery Version 3.1.25 in order for the
# add_task_funcs() function below to successfully add the asynchronous task 
# functions defined in this module to tasks.py.  Why these lines enable this 
# I do not understand.
#@celery_instance.task
#def dummy_result():
#    return 'here be dummy result'

@register_async_task
def run_optim(project_id, optim_name):
    # Load the projects from the DataStore.
    prj.apptasks_load_projects(config)
    
    print('Running optimization...')
    proj = load_project(project_id, raise_exception=True)
    
    print('Thinking...')
    import nutrition.ui as nu
    p = nu.demo()
    
    a = proj.optim()
    b = p.optim()
    
    for attr in a.__dict__.keys():
        print('COMPARING %s' % attr)
        a_attr = getattr(a, attr)
        b_attr = getattr(b, attr)
        print('A: %s' % a_attr)
        print('B: %s' % b_attr)
        if a_attr == b_attr:
            print('(they match)')
        else:
            print('THEY DO NOT MAAATCH')
    
    proj.run_optims(keys=[optim_name], parallel=False)
    figs = proj.plot(toplot=['alloc']) # Only plot allocation
    graphs = []
    for f,fig in enumerate(figs.values()):
        for ax in fig.get_axes():
            ax.set_facecolor('none')
        graph_dict = mpld3.fig_to_dict(fig)
        graphs.append(graph_dict)
        print('Converted figure %s of %s' % (f+1, len(figs)))
    
    print('Saving project...')
    save_project(proj) 
    
    # Return the graphs.
    return {'graphs': graphs}

# Add the asynchronous task functions in this module to the tasks.py module 
# so run_task() can call them.
add_task_funcs(task_func_dict)