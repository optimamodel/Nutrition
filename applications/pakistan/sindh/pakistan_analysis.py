import sys
sys.path.append(
    'C:/Users/debra.tenbrink/Documents/GitHub/Nutrition/')  # I assume this is where you'll be running it from?
from nutrition.project import Project
from nutrition.optimization import Optim
from nutrition.scenarios import Scen
from nutrition.results import write_results
from nutrition.utils import run_parallel
from functools import partial
from nutrition import utils
from nutrition.scenarios import Scen
import sciris as sc


def parallel_optim(region, path=None):
    p = Project('Sindh')

    p.load_data(inputspath=path + region + '_input.xlsx', name=region, time_trend=False)

    age_labels = p.models[region].pops[0].popSizes.keys()
    pop_size_tot = 0
    for a in age_labels: # get total number of stunted and wasted children for objective weights
        pop_size_tot += p.models[region].pops[0].popSizes[a]
        # stunt = p.models[region].pops[0].popSizes[a] * (p.models[region].pops[0].stunting_dist[a]['Moderate'] +
        #                                         p.models[region].pops[0].stunting_dist[a]['High'])
        # wast = p.models[region].pops[0].popSizes[a] * (p.models[region].pops[0].wasting_dist[a]['MAM'] +
        #                                                 p.models[region].pops[0].wasting_dist[a]['SAM'])

    ## define custom optimization
    kwargs = {'name': region,
              'mults': [1],
              'model_name': region,
              'weights': sc.odict({'Minimize the number of child deaths': 11/11,
                                   #'Minimize the prevalence of wasting in children': pop_size_tot,
                                   #'Minimize the prevalence of stunting in children': pop_size_tot}),
                                   #'thrive': 1,
                                   #'Minimize the total number of wasted children under 5': 1,
                                   #'Minimize the total number of stunted children under 5': 1}),
                                    'Minimize the number of stunted children': 1,
                                    'Minimize the number of wasted children': 1}),
                            # The available programs need to be put below, I just filled it with common ones
              'prog_set': ['Balanced energy-protein supplementation', 'Cash transfers',
                           'IFA fortification of wheat flour',
                           'IYCF 1', 'IYCF 2', 'IYCF 3', 'IFAS for pregnant women (community)',
                           'IFAS for pregnant women (health facility)', 'Lipid-based nutrition supplements',
                           'Management of MAM',
                           'Multiple micronutrient supplementation', 'Micronutrient powders', 'Kangaroo mother care',
                           'Treatment of SAM', 'Vitamin A supplementation',
                           'Zinc for treatment + ORS', 'Iron and iodine fortification of salt'],
              'fix_curr': False,
              'add_funds': 0
              }

    p.add_optims(Optim(**kwargs))
    results = p.run_optim(maxiter=50, swarmsize=50, maxtime=500, parallel=False)

    return (p)


input_path = 'Databooks/'
output_path = 'Outputs/'

region_list = ['SUJAWAL', 'THATTA', 'JACOBABAD',
                  'KASHMOR', 'SHIKARPUR', 'LARKANA', 'KAMBAR SHAHDAD KOT', 'SUKKUR',
                  'GHOTKI', 'KHAIRPUR', 'NAUSHAHRO FEROZE', 'SHAHEED BENAZIRABAD', 'DADU', 'JAMSHORO', 'HYDERABAD',
                  'TANDO ALLAHYAR','TANDO MUHAMMAD KHAN', 'MATIARI', 'BADIN', 'SANGHAR', 'MIRPUR KHAS', 'UMER KOT',
                  'THARPARKAR', 'KARACHI WEST', 'MALIR', 'KARACHI SOUTH', 'KARACHI EAST', 'KARACHI CENTRAL', 'KORANGI']

if __name__ == '__main__':

    # p = Project('Sindh')
    # region = region_list[0]
    # p.load_data(inputspath=input_path + region + '_input.xlsx', name=region, time_trend=False)
    # kwargs = {'name': region,
    #           'model_name': region,
    #           'scen_type': 'coverage',
    #           'progvals': sc.odict({'Management of MAM': [0.9, 0.95]})}
    # kwargs2 = {'name': 'baseline',
    #           'model_name': region,
    #           'scen_type': 'coverage',
    #           'progvals': sc.odict()}
    # p.add_scens(Scen(**kwargs))
    # p.add_scens(Scen(**kwargs2))
    # p.run_scens()
    # p.plot(toplot=['prevs'])


    run_optim = partial(parallel_optim, path=input_path)
    results = []
    proj_list = run_parallel(run_optim, region_list) #num_procs=4)
    # len(region_list))
    for p in proj_list:
        for res in p.results:
            for scenres in p.results[res]:
                if scenres.name == 'Baseline':
                    scenres.name = scenres.model_name + ' ' + scenres.name
                else:
                    scenres.name = scenres.model_name
                results.append(scenres)

    write_results(results, filename=output_path + '20200910_Sindh_11/11.xlsx')
