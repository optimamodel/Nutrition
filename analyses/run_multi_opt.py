from nutrition.optimization import Optim
from nutrition.scenarios import Scen
from nutrition.results import write_results
from nutrition.utils import run_parallel
from functools import partial
from nutrition.project import Project
import os
import sciris as sc



def parallel_optim_stunting(region, path=None):
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=PendingDeprecationWarning)

    p = Project('WHA optimisation')
    p.load_data(inputspath=path + region + '_input.xlsx', name=region, time_trend=True)

    age_labels = p.models[region].pops[0].popSizes.keys()
    pop_size_tot = 0
    for a in age_labels:  # get total number of stunted and wasted children for objective weights
        pop_size_tot += p.models[region].pops[0].popSizes[a]
    ## define custom optimization
    kwargs = {'name': region,
              'mults': [0.7,0.85,1.0],
              'model_name': region,
              'weights': sc.odict({'Minimize the number of child deaths': 1,
                                   'Minimize the prevalence of stunting in children': pop_size_tot}),
              'prog_set': ['Balanced energy-protein supplementation', 'IYCF 1', 'IYCF 2',
                           'Kangaroo mother care', 'Public provision of complementary foods','Vitamin A supplementation',
                           'Zinc for treatment + ORS'],
              'fix_curr': False,
              'add_funds': 0
              }

    p.add_optims(Optim(**kwargs))
    results = p.run_optim(maxiter=25, swarmsize=25, maxtime=500, parallel=False)

    return(p)


def parallel_optim_wasting(region, path=None):
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=PendingDeprecationWarning)

    p = Project('WHA optimisation')
    p.load_data(inputspath=path + region + '_input.xlsx', name=region, time_trend=True)

    age_labels = p.models[region].pops[0].popSizes.keys()
    pop_size_tot = 0
    for a in age_labels:  # get total number of stunted and wasted children for objective weights
        pop_size_tot += p.models[region].pops[0].popSizes[a]
    ## define custom optimization
    kwargs = {'name': region,
              'mults': [0.7,0.85,1.0],
              'model_name': region,
              'weights': sc.odict({'Minimize the number of child deaths': 1,
                                   'Minimize the prevalence of wasting in children': pop_size_tot,
                                   'Minimize the prevalence of SAM in children': pop_size_tot}),
              'prog_set': ['Management of MAM', 'Treatment of SAM'],
              'fix_curr': False,
              'add_funds': 0
              }

    p.add_optims(Optim(**kwargs))
    results = p.run_optim(maxiter=25, swarmsize=25, maxtime=500, parallel=False)

    return(p)

def parallel_optim_anaemia(region, path=None):
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=PendingDeprecationWarning)

    p = Project('WHA optimisation')
    p.load_data(inputspath=path + region + '_input.xlsx', name=region, time_trend=True)

    total_PW = sum(p.models[region].pops[1].popSizes)
    total_non_PW = sum(p.models[region].pops[2].popSizes)

    ## define custom optimization
    kwargs = {'name': region,
              'mults': [0.7,0.85,1.0],
              'model_name': region,
              'weights': sc.odict({'Minimize the number of child deaths': 1,
                                   'Minimize the prevalence of anaemia in pregnant women': total_PW,
                                   'Minimize the prevalence of anaemia in non-pregnant women': total_non_PW}),
              'prog_set': ['IFAS (community)','IFAS (health facility)',
                           'IFAS for pregnant women (community)',
                           'IFAS for pregnant women (health facility)',
                           'Long-lasting insecticide-treated bednets', 'IPTp',
                           'Multiple micronutrient supplementation'],
              'fix_curr': False,
              'add_funds': 0
              }

    p.add_optims(Optim(**kwargs))
    results = p.run_optim(maxiter=25, swarmsize=25, maxtime=500, parallel=False)

    return(p)


#
country_list = ['Afghanistan', 'Albania', 'Algeria', 'Angola', 'Armenia', 'Bangladesh', 'Belarus',
                'Belize', 'Benin', 'Bhutan', 'Botswana', 'Burkina Faso', 'Burundi', 'Cambodia',
                'Cameroon', 'Central African Republic', 'Chad', 'Colombia', 'Comoros', 'Congo', 'Cuba',
                'Democratic Republic of the Congo',
                'Dominican Republic', 'Egypt',
                'Ethiopia', 'Gambia, The', 'Georgia', 'Ghana', 'Guinea',
                'Haiti', 'India', 'Iraq', 'Jordan', 'Kazakhstan', 'Kenya', 'Kyrgyzstan', 'Laos', 'Lesotho',
                'Malawi', 'Maldives', 'Mali', 'Mauritania', 'Mongolia', 'Montenegro', 'Mozambique', 'Myanmar', 'Nepal', 'Nigeria',
                'North Korea', 'Pakistan', 'Papua New Guinea', 'Sierra Leone', 'Paraguay','Peru', 'Philippines', 'Senegal', 'South Africa', 'Sri Lanka',
                'Tajikistan', 'Tanzania', 'Thailand', 'Timor-Leste', 'Tunisia', 'Turkmenistan',
                'Uganda', 'Zambia', 'Zimbabwe']


dirname = os.path.dirname(__file__)
input_path = dirname + '/inputs/'
output_path = dirname + '/outputs/'
n_processors = 4

if __name__ == '__main__':

    run_optim_stunting = partial(parallel_optim_stunting, path=input_path)
    run_optim_wasting = partial(parallel_optim_wasting, path=input_path)
    run_optim_anaemia = partial(parallel_optim_anaemia, path=input_path)
    results = []
    proj_list_stunting = run_parallel(run_optim_stunting, country_list, num_procs=n_processors)
    proj_list_wasting = run_parallel(run_optim_wasting, country_list, num_procs=n_processors)
    proj_list_anaemia = run_parallel(run_optim_anaemia, country_list, num_procs=n_processors)

    for p in proj_list_stunting:
        for res in p.results:
            for scenres in p.results[res]:
                if scenres.name == 'Baseline':
                    scenres.name = scenres.model_name + ' ' + scenres.name
                else:
                    scenres.name = scenres.model_name + ' Optimized ' + str(scenres.mult)+ 'x'
                results.append(scenres)

    # write_results(results, filename=output_path + 'test.xlsx')


## Get uppoer and lower bounds
    p_bounds = Project('WHA optimisation bounds')
    optim_budgets = sc.odict()
    for q in range(len(proj_list_stunting)): # loop through countries
        country = proj_list_stunting[q].results.keys()[0]
        int_list_stunting = proj_list_stunting[q].results[0][1].programs.keys()
        int_list_wasting = proj_list_wasting[q].results[0][1].programs.keys()
        int_list_anaemia = proj_list_anaemia[q].results[0][1].programs.keys()
        optim_budgets[country] = sc.odict()

        p_bounds.load_data(inputspath=input_path + country + '_input.xlsx', name=country + '_point', time_trend=True)
        p_bounds.load_data(inputspath=input_path + '' + country + '_input.xlsx', name=country + '_LB',time_trend=True)
        p_bounds.load_data(inputspath=input_path + '' + country + '_input.xlsx', name=country + '_UB',time_trend=True)

        for j in range(len(proj_list_stunting[q].results[0])): # number of scenarios
            scen_name = proj_list_stunting[q].results[0][j].name
            optim_budgets[country][scen_name] = sc.odict()
            for i in int_list_stunting:
                optim_budgets[country][scen_name][i] = proj_list_stunting[q].results[0][j].programs[i].annual_spend[1:]
            for i in int_list_wasting:
                optim_budgets[country][scen_name][i] = proj_list_wasting[q].results[0][j].programs[i].annual_spend[1:]
            for i in int_list_anaemia:
                optim_budgets[country][scen_name][i] = proj_list_anaemia[q].results[0][j].programs[i].annual_spend[1:]

            optim_budgets[country][scen_name] = {k: optim_budgets[country][scen_name][k] for k in optim_budgets[country][scen_name].keys()
                                        if k not in {'country_name', 'Excess budget not allocated'}}


            kwargs = {'name': scen_name + ' point',
                      'model_name': country + '_point',
                      'scen_type': 'budget',
                      'progvals': optim_budgets[country][scen_name]}

            p_bounds.add_scens(Scen(**kwargs))

            kwargs = {'name': scen_name + ' LB',
                      'model_name': country + '_LB',
                      'scen_type': 'budget',
                      'progvals': optim_budgets[country][scen_name]}
            p_bounds.add_scens(Scen(**kwargs))

            kwargs = {'name': scen_name + ' UB',
                      'model_name': country + '_UB',
                      'scen_type': 'budget',
                      'progvals': optim_budgets[country][scen_name]}
            p_bounds.add_scens(Scen(**kwargs))

    p_bounds.run_scens()

    write_results(p_bounds.results['scens'], filename=output_path + 'test_bounds.xlsx')

