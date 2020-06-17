import xlsxwriter as xw
import sys
sys.path.append('/home/dom/Optima')
from nutrition.utils import run_parallel
import sciris as sc
from functools import partial

def interp_cov(project, program, years, target): # linear interpolation of coverage from baseline value
    interp = []
    timeskip = years[1] - years[0]
    baseline_cov = project.models[-1].prog_info.programs[program].base_cov
    if baseline_cov >= target:
        return baseline_cov
    else:
        diff = target - baseline_cov
        for year in list(range(timeskip + 1)):
            interp.append(baseline_cov + year * diff / timeskip)
        return interp

''' Adapted baseline scenario so that the most CE choices can be added for the next round'''
def run_baseline_plus(proj, model_name, prog_set, new, dorun=True):
    from nutrition.scenarios import Scen
    from nutrition.project import run_scen

    model = sc.dcp(proj.model(model_name))
    progvals = sc.odict({prog: [] for prog in prog_set})
    if isinstance(new, dict):
        for prog in new:
            progvals[prog] = new[prog]
    else:
        print(new)
    base = Scen(name=model_name, model_name=model_name, scen_type='coverage', progvals=progvals)
    if dorun:
        return run_scen(base, model)
    else:
        return base

def run_scens_plus(proj, prog_set, new_progs, scens=None): # adapted run_scenario to use adapted baselines
    """Function for running scenarios
    If scens is specified, they are added to self.scens """
    results = []
    if scens is not None:
        proj.add_scens(scens)
    for scen in proj.scens.values():
        if scen.active:
            if (scen.model_name is None) or (scen.model_name not in proj.datasets.keys()):
                raise Exception('Could not find valid dataset for %s.  Edit the scenario and change the dataset' % scen.name)
            res = run_baseline_plus(proj, scen.model_name, prog_set, new_progs)
            results.append(res)
    proj.add_result(results, name='scens')
    return proj

'''Calculates cost, impact and CE of each intervention scale up for a country and returns results until
 a CE threshold is crossed for the specified outcome'''
def calc_CE(country, objective, proj, baseline, prog_list, prog_order):
    import numpy as np
    from nutrition import ui
    stunt_choices = prog_order['stunting']

    wast_choices = prog_order['wasting']

    anaem_choices = prog_order['anaemia']

    mort_choices = prog_order['mortality']

    new_baseline = sc.dcp(baseline)
    p = proj
    effectiveness = 1.0
    if objective == 'stunting':
        programs = sc.dcp(stunt_choices[country])
    elif objective == 'wasting':
        programs = sc.dcp(wast_choices[country])
    elif objective == 'anaemia':
        programs = sc.dcp(anaem_choices[country])
    elif objective == 'mortality':
        programs = sc.dcp(mort_choices[country])
    effective_progs = sc.odict()
    objective_cost = []
    objective_impact = []
    objective_CE = []
    for prog in programs:
        trial_progs = sc.dcp(effective_progs)
        trial_progs.append(prog, interp_cov(p, prog, [2018, 2024], 0.95))
        kwargs = {'name': country,
                  'model_name': country,
                  'scen_type': 'coverage',
                  'progvals': trial_progs}
        scen_list = ui.make_scens([kwargs])
        p.add_scens(scen_list)
        p = run_scens_plus(p, prog_list, trial_progs)
        if objective == 'stunting':
            try:
                trial_effectiveness = (np.sum(p.results['scens'][-1].programs[prog].annual_spend) - \
                                      (len(p.results['scens'][-1].programs[prog].annual_spend)) * \
                                      p.results['scens'][-1].programs[prog].annual_spend[0]) /\
                                      (np.sum(new_baseline.model.stunted) - np.sum(p.results['scens'][-1].model.stunted))
            except RuntimeWarning:
                trial_effectiveness = np.nan
        elif objective == 'wasting':
            try:
                trial_effectiveness = (np.sum(p.results['scens'][-1].programs[prog].annual_spend) - \
                                      (len(p.results['scens'][-1].programs[prog].annual_spend)) * \
                                      p.results['scens'][-1].programs[prog].annual_spend[0]) /\
                                      (np.sum(new_baseline.model.wasted) - np.sum(p.results['scens'][-1].model.wasted))
            except RuntimeWarning:
                trial_effectiveness = np.nan
        elif objective == 'anaemia':
            try:
                trial_effectiveness = (np.sum(p.results['scens'][-1].programs[prog].annual_spend) - \
                                      (len(p.results['scens'][-1].programs[prog].annual_spend)) * \
                                      p.results['scens'][-1].programs[prog].annual_spend[0]) /\
                                      (np.sum(new_baseline.model.pw_anaemic) - np.sum(p.results['scens'][-1].model.pw_anaemic) + np.sum(new_baseline.model.nonpw_anaemic) - np.sum(p.results['scens'][-1].model.nonpw_anaemic))
            except RuntimeWarning:
                trial_effectiveness = np.nan
        elif objective == 'mortality':
            try:
                trial_effectiveness = (np.sum(p.results['scens'][-1].programs[prog].annual_spend) - \
                                      (len(p.results['scens'][-1].programs[prog].annual_spend)) * \
                                      p.results['scens'][-1].programs[prog].annual_spend[0]) /\
                                      (np.sum(new_baseline.model.child_deaths) - np.sum(p.results['scens'][-1].model.child_deaths))
            except RuntimeWarning:
                trial_effectiveness = 0 #np.nan
        else:
            trial_effectiveness = 0

        effective_progs.append(prog, interp_cov(p, prog, [2018, 2024], 0.95))
        kwargs = {'name': country,
                  'model_name': country,
                  'scen_type': 'coverage',
                  'progvals': effective_progs}
        scen_list = ui.make_scens([kwargs])
        p.add_scens(scen_list)
        p = run_scens_plus(p, prog_list, effective_progs)
        effectiveness = trial_effectiveness
        print(effectiveness, prog)
        if effectiveness <= 0 or effectiveness == np.nan or effectiveness == np.inf:
            objective_CE.append(0)
        else:
            objective_CE.append(effectiveness)
            objective_cost.append((np.sum(p.results['scens'][-1].programs[prog].annual_spend) -
                              (len(p.results['scens'][-1].programs[prog].annual_spend)) *
                              p.results['scens'][-1].programs[prog].annual_spend[0]))
        if effectiveness <= 0 or effectiveness == np.nan or effectiveness == np.inf:
            objective_impact.append(0)
        else:
            if objective == 'stunting':
                objective_impact.append(np.sum(baseline.model.stunted) - np.sum(p.results['scens'][-1].model.stunted))
            elif objective == 'wasting':
                objective_impact.append(np.sum(baseline.model.wasted) - np.sum(p.results['scens'][-1].model.wasted))
            elif objective == 'anaemia':
                objective_impact.append(np.sum(baseline.model.pw_anaemic) - np.sum(p.results['scens'][-1].model.pw_anaemic) + np.sum(baseline.model.nonpw_anaemic) - np.sum(p.results['scens'][-1].model.nonpw_anaemic))
            elif objective == 'mortality':
                objective_impact.append(np.sum(baseline.model.child_deaths) - np.sum(p.results['scens'][-1].model.child_deaths))
            else:
                objective_impact.append(0)
        new_baseline = p.results['scens'][-1]
        #del programs[programs.keys()[location]] # delete most CE program for next round
    objective_progs = effective_progs.keys()
    return objective_CE, objective_cost, objective_impact, objective_progs

'''Main function to run CE analysis for all outcomes by country'''
def run_analysis(country, prog_order, type):
    from nutrition import project

    prog_list = ['Balanced energy-protein supplementation', 'Calcium supplementation',
                 'Delayed cord clamping', 'IFA fortification of maize', 'IFAS (community)',
                 'IFAS for pregnant women (community)', 'IPTp', 'Cash transfers',
                 'Iron and iodine fortification of salt', 'IYCF 1', 'Kangaroo mother care',
                 'Lipid-based nutrition supplements', 'Long-lasting insecticide-treated bednets',
                 'Multiple micronutrient supplementation', 'Zinc for treatment + ORS',
                 'Public provision of complementary foods', 'Treatment of SAM', 'Vitamin A supplementation']

    p = project.Project(country + ' scaled up')
    if type == 'LBC':
        loc_name = 'Cost lower bounds/lbc'
    elif type == 'UBC':
        loc_name = 'Cost upper bounds/ubc'
    elif type == 'LBE':
        loc_name = 'Efficacy lower bounds/lbe'
    elif type == 'UBE':
        loc_name = 'Efficacy upper bounds/ube'
    else:
        print('Incorrect type was supplied for global bounds, please enter LBC, UBC, LBE or UBE')
    p.load_data(country=loc_name + '_costed_baseline_' + country, name=country, time_trend=False)
    baseline = p.run_baseline(country, prog_list)
    stunting_CE, stunting_cost, stunting_impact, best_stunting_progs = calc_CE(country, 'stunting', p, baseline,
                                                                               prog_list,  prog_order)
    wasting_CE, wasting_cost, wasting_impact, best_wasting_progs = calc_CE(country, 'wasting', p, baseline,
                                                                           prog_list, prog_order)
    anaemia_CE, anaemia_cost, anaemia_impact, best_anaemia_progs = calc_CE(country, 'anaemia', p, baseline,
                                                                               prog_list, prog_order)
    mortality_CE, mortality_cost, mortality_impact, best_mortality_progs = calc_CE(country, 'mortality', p, baseline,
                                                                               prog_list, prog_order)
    CE_data = [[stunting_CE, stunting_cost, stunting_impact, best_stunting_progs],
               [wasting_CE, wasting_cost, wasting_impact, best_wasting_progs],
               [anaemia_CE, anaemia_cost, anaemia_impact, best_anaemia_progs],
               [mortality_CE, mortality_cost, mortality_impact, best_mortality_progs]]
    return CE_data

def run_country_bounds(date, type, prog_order):

    # initialise project

    countries = ['China', 'North Korea', 'Cambodia', 'Indonesia', 'Laos', 'Malaysia', 'Maldives', 'Myanmar',
                 'Philippines', 'Sri Lanka', 'Thailand', 'Timor-Leste', 'Vietnam', 'Fiji', 'Kiribati',
                 'Federated States of Micronesia', 'Papua New Guinea', 'Samoa', 'Solomon Islands', 'Tonga', 'Vanuatu',
                 'Armenia', 'Azerbaijan', 'Kazakhstan', 'Kyrgyzstan', 'Mongolia', 'Tajikistan', 'Turkmenistan',
                 'Uzbekistan', 'Albania', 'Bosnia and Herzegovina', 'Bulgaria', 'Macedonia', 'Montenegro', 'Romania',
                 'Serbia', 'Belarus', 'Moldova', 'Russian Federation', 'Ukraine', 'Belize', 'Cuba', 'Dominican Republic',
                 'Grenada', 'Guyana', 'Haiti', 'Jamaica', 'Saint Lucia', 'Saint Vincent and the Grenadines', 'Suriname',
                 'Bolivia', 'Ecuador', 'Peru', 'Colombia', 'Costa Rica', 'El Salvador', 'Guatemala', 'Honduras',
                 'Nicaragua', 'Venezuela', 'Brazil', 'Paraguay', 'Algeria', 'Egypt', 'Iran', 'Iraq', 'Jordan', 'Lebanon',
                 'Libya', 'Morocco', 'Palestine', 'Syria', 'Tunisia', 'Turkey', 'Yemen', 'Afghanistan', 'Bangladesh',
                 'Bhutan', 'India', 'Nepal', 'Pakistan', 'Angola', 'Central African Republic', 'Congo',
                 'Democratic Republic of the Congo', 'Equatorial Guinea', 'Gabon', 'Burundi', 'Comoros', 'Djibouti',
                 'Ethiopia', 'Kenya', 'Madagascar', 'Malawi', 'Mauritius', 'Mozambique', 'Rwanda', 'Somalia', 'Tanzania',
                 'Uganda', 'Zambia', 'Botswana', 'Lesotho', 'Namibia', 'South Africa', 'Eswatini', 'Zimbabwe', 'Benin',
                 'Burkina Faso', 'Cameroon', 'Cape Verde', 'Chad', 'Cote dIvoire', 'The Gambia', 'Ghana', 'Guinea',
                 'Guinea-Bissau', 'Liberia', 'Mali', 'Mauritania', 'Niger', 'Nigeria', 'Sao Tome and Principe', 'Senegal',
                 'Sierra Leone', 'Togo', 'Georgia', 'South Sudan', 'Sudan']


    CE_data = sc.odict()
    # run simulation for each country
    parallel_analysis = partial(run_analysis, prog_order=prog_order, type=type)
    CE_outputs = run_parallel(parallel_analysis, countries, 8)

    for c, country in enumerate(countries):
        CE_data[country] = CE_outputs[c]
    print(CE_data)

    CE_book = xw.Workbook('Results/' + date + '/' + type + '_Country_CE_' + date + '.xlsx')
    CE_sheet = CE_book.add_worksheet()
    row = 0
    column = 0

    '''Write results to excel sheet'''
    for country in CE_data.keys():
        CE_sheet.write(row, column, country)
        row += 1
        column += 1
        for o, objective in enumerate(['stunting', 'wasting', 'anaemia', 'mortality']):
            CE_sheet.write(row, column, objective)
            row += 1
            column += 1
            for m, measure in enumerate(['Cost effectiveness', 'Cost', 'Impact', 'Program']):
                CE_sheet.write(row, column, measure)
                column += 1
                if CE_data[country][o][m]:
                    if measure == 'Cost':
                        CE_sheet.write(row, column, 0)
                        column += 1
                        for e, element in enumerate(CE_data[country][o][m]):
                            if e == 0:
                                CE_sheet.write(row, column, CE_data[country][o][m][e])
                                column += 1
                            else:
                                CE_sheet.write(row, column, sum(CE_data[country][o][m][:e+1]))
                                column += 1
                        row += 1
                        column -= e + 3
                    elif measure == 'Impact':
                        CE_sheet.write(row, column, 0)
                        column += 1
                        CE_sheet.write_row(row, column, CE_data[country][o][m])
                        row += 1
                        column -= 2
                    else:
                        CE_sheet.write(row, column, "")
                        column += 1
                        CE_sheet.write_row(row, column, CE_data[country][o][m])
                        row += 1
                        column -= 2
                else:
                    CE_sheet.write(row, column, "")
                    row += 1
                    column -= 1
            column -= 1
        column -= 1
    CE_book.close()
    print('Finished!')
    return








