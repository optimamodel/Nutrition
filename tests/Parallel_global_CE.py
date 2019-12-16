import xlsxwriter as xw
import numpy as np
from nutrition import project
from nutrition import ui
from nutrition.results import interp_cov
from nutrition.utils import run_parallel
from functools import partial
import sciris as sc
# Lots to do here!!

if __name__ == '__main__':
    def program_CE(prog, prog_list, proj, effective_progs, cov, country_list, iptp_trigger, outcome, baseline):
        trials = []
        trial = 0
        cost = 0
        if prog == 'IPTp' or prog == 'Long-lasting insecticide-treated bednets':
            trial_progs = sc.dcp(effective_progs)
            trial_progs.append(prog, interp_cov(proj, prog, [2018, 2024], cov))
            scen_list = []
            for c, country in enumerate(country_list):
                kwargs = {'name': country + prog,
                          'model_name': country,
                          'scen_type': 'coverage',
                          'progvals': trial_progs}
                scen_list.append(ui.make_scens([kwargs]))
            proj.add_scens(scen_list)
            proj.run_scens_plus(prog_list, trial_progs)
            for c, country in enumerate(country_list):
                if not iptp_trigger[country]:
                    if outcome == 'stunting':
                        trial += np.sum(proj.results['scens'][c].model.stunted)
                    elif outcome == 'wasting':
                        trial += np.sum(proj.results['scens'][c].model.wasted)
                    elif outcome == 'anaemia':
                        trial += np.sum(proj.results['scens'][c].model.child_anaemic)
                    elif outcome == 'mortality':
                        trial += np.sum(proj.results['scens'][c].model.child_deaths)
                    cost += np.sum(proj.results['scens'][c].programs[prog].annual_spend) - \
                                      (len(proj.results['scens'][c].programs[prog].annual_spend)) * \
                                      proj.results['scens'][c].programs[prog].annual_spend[0]
                else:
                    if outcome == 'stunting':
                        trial += np.sum(proj.run_baseline(country, prog_list).model.stunted)
                    elif outcome == 'wasting':
                        trial += np.sum(proj.run_baseline(country, prog_list).model.wasted)
                    elif outcome == 'anaemia':
                        trial += np.sum(proj.run_baseline(country, prog_list).model.child_anaemic)
                    elif outcome == 'mortality':
                        trial += np.sum(proj.run_baseline(country, prog_list).model.child_deaths)

        else:
            trial_progs = sc.dcp(effective_progs)
            trial_progs.append(prog, interp_cov(proj, prog, [2018, 2024], cov))
            scen_list = []
            for c, country in enumerate(country_list):
                kwargs = {'name': country + prog,
                          'model_name': country,
                          'scen_type': 'coverage',
                          'progvals': trial_progs}
                scen_list.append(ui.make_scens([kwargs]))
            proj.add_scens(scen_list)
            proj.run_scens_plus(prog_list, trial_progs)
            for c, country in enumerate(country_list):
                if outcome == 'stunting':
                    trial += np.sum(proj.results['scens'][c].model.stunted)
                elif outcome == 'wasting':
                    trial += np.sum(proj.results['scens'][c].model.wasted)
                elif outcome == 'anaemia':
                    trial += np.sum(proj.results['scens'][c].model.child_anaemic)
                elif outcome == 'mortality':
                    trial += np.sum(proj.results['scens'][c].model.child_deaths)
                cost += np.sum(proj.results['scens'][c].programs[prog].annual_spend) - \
                                  (len(proj.results['scens'][c].programs[prog].annual_spend)) * \
                                  proj.results['scens'][c].programs[prog].annual_spend[0]
        try:
            trial_effectiveness = cost / (baseline - trial)
        except RuntimeWarning:
            trial_effectiveness = np.nan
        if trial_effectiveness >= 0:
            trials.append(trial_effectiveness)
        else:
            trials.append(np.nan)
        return trials, trial, cost

    def run_total_analysis(country_list, num_procs):
        cov = 1.0
        progval = sc.odict(
            {'Balanced energy-protein supplementation': cov, 'Calcium supplementation': cov, 'Cash transfers': cov,
             'Delayed cord clamping': cov, 'IFA fortification of maize': cov, 'IFAS (community)': cov,
             'IFAS for pregnant women (community)': cov, 'IPTp': cov, 'Iron and iodine fortification of salt': cov,
             'IYCF 1': cov, 'Kangaroo mother care': cov, 'Lipid-based nutrition supplements': cov,
             'Long-lasting insecticide-treated bednets': cov, 'Mg for eclampsia': cov, 'Mg for pre-eclampsia': cov,
             'Micronutrient powders': cov, 'Multiple micronutrient supplementation': cov,
             'Oral rehydration salts': cov, 'Public provision of complementary foods': cov, 'Treatment of SAM': cov,
             'Vitamin A supplementation': cov, 'Zinc for treatment + ORS': cov, 'Zinc supplementation': cov})

        prog_list = sc.dcp(progval.keys())

        stunt_progs = sc.odict({'IFAS for pregnant women (community)': cov, 'IPTp': cov,
                                'IYCF 1': cov, 'Multiple micronutrient supplementation': cov,
                                'Public provision of complementary foods': cov,
                                'Treatment of SAM': cov,
                                'Vitamin A supplementation': cov, 'Zinc supplementation': cov})
        wast_progs = sc.odict({'Cash transfers': cov, 'Vitamin A supplementation': cov, 'Zinc supplementation': cov})
        anaem_progs = sc.odict({'IFA fortification of maize': cov, 'Iron and iodine fortification of salt': cov,
                                'Long-lasting insecticide-treated bednets': cov,
                                'Micronutrient powders': cov})
        mort_progs = sc.odict({'IFA fortification of maize': cov,
                               'IFAS for pregnant women (community)': cov, 'IPTp': cov,
                               'IYCF 1': cov, 'Kangaroo mother care': cov,
                               'Long-lasting insecticide-treated bednets': cov,
                               'Multiple micronutrient supplementation': cov,
                               'Oral rehydration salts': cov, 'Public provision of complementary foods': cov,
                               'Treatment of SAM': cov,
                               'Vitamin A supplementation': cov, 'Zinc for treatment + ORS': cov,
                               'Zinc supplementation': cov})

        programs = [stunt_progs, wast_progs, anaem_progs, mort_progs]
        tol = [20000, 200000, 50000, 150000]
        p = project.Project('scaled up')
        iptp_trigger = sc.odict()
        load = partial(p.load_data, time_trend=False)
        run_parallel(load, country_list, num_procs)
        for country in country_list:
            if p.datasets[-1].demo_data.demo['Percentage of population at risk of malaria'] <= 0.005:
                iptp_trigger[country] = True
            else:
                iptp_trigger[country] = False
        for o, outcome in enumerate(['stunting', 'wasting', 'anaemia', 'mortality']):
            effectiveness = 1.0
            objective_cost = []
            objective_impact = []
            objective_CE = []
            run_baseline = partial(p.run_baseline, prog_set=prog_list)
            baseline_full = run_parallel(run_baseline, country_list, num_procs)
            if outcome == 'stunting':
                baseline_set = np.sum(baseline_full[i].model.stunted for i in list(range(len(country_list))))
            elif outcome == 'wasting':
                baseline_set = np.sum(baseline_full[i].model.wasted for i in list(range(len(country_list))))
            elif outcome == 'anaemia':
                baseline_set = np.sum(baseline_full[i].model.child_anaemic for i in list(range(len(country_list))))
            elif outcome == 'mortality':
                baseline_set = np.sum(baseline_full[i].model.child_deaths for i in list(range(len(country_list))))
            baseline = np.sum(baseline_set)
            effective_progs = sc.odict()
            while effectiveness < tol[o] and programs[o]:
                test_progs = partial(program_CE, prog_list=prog_list, proj=p, effective_progs=effective_progs, cov=cov,
                                     country_list=country_list, iptp_trigger=iptp_trigger, outcome=outcome, baseline=baseline)
                trials, trial, cost = run_parallel(test_progs, programs[o].keys(), num_procs)
                try:
                    location = np.nanargmin(trials)
                except ValueError:
                    break
                effective_progs.append(programs[o].keys()[location],
                                       interp_cov(p, programs[o].keys()[location], [2018, 2024], cov))
                effectiveness = trials[location]
                objective_CE.append(effectiveness)
                objective_cost.append(cost[location])
                objective_impact.append(trial[location])
                baseline = trial[location]
                del programs[o][programs[o].keys()[location]]
            objective_progs = effective_progs.keys()
            if outcome == 'stunting':
                stunting_CE = objective_CE
                stunting_cost = objective_cost
                stunting_impact = objective_impact
                best_stunting_progs = objective_progs
            elif outcome == 'wasting':
                wasting_CE = objective_CE
                wasting_cost = objective_cost
                wasting_impact = objective_impact
                best_wasting_progs = objective_progs
            elif outcome == 'anaemia':
                anaemia_CE = objective_CE
                anaemia_cost = objective_cost
                anaemia_impact = objective_impact
                best_anaemia_progs = objective_progs
            elif outcome == 'mortality':
                mortality_CE = objective_CE
                mortality_cost = objective_cost
                mortality_impact = objective_impact
                best_mortality_progs = objective_progs
        CE_data = [[stunting_CE[:-1], stunting_cost[:-1], stunting_impact[:-1], best_stunting_progs[:-1]],
                   [wasting_CE[:-1], wasting_cost[:-1], wasting_impact[:-1], best_wasting_progs[:-1]],
                   [anaemia_CE[:-1], anaemia_cost[:-1], anaemia_impact[:-1], best_anaemia_progs[:-1]],
                   [mortality_CE[:-1], mortality_cost[:-1], mortality_impact[:-1], best_mortality_progs[:-1]]]
        return CE_data
    # initialise project

    countries = ['China', 'North Korea', 'Cambodia', 'Indonesia', 'Laos', 'Malaysia', 'Maldives', 'Myanmar',
                 'Philippines', 'Sri Lanka', 'Thailand', 'Timor-Leste', 'Vietnam', 'Fiji', 'Kiribati',
                 'Federated States of Micronesia', 'Papua New Guinea', 'Samoa', 'Solomon Islands', 'Tonga', 'Vanuatu',
                 'Armenia', 'Azerbaijan', 'Kazakhstan', 'Kyrgyzstan', 'Mongolia', 'Tajikistan', 'Turkmenistan',
                 'Uzbekistan', 'Albania', 'Bosnia and Herzegovina', 'Bulgaria', 'Macedonia', 'Montenegro', 'Romania',
                 'Serbia', 'Belarus', 'Moldova', 'Russian Federation', 'Ukraine', 'Belize', 'Cuba',
                 'Dominican Republic',
                 'Grenada', 'Guyana', 'Haiti', 'Jamaica', 'Saint Lucia', 'Saint Vincent and the Grenadines', 'Suriname',
                 'Bolivia', 'Ecuador', 'Peru', 'Colombia', 'Costa Rica', 'El Salvador', 'Guatemala', 'Honduras',
                 'Nicaragua', 'Venezuela', 'Brazil', 'Paraguay', 'Algeria', 'Egypt', 'Iran', 'Iraq', 'Jordan',
                 'Lebanon',
                 'Libya', 'Morocco', 'Palestine', 'Syria', 'Tunisia', 'Turkey', 'Yemen', 'Afghanistan', 'Bangladesh',
                 'Bhutan', 'India', 'Nepal', 'Pakistan', 'Angola', 'Central African Republic', 'Congo',
                 'Democratic Republic of the Congo', 'Equatorial Guinea', 'Gabon', 'Burundi', 'Comoros', 'Djibouti',
                 'Ethiopia', 'Kenya', 'Madagascar', 'Malawi', 'Mauritius', 'Mozambique', 'Rwanda', 'Somalia',
                 'Tanzania',
                 'Uganda', 'Zambia', 'Botswana', 'Lesotho', 'Namibia', 'South Africa', 'Eswatini', 'Zimbabwe', 'Benin',
                 'Burkina Faso', 'Cameroon', 'Cape Verde', 'Chad', 'Cote dIvoire', 'The Gambia', 'Ghana', 'Guinea',
                 'Guinea-Bissau', 'Liberia', 'Mali', 'Mauritania', 'Niger', 'Nigeria', 'Sao Tome and Principe',
                 'Senegal',
                 'Sierra Leone', 'Togo', 'Georgia', 'South Sudan', 'Sudan']

    CE_data = sc.odict()
    # run simulation for each country
    result = run_total_analysis(countries, 16)

    CE_book = xw.Workbook('Global_cost_effectiveness21082019.xlsx')
    CE_sheet = CE_book.add_worksheet()
    row = 0
    column = 0

    CE_sheet.write(row, column, 'World')
    row += 1
    column += 1
    for o, objective in enumerate(['stunting', 'wasting', 'anaemia', 'mortality']):
        CE_sheet.write(row, column, objective)
        row += 1
        column += 1
        for m, measure in enumerate(['Cost effectiveness', 'Cost', 'Impact', 'Program']):
            CE_sheet.write(row, column, measure)
            column += 1
            if result[o][m]:
                if measure == 'Cost':
                    CE_sheet.write(row, column, 0)
                    column += 1
                    for e, element in enumerate(result[o][m]):
                        if e == 0:
                            CE_sheet.write(row, column, result[o][m][e])
                            column += 1
                        else:
                            CE_sheet.write(row, column, sum(result[o][m][:e + 1]))
                            column += 1
                    row += 1
                    column -= e + 3
                elif measure == 'Impact':
                    CE_sheet.write(row, column, 0)
                    column += 1
                    CE_sheet.write_row(row, column, result[o][m])
                    row += 1
                    column -= 2
                else:
                    CE_sheet.write(row, column, "")
                    column += 1
                    CE_sheet.write_row(row, column, result[o][m])
                    row += 1
                    column -= 2
            else:
                CE_sheet.write(row, column, "")
                row += 1
                column -= 1
        column -= 1

    CE_book.close()
    print('Finished!')







