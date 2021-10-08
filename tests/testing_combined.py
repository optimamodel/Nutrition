""""This script may be used to test running non-optimization
    and optimization scenarios together.
    resampling (boolian): whether to use resampling with multirun or point estimators with single run (defualt: True)
    rampling   (boolian): whether to use ramping function or not
    NOTE: Resampling does not work well (in progress)"""
import nutrition.ui as nu
import sciris as sc
from nutrition.project import Project
from nutrition.optimization import Optim
from nutrition.results import write_results
from nutrition.utils import run_parallel
from functools import partial


input_path = 'Databooks/new_format/'
output_path = 'Outputs/'
region_list = ['DOUALA', 'WEST']
ramping = True

"""" If the model is run for a single run using 'p.run_scens()' then set resampling=False
    to make sure that the default point estimators are used from 
    the databook with out considering any randomness!"""
p1 = nu.Project('eg')
p1.load_data('demo', 'testing', name='eg', resampling=True)

"""Define non-optimization scenarios"""

kwargs1 = {'name':'Treat SAM 100%',
           'model_name': 'eg',
           'scen_type': 'coverage',
            'progvals': sc.odict({'Treatment of SAM': [0.9, 0.5, 0.8]})}

kwargs2 = {'name': 'IYCF at $10 mil',
         'model_name': 'eg',
         'scen_type': 'budget',
           'progvals': sc.odict({'IYCF 1': [1e7, 2e7, 1.5e6, 2.5e7],
                                 'IPTp': [2e7, 2.8e7, 2.8e6, 4.25e7]})}

kwargs3 = {'name': 'IYCF',
           'model_name': 'eg',
           'scen_type': 'coverage',
           'progvals': sc.odict({'IYCF 1': [0.6, 0.2, 0.5, 0.95, 0.8]})}

def parallel_optim(region, path=None, ramping=True):
    """Define optimization scenario"""
    p2 = Project('Cameroon')
    p2.load_data(inputspath=path + region + '_input.xlsx', name=region, resampling=False)

    """Define a custom optimization scenario"""
    
    kwargs = {'name': region,
              'mults': [1],
              'model_name': region,
              'weights': sc.odict({'Minimize the number of child deaths': [1, 0.5],
                                   'thrive': [1, 0.2]}),
              'prog_set': ['Balanced energy-protein supplementation', 'Cash transfers',
                           'IFA fortification of wheat flour',
                           'IYCF 1', 'IYCF 2', 'IFAS for pregnant women (community)',
                           'IFAS for pregnant women (health facility)', 'Lipid-based nutrition supplements',
                           'Multiple micronutrient supplementation', 'Micronutrient powders', 'Kangaroo mother care',
                           'Treatment of SAM', 'Vitamin A supplementation',
                           'Zinc for treatment + ORS', 'Iron and iodine fortification of salt'],
              'fix_curr': False,
              'add_funds': 0
              }

    p2.add_optims(Optim(**kwargs))
    p2.run_optim(maxiter=50, swarmsize=0, maxtime=500, parallel=False, ramping=ramping)
    return (p2)

"""run non optimization scenarios"""
scen_list = nu.make_scens([kwargs1, kwargs2, kwargs3])
p1.add_scens(scen_list)
#p1.run_scens(ramping=ramping) # make sure to set resampling=False
p1.multirun_scens(ramping=ramping)
p1.write_results(filename=output_path + 'non_optimized.xlsx')

"""run optimization scenarios"""
if __name__ == '__main__':

    run_optim = partial(parallel_optim, path=input_path, ramping=ramping)
    results = []
    proj_list = run_parallel(run_optim, region_list, num_procs=3)
    for p in proj_list:
        for res in p.results:
            for scenres in p.results[res]:
                if scenres.name == 'Baseline':
                    scenres.name = scenres.model_name + ' ' + scenres.name
                else:
                    scenres.name = scenres.model_name
                results.append(scenres)
    write_results(results, filename=output_path + 'optimized.xlsx')




