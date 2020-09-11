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
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    prog_list = ['IYCF 1', 'IYCF 2', 'Kangaroo mother care',
                 'Public provision of complementary foods', 'Vitamin A supplementation',
                 'Treatment of SAM',
                 'Lipid-based nutrition supplements']
                 #'IPTp', 'Multiple micronutrient supplementation',
                 #'Management of MAM','Oral rehydration salts', 'Zinc for treatment + ORS',
                 #'Balanced energy-protein supplementation', 'Cash transfers',
                 #'IFAS (community)', 'IFAS for pregnant women (community)'],
    p0 = Project('Budget')
    p0.load_data(inputspath=os.path.dirname(__file__) + '/inputs/Medium 2019 base/' + region + '_input.xlsx', name=region, time_trend=False)
    total_budget_2019 = 0.0
    for prog in prog_list:
        if prog in p0.models[region].prog_info.programs.keys():
            total_budget_2019 += p0.models[region].prog_info.programs[prog].annual_spend[0]


    p = Project('pes 2021 opt')
    p.load_data(inputspath=path + region + '_input.xlsx', name=region, time_trend=False)
    total_budget_2020 = 0.0
    for prog in prog_list:
        if prog in p.models[region].prog_info.programs.keys():
            total_budget_2020 += p.models[region].prog_info.programs[prog].annual_spend[0]

    age_labels = p.models[region].pops[0].popSizes.keys()
    pop_size_tot = 0
    for a in age_labels:  # get total number of stunted and wasted children for objective weights
        pop_size_tot += p.models[region].pops[0].popSizes[a]

    mult = [1.0 * total_budget_2019 / max(1,total_budget_2020)]
    ## define custom optimization
    kwargs = {'name': region,
              'mults': mult,
              'model_name': region,
              'weights': sc.odict({'Minimize the number of child deaths': 1,
                                   'Minimize the prevalence of stunting in children': 0,#pop_size_tot,
                                   'Minimize the total number of stunted children under 5': 0,
                                   'thrive': 1}),
              'prog_set': prog_list,
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
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    prog_list = ['IYCF 1', 'IYCF 2', 'Kangaroo mother care',
                 'Public provision of complementary foods', 'Vitamin A supplementation',
                 'Treatment of SAM',
                 'Lipid-based nutrition supplements']
                 #'IPTp', 'Multiple micronutrient supplementation',
                 #'Management of MAM','Oral rehydration salts', 'Zinc for treatment + ORS',
                 #'Balanced energy-protein supplementation', 'Cash transfers',
                 #'IFAS (community)', 'IFAS for pregnant women (community)'],
    p0 = Project('Budget')
    p0.load_data(
        inputspath=os.path.dirname(__file__) + '/inputs/Medium 2019 base/' + region + '_input.xlsx',
        name=region, time_trend=False)
    total_budget_2019 = 0.0
    for prog in prog_list:
        if prog in p0.models[region].prog_info.programs.keys():
            total_budget_2019 += p0.models[region].prog_info.programs[prog].annual_spend[0]

    p = Project('med 2021 opt')
    p.load_data(inputspath=path + region + '_input.xlsx', name=region, time_trend=False)
    total_budget_2020 = 0.0
    for prog in prog_list:
        if prog in p.models[region].prog_info.programs.keys():
            total_budget_2020 += p.models[region].prog_info.programs[prog].annual_spend[0]
    age_labels = p.models[region].pops[0].popSizes.keys()
    pop_size_tot = 0
    for a in age_labels:  # get total number of stunted and wasted children for objective weights
        pop_size_tot += p.models[region].pops[0].popSizes[a]

    mult = [1.0 * total_budget_2019 / max(1,total_budget_2020)]

    ## define custom optimization
    kwargs = {'name': region,
              'mults': mult,
              'model_name': region,
              'weights': sc.odict({'Minimize the number of child deaths': 1,
                                   'Minimize the prevalence of stunting in children': 0,#pop_size_tot,
                                   'Minimize the total number of stunted children under 5': 0,
                                   'thrive': 1}),
              'prog_set': prog_list,
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
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    prog_list = ['IYCF 1', 'IYCF 2', 'Kangaroo mother care',
                 'Public provision of complementary foods', 'Vitamin A supplementation',
                 'Treatment of SAM',
                 'Lipid-based nutrition supplements']
                 #'IPTp', 'Multiple micronutrient supplementation',
                 #'Management of MAM','Oral rehydration salts', 'Zinc for treatment + ORS',
                 #'Balanced energy-protein supplementation', 'Cash transfers',
                 #'IFAS (community)', 'IFAS for pregnant women (community)'],
    p0 = Project('Budget')
    p0.load_data(
        inputspath=os.path.dirname(__file__) + '/inputs/Medium 2019 base/' + region + '_input.xlsx',
        name=region, time_trend=False)
    total_budget_2019 = 0.0
    for prog in prog_list:
        if prog in p0.models[region].prog_info.programs.keys():
            total_budget_2019 += p0.models[region].prog_info.programs[prog].annual_spend[0]

    p = Project('opt 2021 opt')
    p.load_data(inputspath=path + region + '_input.xlsx', name=region, time_trend=False)
    total_budget_2020 = 0.0
    for prog in prog_list:
        if prog in p.models[region].prog_info.programs.keys():
            total_budget_2020 += p.models[region].prog_info.programs[prog].annual_spend[0]
    age_labels = p.models[region].pops[0].popSizes.keys()
    pop_size_tot = 0
    for a in age_labels:  # get total number of stunted and wasted children for objective weights
        pop_size_tot += p.models[region].pops[0].popSizes[a]

    mult = [1.0 * total_budget_2019 / max(1,total_budget_2020)]

    ## define custom optimization
    kwargs = {'name': region,
              'mults': mult,
              'model_name': region,
              'weights': sc.odict({'Minimize the number of child deaths': 1,
                                   'Minimize the prevalence of stunting in children': 0,#pop_size_tot,
                                   'Minimize the total number of stunted children under 5': 0,
                                   'thrive': 1}),
              'prog_set': prog_list,
              'fix_curr': False,
              'add_funds': 0
              }

    p.add_optims(Optim(**kwargs))
    results = p.run_optim(maxiter=25, swarmsize=25, maxtime=500, parallel=False)
    #results = p.run_optim(maxiter=2, swarmsize=2, maxtime=5, parallel=False)

    return(p)


#
country_list = ['Afghanistan', 'Albania', 'Algeria', 'Angola']#, 'Argentina', 'Armenia', 'Azerbaijan', 'Bangladesh',
                # 'Belarus', 'Belize', 'Benin', 'Bhutan', 'Bolivia', 'Bosnia and Herzegovina', 'Botswana',
                # 'Brazil', 'Burkina Faso', 'Burundi', 'Cambodia', 'Cameroon', 'Cape Verde', 'Central African Republic',
                # 'Chad', 'Colombia', 'Comoros', 'Congo', 'Costa Rica', 'Cote d\'Ivoire', 'Cuba', 'Democratic Republic of the Congo',
                # 'Djibouti', 'Dominican Republic', 'Ecuador', 'Egypt', 'El Salvador', 'Equatorial Guinea', 'Eritrea', 'Ethiopia',
                # 'Eswatini','Gabon', 'Gambia, The', 'Georgia', 'Ghana', 'Guatemala', 'Guinea', 'Guinea-Bissau', 'Guyana', 'Haiti',
                # 'Honduras', 'India', 'Indonesia', 'Iraq', 'Jamaica', 'Jordan', 'Kazakhstan', 'Kenya',
                # 'Kyrgyzstan', 'Laos', 'Lesotho', 'Liberia', 'Macedonia', 'Madagascar', 'Malawi',
                # 'Maldives', 'Mali', 'Mauritania', 'Mexico','Moldova','Mongolia', 'Montenegro', 'Morocco', 'Mozambique',
                # 'Myanmar', 'Namibia', 'Nepal', 'Nicaragua', 'Niger', 'Nigeria', 'North Korea', 'Pakistan', 'Panama', 'Papua New Guinea',
                # 'Paraguay', 'Peru', 'Philippines', 'Rwanda', 'Saint Lucia', 'Samoa', 'Sao Tome and Principe', 'Senegal',
                # 'Serbia', 'Sierra Leone', 'Solomon Islands', 'Somalia', 'South Africa', 'South Sudan', 'Sri Lanka',
                # 'Sudan', 'Suriname', 'Syria', 'Tajikistan', 'Tanzania', 'Thailand', 'Timor-Leste', 'Togo',
                # 'Tonga', 'Tunisia', 'Turkey', 'Turkmenistan', 'Uganda', 'Ukraine', 'Uzbekistan', 'Vanuatu',
                # 'Venezuela', 'Vietnam', 'Yemen', 'Zambia', 'Zimbabwe']

prog_list = ['IYCF 1', 'IYCF 2', 'Kangaroo mother care',
                             'Public provision of complementary foods', 'Vitamin A supplementation',
                             'Treatment of SAM',
                             'Lipid-based nutrition supplements'],
                             #'IPTp', 'Multiple micronutrient supplementation',
                             #'Management of MAM','Oral rehydration salts', 'Zinc for treatment + ORS',
                             #'Balanced energy-protein supplementation', 'Cash transfers',
                             #'IFAS (community)', 'IFAS for pregnant women (community)'],

dirname = os.path.dirname(__file__)
input_path_med = dirname + '/inputs/Medium 2020 base/'
input_path_pes = dirname + '/inputs/Pes 2020 base/'
input_path_opt = dirname + '/inputs/Opt 2020 base/'
input_path_noCOVID = dirname + '/inputs/Medium 2019 base/'

output_path = dirname + '/outputs/'
n_processors = 4
bounds = False

if __name__ == '__main__':

    run_optim1 = partial(parallel_optim1, path=input_path_med)
    run_optim2 = partial(parallel_optim2, path=input_path_pes)
    run_optim3 = partial(parallel_optim3, path=input_path_opt)
    results = []
    proj_list1 = run_parallel(run_optim1, country_list, num_procs=n_processors)
    proj_list2 = run_parallel(run_optim2, country_list, num_procs=n_processors)
    proj_list3 = run_parallel(run_optim3, country_list, num_procs=n_processors)


    b = Project('Baseline2019')
    b_trend = Project('Baseline2019_trend')
    b_counter_med = Project('Baseline2020_med_trend')
    b_counter_pes = Project('Baseline2020_pes_trend')
    b_counter_opt = Project('Baseline2020_opt_trend')

    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
    warnings.filterwarnings("ignore", category=RuntimeWarning)

    for c in country_list:
        region = c
        b.load_data(inputspath=input_path_noCOVID + region + '_input.xlsx', name=region, time_trend=False)
        kwargs = {'name': region,
                  'model_name': region,
                  'scen_type': 'coverage',
                  'progvals': sc.odict({'IYCF 1': [], 'IYCF 2': [], 'Kangaroo mother care': [],
                           'Public provision of complementary foods': [],'Vitamin A supplementation': [],
                           'Lipid-based nutrition supplements': [],
                           'Treatment of SAM': []})}
                           #'Management of MAM': [],'Oral rehydration salts': [], 'Zinc for treatment + ORS': [],
                           #'Balanced energy-protein supplementation': [], 'Cash transfers': [],
                           #'IFAS for pregnant women (community)': [],
                           #'IFAS (community)': [],  'IPTp': [],
                           #'Multiple micronutrient supplementation': []})}
        b.add_scens(Scen(**kwargs))
    b.run_scens()
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
    warnings.filterwarnings("ignore", category=RuntimeWarning)

    for c in country_list:
        region = c
        b_trend.load_data(inputspath=input_path_noCOVID + region + '_input.xlsx', name=region, time_trend=True)
        kwargs = {'name': region,
                  'model_name': region,
                  'scen_type': 'coverage',
                  'progvals': sc.odict({'IYCF 1': [], 'IYCF 2': [], 'Kangaroo mother care': [],
                           'Public provision of complementary foods': [],'Vitamin A supplementation': [],
                           'Lipid-based nutrition supplements': [],
                           'Treatment of SAM': []})}
                           #'Management of MAM': [],'Oral rehydration salts': [], 'Zinc for treatment + ORS': [],
                           #'Balanced energy-protein supplementation': [], 'Cash transfers': [],
                           #'IFAS for pregnant women (community)': [],
                           #'IFAS (community)': [],  'IPTp': [],
                           #'Multiple micronutrient supplementation': []})}
        b_trend.add_scens(Scen(**kwargs))
    b_trend.run_scens()
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
    warnings.filterwarnings("ignore", category=RuntimeWarning)

    for c in country_list:
        region = c
        b_counter_pes.load_data(inputspath=input_path_pes + region + '_input.xlsx', name=region, time_trend=True)
        kwargs = {'name': region,
                  'model_name': region,
                  'scen_type': 'coverage',
                  'progvals': sc.odict({'Balanced energy-protein supplementation': [], 'Cash transfers': [],
                           'IYCF 1': [], 'IYCF 2': [], 'Kangaroo mother care': [],
                           'Public provision of complementary foods': [],'Vitamin A supplementation': [],
                           'Lipid-based nutrition supplements': [],
                           #'Management of MAM': [],'Oral rehydration salts': [], 'Zinc for treatment + ORS': [],
                           'Treatment of SAM': [], 'IFAS for pregnant women (community)': [],
                           'IFAS (community)': [],  'IPTp': [],
                           'Multiple micronutrient supplementation': []})}
        b_counter_pes.add_scens(Scen(**kwargs))
    b_counter_pes.run_scens()
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
    warnings.filterwarnings("ignore", category=RuntimeWarning)

    for c in country_list:
        region = c
        b_counter_med.load_data(inputspath=input_path_med + region + '_input.xlsx', name=region, time_trend=True)
        kwargs = {'name': region,
                  'model_name': region,
                  'scen_type': 'coverage',
                  'progvals': sc.odict({'IYCF 1': [], 'IYCF 2': [], 'Kangaroo mother care': [],
                           'Public provision of complementary foods': [],'Vitamin A supplementation': [],
                           'Lipid-based nutrition supplements': [],
                           'Treatment of SAM': []})}
                           #'Management of MAM': [],'Oral rehydration salts': [], 'Zinc for treatment + ORS': [],
                           #'Balanced energy-protein supplementation': [], 'Cash transfers': [],
                           #'IFAS for pregnant women (community)': [],
                           #'IFAS (community)': [],  'IPTp': [],
                           #'Multiple micronutrient supplementation': []})}
        b_counter_med.add_scens(Scen(**kwargs))
    b_counter_med.run_scens()
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
    warnings.filterwarnings("ignore", category=RuntimeWarning)

    for c in country_list:
        region = c
        b_counter_opt.load_data(inputspath=input_path_opt + region + '_input.xlsx', name=region, time_trend=True)
        kwargs = {'name': region,
                  'model_name': region,
                  'scen_type': 'coverage',
                  'progvals': sc.odict({'IYCF 1': [], 'IYCF 2': [], 'Kangaroo mother care': [],
                           'Public provision of complementary foods': [],'Vitamin A supplementation': [],
                           'Lipid-based nutrition supplements': [],
                           'Treatment of SAM': []})}
                           #'Management of MAM': [],'Oral rehydration salts': [], 'Zinc for treatment + ORS': [],
                           #'Balanced energy-protein supplementation': [], 'Cash transfers': [],
                           #'IFAS for pregnant women (community)': [],
                           #'IFAS (community)': [],  'IPTp': [],
                           #'Multiple micronutrient supplementation': []})}
        b_counter_opt.add_scens(Scen(**kwargs))
    b_counter_opt.run_scens()
    # budgets2020 = sc.odict()
    # for c in range(len(country_list)):
    #     budgets2020[country_list[c]] = sc.odict()
    #     for i in prog_list:
    #         budgets2020[country_list[c]]['Baseline 2019'][i] = b.results[c][j].programs[i].annual_spend[1:]

    for res in b.results:
        for scenres in b.results[res]:
            scenres.name = scenres.model_name + ' Baseline 2019'
            results.append(scenres)
    for res in b_trend.results:
        for scenres in b_trend.results[res]:
            scenres.name = scenres.model_name + ' Baseline 2019 trend'
            results.append(scenres)
    for res in b_counter_pes.results:
        for scenres in b_counter_pes.results[res]:
            scenres.name = scenres.model_name + ' Baseline pes trend'
            results.append(scenres)
    for res in b_counter_med.results:
        for scenres in b_counter_med.results[res]:
            scenres.name = scenres.model_name + ' Baseline med trend'
            results.append(scenres)
    for res in b_counter_opt.results:
        for scenres in b_counter_opt.results[res]:
            scenres.name = scenres.model_name + ' Baseline opt trend'
            results.append(scenres)
    for p in proj_list1:
        for res in p.results:
            for scenres in p.results[res]:
                if scenres.name == 'Baseline':
                    scenres.name = scenres.model_name + ' Baseline pes'
                else:
                    scenres.name = scenres.model_name + ' Optimized pes'
                results.append(scenres)
    for p in proj_list2:
        for res in p.results:
            for scenres in p.results[res]:
                if scenres.name == 'Baseline':
                    scenres.name = scenres.model_name + ' Baseline med'
                else:
                    scenres.name = scenres.model_name + ' Optimized med'
                results.append(scenres)
    for p in proj_list3:
        for res in p.results:
            for scenres in p.results[res]:
                if scenres.name == 'Baseline':
                    scenres.name = scenres.model_name + ' Baseline opt'
                else:
                    scenres.name = scenres.model_name + ' Optimized opt'
                results.append(scenres)

    write_results(results, filename=output_path + 'projection_from_2020_7ints_.xlsx')




