import sys
from nutrition.project import Project
from nutrition.optimization import Optim
from nutrition.results import write_results
from nutrition.utils import run_parallel
from functools import partial
from nutrition import utils
from nutrition.scenarios import Scen
import sciris as sc

input_path = 'Databooks/new_format/'
output_path = 'Outputs/'

region_list = ['National', 'Highland', 'Northern Mountainous']

nutrition_specific = ['IYCF 1', 'IFAS for pregnant women (health facility)', 'Multiple micronutrient supplementation',
                      'Micronutrient powders', 'Treatment of SAM', 'Vitamin A supplementation',
                      'Zinc for treatment + ORS']

nutrition_all = ['IYCF 1', 'IFAS for pregnant women (health facility)',
                 'IPTp', 'Long-lasting insecticide-treated bednets',
                 'Multiple micronutrient supplementation', 'Micronutrient powders',
                 'Treatment of SAM', 'Vitamin A supplementation', 'Zinc for treatment + ORS']

def parallel_optim(progs, region, path=None, fixed=False, additional=0):
    p = Project('Vietnam')
    p.load_data(inputspath=path + region + '.xlsx', name=region)

    if region == 'National':
        additional *= 10

    kwargs = {'name': region,
              'mults': [1],
              'model_name': region,
              'weights': sc.odict({'thrive': 1}),
              'prog_set': progs,
              'fix_curr': fixed,
              'add_funds': additional
              }

    p.add_optims(Optim(**kwargs))
    results = p.run_optim(maxiter=25, swarmsize=None, maxtime=400, parallel=False)

    return results


if __name__ == '__main__':
    # run optimizations for existing budget

    results = []
    for progs in [nutrition_specific]:
        if progs == nutrition_specific:
            for region_mod in ['_main']:
                run_optim = partial(parallel_optim, progs, path=input_path)
                mod_region_list = [region + region_mod for region in region_list]
                proj_list = run_parallel(run_optim, mod_region_list, num_procs=4)

                for p in proj_list:
                    for scenres in p:
                        if scenres.name == 'Baseline':
                            scenres.name = scenres.model_name + ' limprog baseline'
                        else:
                            scenres.name = scenres.model_name + ' limprog optimal'
                        results.append(scenres)
        else:
            run_optim = partial(parallel_optim, progs, path=input_path)
            mod_region_list = [region + '_combineIYCF' for region in region_list]
            proj_list = run_parallel(run_optim, mod_region_list, num_procs=4)

            for p in proj_list:
                for scenres in p:
                    if scenres.name == 'Baseline':
                        scenres.name = scenres.model_name + ' fullprog baseline'
                    else:
                        scenres.name = scenres.model_name + ' fullprog optimal'
                    results.append(scenres)

    write_results(results, filename=output_path + 'test2.xlsx')

''' Include if adding additional funds
    # run optimizations for fixed existing budget plus additional $1M, $2M, $5M
    for budget in [1e+06, 2e+06, 5e+06]:
        run_optim = partial(parallel_optim, path=input_path, fixed=True, additional=budget)
        results = []
        proj_list = run_parallel(run_optim, region_list, num_procs=4)

        for p in proj_list:
            for scenres in p:
                if scenres.name == 'Baseline':
                    scenres.name = scenres.model_name + ' baseline'
                else:
                    scenres.name = scenres.model_name + ' optimal'
                results.append(scenres)

        write_results(results, filename=output_path + 'Vietnam_20210208' + "{:.0e}".format(budget) + '.xlsx')
'''