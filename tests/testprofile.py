#!/usr/bin/env python
"""
Profile the nutrition model.
"""

#####################################################################################################
#%% Imports and settings
import pylab as pl
import nutrition.ui as nu
import sciris.core as sc
try:
    from line_profiler import LineProfiler
except: 
    errormsg = 'ERROR: You need to install line_profiler! "conda install line-profiler" or something like that'
    raise Exception(errormsg)


#####################################################################################################
#%% Preliminaries -- do a CPU benchmark
def cpubenchmark(repeats=int(1e6)):
    starttime = sc.tic()
    tmp = [0+tmp for tmp in range(repeats)]
    timediff = sc.toc(starttime, 'out')
    performance = 1.0/timediff
    return performance
   
# Calculate performance
performance1 = cpubenchmark()
pl.pause(0.5)
performance2 = cpubenchmark()
CPUperformance = sum([performance1, performance2])/2. # Find average of before and after

# Calculate initialization
start = sc.tic()
P = nu.demo()
initialization = sc.toc(start, 'out')

# Calculate model un
start = sc.tic()
P.run_scens()
model_run = sc.toc(start, 'out')


#####################################################################################################
#%% Profiling
'''
Examples:
    nu.demo
    P.run_scens
    P.scens[0].run_scen
    P.scens[0].model.run_sim
    P.scens[0].model._apply_prog_covs
    P.scens[0].model._update_pop_mort
    P.scens[0].model.pops[0].update_mortality
    P.scens[0].model.integrate
    P.scens[0].model._move_children
    P.scens[0].model._apply_child_mort
'''
functiontoprofile = 'P.scens[0].model.pops[0].update_mortality'
def profile():
    print('Profiling %s...' % functiontoprofile)

    def do_profile(follow=None):
      def inner(func):
          def profiled_func(*args, **kwargs):
              try:
                  profiler = LineProfiler()
                  profiler.add_function(func)
                  for f in follow:
                      profiler.add_function(f)
                  profiler.enable_by_count()
                  return func(*args, **kwargs)
              finally:
                  profiler.print_stats()
          return profiled_func
      return inner
    
    
    
    @do_profile(follow=[eval(functiontoprofile)]) # Add decorator to function being profiled
    def runwrapper(): 
        P.run_scens()
    runwrapper()
    
    print('Done.')

profile()

print("CPU benchmark:%0.2f million flops" % (CPUperformance))
print('Model initialization: %s s' % initialization)
print('Model runtime: %s s' % model_run)
