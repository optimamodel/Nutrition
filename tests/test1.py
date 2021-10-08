import sys

sys.path.append('C:/Users/debra.tenbrink/Documents/GitHub/Nutrition/')  # I assume this is where you'll be running it from?
from nutrition.project import Project
from nutrition.optimization import Optim
from nutrition.results import write_results
from nutrition.utils import run_parallel
from functools import partial
from nutrition import utils
from nutrition.scenarios import Scen
import sciris as sc


def parallel_optim(region, path=None, ramping=True):
    p = Project('Cameroon')

    p.load_data(inputspath=path + region + '_input.xlsx', name=region)

    ## define custom optimization
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

    p.add_optims(Optim(**kwargs))
    p.run_optim(maxiter=50, swarmsize=0, maxtime=500, parallel=False, ramping=ramping)

    return (p)


input_path = 'Databooks/new_format/'
output_path = 'Outputs/'
ramping = True

#region_list = ['ADAMAOUA', 'CENTRE', 'DOUALA', 'EAST', 'FAR NORTH', 'LITTORAL', 'NORTH',
#               'NORTHWEST', 'WEST', 'SOUTH', 'SOUTHWEST', 'YAOUNDE']
region_list = ['DOUALA', 'WEST']

if __name__ == '__main__':

    run_optim = partial(parallel_optim, path=input_path, ramping=ramping)
    results = []
    proj_list = run_parallel(run_optim, region_list, num_procs=3)
    # len(region_list))
    for p in proj_list:
        for res in p.results:
            for scenres in p.results[res]:
                if scenres.name == 'Baseline':
                    scenres.name = scenres.model_name + ' ' + scenres.name
                else:
                    scenres.name = scenres.model_name
                results.append(scenres)

    write_results(results, filename=output_path + 'test1.xlsx')
