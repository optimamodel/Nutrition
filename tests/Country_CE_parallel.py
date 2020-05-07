import xlsxwriter as xw
import sys
sys.path.append('/home/dom/Optima')
from nutrition.utils import run_parallel
import sciris as sc

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
def calc_CE(country, objective, proj, baseline, progs, prog_list, tol):
    import numpy as np
    from nutrition import ui
    import warnings
    warnings.filterwarnings('error')

    new_baseline = sc.dcp(baseline)
    p = proj
    effectiveness = 1.0
    programs = sc.dcp(progs)
    effective_progs = sc.odict()
    objective_cost = []
    objective_impact = []
    objective_CE = []
    while effectiveness < tol and programs:
        trials = []
        for prog in programs.keys():
            if prog == 'IPTp' or prog == 'Long-lasting insecticide-treated bednets':
                if p.datasets[-1].demo_data.demo['Percentage of population at risk of malaria'] <= 0.005:
                    trial_progs = sc.dcp(effective_progs)
                    trial_progs.append(prog, interp_cov(p, prog, [2018, 2024], 0.95))
                    trials.append(np.nan)
                    continue
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
                    trial_effectiveness = np.nan
            if trial_effectiveness >= 0:
                trials.append(trial_effectiveness)
            else:
                trials.append(np.nan)
        try:
            location = np.nanargmin(trials)
        except ValueError:
            break
        effective_progs.append(programs.keys()[location], interp_cov(p, programs.keys()[location], [2018, 2024], 0.95))
        kwargs = {'name': country,
                  'model_name': country,
                  'scen_type': 'coverage',
                  'progvals': effective_progs}
        scen_list = ui.make_scens([kwargs])
        p.add_scens(scen_list)
        p = run_scens_plus(p, prog_list, effective_progs)
        effectiveness = trials[location]
        print(effectiveness, programs.keys()[location])
        objective_CE.append(effectiveness)
        objective_cost.append((np.sum(p.results['scens'][-1].programs[programs.keys()[location]].annual_spend) -
                              (len(p.results['scens'][-1].programs[programs.keys()[location]].annual_spend)) *
                              p.results['scens'][-1].programs[programs.keys()[location]].annual_spend[0]))
        if objective == 'stunting':
            objective_impact.append(np.sum(baseline.model.stunted) - np.sum(p.results['scens'][-1].model.stunted))
        elif objective == 'wasting':
            objective_impact.append(np.sum(baseline.model.wasted) - np.sum(p.results['scens'][-1].model.wasted))
        elif objective == 'anaemia':
            objective_impact.append(np.sum(baseline.model.pw_anaemic) - np.sum(p.results['scens'][-1].model.pw_anaemic) + np.sum(baseline.model.nonpw_anaemic) - np.sum(p.results['scens'][-1].model.nonpw_anaemic))
        elif objective == 'mortality':
            objective_impact.append(np.sum(baseline.model.child_deaths) - np.sum(p.results['scens'][-1].model.child_deaths))
        new_baseline = p.results['scens'][-1]
        del programs[programs.keys()[location]] # delete most CE program for next round
    objective_progs = effective_progs.keys()
    return objective_CE, objective_cost, objective_impact, objective_progs

'''Main function to run CE analysis for all outcomes by country'''
def run_analysis(country):
    from nutrition import project
    cov = 0.95
    prog_list = ['Balanced energy-protein supplementation', 'Calcium supplementation',
                 'Delayed cord clamping', 'IFA fortification of maize', 'IFAS (community)',
                 'IFAS for pregnant women (community)', 'IPTp', 'Cash transfers',
                 'Iron and iodine fortification of salt', 'IYCF 1', 'Kangaroo mother care',
                 'Lipid-based nutrition supplements', 'Long-lasting insecticide-treated bednets',
                 'Multiple micronutrient supplementation', 'Zinc for treatment + ORS',
                 'Public provision of complementary foods', 'Treatment of SAM', 'Vitamin A supplementation']

    stunt_progs = sc.odict({'Balanced energy-protein supplementation': cov,
                            'IPTp': cov,
                            'IYCF 1': cov, 'Long-lasting insecticide-treated bednets': cov, 'Lipid-based nutrition supplements': cov,
                            'Multiple micronutrient supplementation': cov,
                            'Zinc for treatment + ORS': cov, 'Public provision of complementary foods': cov,
                            'Vitamin A supplementation': cov})
    wast_progs = sc.odict({'Balanced energy-protein supplementation': cov,
                           'IFAS for pregnant women (community)': cov,
                           'IYCF 1': cov, 'Kangaroo mother care': cov, 'Lipid-based nutrition supplements': cov,
                           'Multiple micronutrient supplementation': cov,
                           'Zinc for treatment + ORS': cov, 'Public provision of complementary foods': cov,
                           'Treatment of SAM': cov, 'Cash transfers': cov,
                           'Vitamin A supplementation': cov})
    anaem_progs = sc.odict({'IFA fortification of maize': cov, 'Multiple micronutrient supplementation': cov,
                            'Iron and iodine fortification of salt': cov,
                            'IYCF 1': cov, 'Long-lasting insecticide-treated bednets': cov, 'Lipid-based nutrition supplements': cov,
                            'IPTp': cov, 'Zinc for treatment + ORS': cov,
                            'Public provision of complementary foods': cov, 'IFAS for pregnant women (community)': cov,
                            'IFAS (community)': cov, 'Vitamin A supplementation': cov})
    mort_progs = sc.odict({'IFA fortification of maize': cov, 'Balanced energy-protein supplementation': cov,
                           'IFAS for pregnant women (community)': cov, 'IPTp': cov, 'Long-lasting insecticide-treated bednets': cov,
                           'IYCF 1': cov, 'Kangaroo mother care': cov, 'Lipid-based nutrition supplements': cov,
                           'Multiple micronutrient supplementation': cov,
                           'Zinc for treatment + ORS': cov, 'Public provision of complementary foods': cov,
                           'Treatment of SAM': cov, 'Cash transfers': cov,
                           'Vitamin A supplementation': cov, 'IFAS (community)': cov})

    tol = [200000, 200000, 500000, 150000] # CE thresholds for each outcome
    p = project.Project(country + ' scaled up')
    p.load_data(country='costed_baseline_' + country, name=country, time_trend=False)
    baseline = p.run_baseline(country, prog_list)
    stunting_CE, stunting_cost, stunting_impact, best_stunting_progs = calc_CE(country, 'stunting', p, baseline,
                                                                               stunt_progs, prog_list, tol[0])
    wasting_CE, wasting_cost, wasting_impact, best_wasting_progs = calc_CE(country, 'wasting', p, baseline,
                                                                           wast_progs, prog_list, tol[1])
    anaemia_CE, anaemia_cost, anaemia_impact, best_anaemia_progs = calc_CE(country, 'anaemia', p, baseline,
                                                                               anaem_progs, prog_list, tol[2])
    mortality_CE, mortality_cost, mortality_impact, best_mortality_progs = calc_CE(country, 'mortality', p, baseline,
                                                                               mort_progs, prog_list, tol[3])
    CE_data = [[stunting_CE[:-1], stunting_cost[:-1], stunting_impact[:-1], best_stunting_progs[:-1]],
               [wasting_CE[:-1], wasting_cost[:-1], wasting_impact[:-1], best_wasting_progs[:-1]],
               [anaemia_CE[:-1], anaemia_cost[:-1], anaemia_impact[:-1], best_anaemia_progs[:-1]],
               [mortality_CE[:-1], mortality_cost[:-1], mortality_impact[:-1], best_mortality_progs[:-1]]]
    return CE_data

def run_country_ce(date='01012020'):
    time_trends = False
    type = 'scaled up'

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
    output_data = sc.odict()
    # run simulation for each country
    CE_outputs = run_parallel(run_analysis, countries, 8)

    for c, country in enumerate(countries):
        CE_data[country] = CE_outputs[c]

    for objective in ['stunting', 'wasting', 'anaemia', 'mortality']:
        output_data[objective] = sc.odict()
        for c, country in enumerate(countries):
            output_data[objective][country] = CE_outputs[c][objective]['Programs']

    CE_book = xw.Workbook('Results/' + date + '/' + 'Country_CE_' + date + '.xlsx')
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
    return output_data

if __name__ == '__main__':
    run_country_ce()







