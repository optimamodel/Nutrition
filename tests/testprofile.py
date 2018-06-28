#!/usr/bin/env python
"""
Profile the nutrition model.
"""

#%% Imports and settings
import pylab as pl
import nutrition.ui as nu
import sciris.core as sc
try:
    from line_profiler import LineProfiler
except: 
    errormsg = 'ERROR: You need to install line_profiler! "conda install line-profiler" or something like that'
    raise Exception(errormsg)

functiontoprofile = 'model' # Choices are: model, runsim, makesimpars, interp

#%% Preliminaries -- do a CPU benchmark
def cpubenchmark(repeats=int(1e6)):
    starttime = sc.tic()
    tmp = [0+tmp for tmp in range(repeats)]
    timediff = sc.toc(starttime, 'out')
    performance = 1.0/timediff
    return performance
    
performance1 = cpubenchmark()
pl.pause(0.5)
performance2 = cpubenchmark()
CPUperformance = sum([performance1, performance2])/2. # Find average of before and after


############################################################################################################################
#%% Profiling
############################################################################################################################

start = sc.tic()
P = nu.demo()
elapsed = sc.toc(start, 'out')

def profile():
    print('Profiling...')

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
    
    
    
    @do_profile(follow=[nu.demo]) # Add decorator to function being profiled
    def runwrapper(): 
        nu.demo()
    runwrapper()
    
    print('Done.')

profile()

print("CPU benchmark:%0.2f million flops" % (CPUperformance))
print('Model runtime: %s s' % elapsed)

