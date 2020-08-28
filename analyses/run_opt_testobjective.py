from nutrition.optimization import Optim
from nutrition.scenarios import Scen
from nutrition.results import write_results
from nutrition.utils import run_parallel
from functools import partial
from nutrition.project import Project
import os
import sciris as sc



def parallel_optim1(region, path=None):
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
              'mults': [1.0],
              'model_name': region,
              'weights': sc.odict({'Minimize the number of child deaths': 0,
                                   'thrive': 1}),
              'prog_set': ['Balanced energy-protein supplementation', 'Cash transfers',
                             'IYCF 1', 'IYCF 2', 'Kangaroo mother care',
                             'Public provision of complementary foods', 'Vitamin A supplementation',
                             'Management of MAM', 'Treatment of SAM',
                             'IFAS (community)', 'IFAS for pregnant women (community)',
                             'Oral rehydration salts', 'Zinc for treatment + ORS', 'IPTp',
                             'Multiple micronutrient supplementation'],
              'fix_curr': False,
              'add_funds': 0
              }

    p.add_optims(Optim(**kwargs))
    results = p.run_optim(maxiter=25, swarmsize=25, maxtime=500, parallel=False)
    # results = p.run_optim(maxiter=2, swarmsize=2, maxtime=5, parallel=False)

    return(p)


def parallel_optim2(region, path=None):
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
              'mults': [1.0],
              'model_name': region,
              'weights': sc.odict({'Minimize the number of child deaths': 1,
                                   'thrive': 1}),
              'prog_set': ['Balanced energy-protein supplementation', 'Cash transfers',
                             'IYCF 1', 'IYCF 2', 'Kangaroo mother care',
                             'Public provision of complementary foods', 'Vitamin A supplementation',
                             'Management of MAM', 'Treatment of SAM',
                             'IFAS (community)', 'IFAS for pregnant women (community)',
                             'Oral rehydration salts', 'Zinc for treatment + ORS', 'IPTp',
                             'Multiple micronutrient supplementation'],
              'fix_curr': False,
              'add_funds': 0
              }

    p.add_optims(Optim(**kwargs))
    results = p.run_optim(maxiter=25, swarmsize=25, maxtime=500, parallel=False)
    # results = p.run_optim(maxiter=2, swarmsize=2, maxtime=5, parallel=False)

    return(p)

def parallel_optim3(region, path=None):
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=PendingDeprecationWarning)

    p = Project('WHA optimisation')
    p.load_data(inputspath=path + region + '_input.xlsx', name=region, time_trend=True)

    total_PW = sum(p.models[region].pops[1].popSizes)
    total_non_PW = sum(p.models[region].pops[2].popSizes)

    ## define custom optimization
    kwargs = {'name': region,
              'mults': [1.0],
              'model_name': region,
              'weights': sc.odict({'Minimize the number of child deaths': 5,
                                   'thrive': 1}),
              'prog_set': ['Balanced energy-protein supplementation', 'Cash transfers',
                             'IYCF 1', 'IYCF 2', 'Kangaroo mother care',
                             'Public provision of complementary foods', 'Vitamin A supplementation',
                             'Management of MAM', 'Treatment of SAM',
                             'IFAS (community)', 'IFAS for pregnant women (community)',
                             'Oral rehydration salts', 'Zinc for treatment + ORS', 'IPTp',
                             'Multiple micronutrient supplementation'],
              'fix_curr': False,
              'add_funds': 0
              }

    p.add_optims(Optim(**kwargs))
    results = p.run_optim(maxiter=25, swarmsize=25, maxtime=500, parallel=False)
    # results = p.run_optim(maxiter=2, swarmsize=2, maxtime=5, parallel=False)

    return(p)


def parallel_optim4(region, path=None):
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=PendingDeprecationWarning)

    p = Project('WHA optimisation')
    p.load_data(inputspath=path + region + '_input.xlsx', name=region, time_trend=True)

    total_PW = sum(p.models[region].pops[1].popSizes)
    total_non_PW = sum(p.models[region].pops[2].popSizes)

    ## define custom optimization
    kwargs = {'name': region,
              'mults': [1.0],
              'model_name': region,
              'weights': sc.odict({'Minimize the number of child deaths': 10,
                                   'thrive': 1}),
              'prog_set': ['Balanced energy-protein supplementation', 'Cash transfers',
                             'IYCF 1', 'IYCF 2', 'Kangaroo mother care',
                             'Public provision of complementary foods', 'Vitamin A supplementation',
                             'Management of MAM', 'Treatment of SAM',
                             'IFAS (community)', 'IFAS for pregnant women (community)',
                             'Oral rehydration salts', 'Zinc for treatment + ORS', 'IPTp',
                             'Multiple micronutrient supplementation'],
              'fix_curr': False,
              'add_funds': 0
              }

    p.add_optims(Optim(**kwargs))
    results = p.run_optim(maxiter=25, swarmsize=25, maxtime=500, parallel=False)
    # results = p.run_optim(maxiter=2, swarmsize=2, maxtime=5, parallel=False)

    return(p)

def parallel_optim5(region, path=None):
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=PendingDeprecationWarning)

    p = Project('WHA optimisation')
    p.load_data(inputspath=path + region + '_input.xlsx', name=region, time_trend=True)

    total_PW = sum(p.models[region].pops[1].popSizes)
    total_non_PW = sum(p.models[region].pops[2].popSizes)

    ## define custom optimization
    kwargs = {'name': region,
              'mults': [1.0],
              'model_name': region,
              'weights': sc.odict({'Minimize the number of child deaths': 1,
                                   'thrive': 0}),
              'prog_set': ['Balanced energy-protein supplementation', 'Cash transfers',
                             'IYCF 1', 'IYCF 2', 'Kangaroo mother care',
                             'Public provision of complementary foods', 'Vitamin A supplementation',
                             'Management of MAM', 'Treatment of SAM',
                             'IFAS (community)', 'IFAS for pregnant women (community)',
                             'Oral rehydration salts', 'Zinc for treatment + ORS', 'IPTp',
                             'Multiple micronutrient supplementation'],
              'fix_curr': False,
              'add_funds': 0
              }

    p.add_optims(Optim(**kwargs))
    results = p.run_optim(maxiter=25, swarmsize=25, maxtime=500, parallel=False)
    # results = p.run_optim(maxiter=2, swarmsize=2, maxtime=5, parallel=False)

    return(p)
#
country_list = ['Afghanistan', 'Albania', 'Algeria', 'Angola', 'Armenia', 'Azerbaijan', 'Bangladesh',
                'Belarus', 'Belize', 'Benin', 'Bhutan', 'Bolivia', 'Bosnia and Herzegovina', 'Botswana',
                'Brazil', 'Burkina Faso', 'Burundi', 'Cambodia', 'Cameroon', 'Cape Verde', 'Central African Republic',
                'Chad', 'Colombia', 'Comoros', 'Congo', 'Costa Rica', 'Cote d\'Ivoire', 'Cuba', 'Democratic Republic of the Congo',
                'Djibouti', 'Dominican Republic', 'Ecuador', 'Egypt', 'El Salvador', 'Equatorial Guinea', 'Ethiopia', 'Gabon',
                'Gambia, The', 'Georgia', 'Ghana', 'Guatemala', 'Guinea', 'Guinea-Bissau', 'Guyana', 'Haiti',
                'Honduras', 'India', 'Indonesia', 'Iraq', 'Jamaica', 'Jordan', 'Kazakhstan', 'Kenya',
                'Kyrgyzstan', 'Laos', 'Lesotho', 'Liberia', 'Macedonia', 'Madagascar', 'Malawi',
                'Maldives', 'Mali', 'Mauritania', 'Moldova', 'Mongolia', 'Montenegro', 'Morocco', 'Mozambique',
                'Myanmar', 'Namibia', 'Nepal', 'Nicaragua', 'Niger', 'Nigeria', 'North Korea', 'Pakistan', 'Papua New Guinea',
                'Paraguay', 'Peru', 'Philippines', 'Rwanda', 'Saint Lucia', 'Samoa', 'Sao Tome and Principe', 'Senegal',
                'Serbia', 'Sierra Leone', 'Solomon Islands', 'Somalia', 'South Africa', 'South Sudan', 'Sri Lanka',
                'Sudan', 'Suriname', 'Syria', 'Tajikistan', 'Tanzania', 'Thailand', 'Timor-Leste', 'Togo',
                'Tonga', 'Tunisia', 'Turkey', 'Turkmenistan', 'Uganda', 'Ukraine', 'Uzbekistan', 'Vanuatu',
                'Venezuela', 'Vietnam', 'Yemen', 'Zambia', 'Zimbabwe']



dirname = os.path.dirname(__file__)
input_path = dirname + '/inputs/Medium 2020 base/'
output_path = dirname + '/outputs/'
n_processors = 4
bounds = False

if __name__ == '__main__':

    run_optim1 = partial(parallel_optim1, path=input_path)
    run_optim2 = partial(parallel_optim2, path=input_path)
    run_optim3 = partial(parallel_optim3, path=input_path)
    run_optim4 = partial(parallel_optim4, path=input_path)
    run_optim5 = partial(parallel_optim5, path=input_path)
    results = []
    proj_list1 = run_parallel(run_optim1, country_list, num_procs=n_processors)
    proj_list2 = run_parallel(run_optim2, country_list, num_procs=n_processors)
    proj_list3 = run_parallel(run_optim3, country_list, num_procs=n_processors)
    proj_list4 = run_parallel(run_optim4, country_list, num_procs=n_processors)
    proj_list5 = run_parallel(run_optim5, country_list, num_procs=n_processors)

    for p in proj_list1:
        for res in p.results:
            for scenres in p.results[res]:
                if scenres.name == 'Baseline':
                    scenres.name = scenres.model_name + ' ' + scenres.name
                else:
                    scenres.name = scenres.model_name + ' Optimized obj1 ' + str(scenres.mult)+ 'x'
                results.append(scenres)
    for p in proj_list2:
        for res in p.results:
            for scenres in p.results[res]:
                if scenres.name != 'Baseline':
                    scenres.name = scenres.model_name + ' Optimized obj2 ' + str(scenres.mult)+ 'x'
                    results.append(scenres)
    for p in proj_list3:
        for res in p.results:
            for scenres in p.results[res]:
                if scenres.name != 'Baseline':
                    scenres.name = scenres.model_name + ' Optimized obj3 ' + str(scenres.mult)+ 'x'
                    results.append(scenres)
    for p in proj_list4:
        for res in p.results:
            for scenres in p.results[res]:
                if scenres.name != 'Baseline':
                    scenres.name = scenres.model_name + ' Optimized obj4 ' + str(scenres.mult)+ 'x'
                    results.append(scenres)
    for p in proj_list5:
        for res in p.results:
            for scenres in p.results[res]:
                if scenres.name != 'Baseline':
                    scenres.name = scenres.model_name + ' Optimized obj5 ' + str(scenres.mult)+ 'x'
                    results.append(scenres)

    # write_results(results, filename=output_path + 'test.xlsx')


    if bounds:
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
    else:
        write_results(results, filename=output_path + 'test.xlsx')


