import xlsxwriter as xw
import sciris as sc
from nutrition.project import Project
from nutrition import ui
import numpy as np

def interp_cov(project, program, years, target):
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

def cost_impact(country, prog_list, objective_progs, effective_progs, objective):
    cost = []
    impact = []
    p = Project(country + ' scaled up')
    p.load_data(country='costed_baseline_' + country, name=country, time_trend=False)
    if effective_progs:
        baseline = p.run_baseline_plus(country, prog_list, effective_progs)
    else:
        baseline = p.run_baseline(country, prog_list)
    for prog in objective_progs.keys():
        if prog == 'IPTp' or prog == 'Long-lasting insecticide-treated bednets':
            if p.datasets[-1].demo_data.demo['Percentage of population at risk of malaria'] <= 0.005:
                cost.append(0)
                impact.append(0)
                continue
        trial_progs = sc.dcp(effective_progs)
        trial_progs.append(prog, interp_cov(p, prog, [2018, 2024], 0.95))
        kwargs = {'name': country,
                  'model_name': country,
                  'scen_type': 'coverage',
                  'progvals': trial_progs}
        scen_list = ui.make_scens([kwargs])
        p.add_scens([scen_list])
        p.run_scens_plus(prog_list, trial_progs)
        cost.append((np.sum(p.results['scens'][-1].programs[prog].annual_spend) -
                     (len(p.results['scens'][-1].programs[prog].annual_spend)) *
                     p.results['scens'][-1].programs[prog].annual_spend[0]))
        if objective == 'stunting':
            impact.append(np.sum(baseline.model.stunted) - np.sum(p.results['scens'][-1].model.stunted))
        elif objective == 'wasting':
            impact.append(np.sum(baseline.model.wasted) - np.sum(p.results['scens'][-1].model.wasted))
        elif objective == 'anaemia':
            impact.append(np.sum(baseline.model.child_anaemic) - np.sum(p.results['scens'][-1].model.child_anaemic))
        elif objective == 'mortality':
            impact.append(np.sum(baseline.model.child_deaths) - np.sum(p.results['scens'][-1].model.child_deaths))
    return cost, impact


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

cov = 0.95
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

stunt_progs = sc.odict({'Balanced energy-protein supplementation': cov, 'Cash transfers': cov,
                        'IFAS for pregnant women (community)': cov, 'IPTp': cov,
                        'IYCF 1': cov, 'Kangaroo mother care': cov, 'Lipid-based nutrition supplements': cov,
                        'Long-lasting insecticide-treated bednets': cov,
                        'Multiple micronutrient supplementation': cov,
                        'Oral rehydration salts': cov, 'Public provision of complementary foods': cov,
                        'Treatment of SAM': cov,
                        'Vitamin A supplementation': cov, 'Zinc for treatment + ORS': cov,
                        'Zinc supplementation': cov})
wast_progs = sc.odict({'Balanced energy-protein supplementation': cov, 'Cash transfers': cov,
                       'IFAS for pregnant women (community)': cov, 'IPTp': cov,
                       'IYCF 1': cov, 'Kangaroo mother care': cov, 'Lipid-based nutrition supplements': cov,
                       'Long-lasting insecticide-treated bednets': cov,
                       'Multiple micronutrient supplementation': cov,
                       'Oral rehydration salts': cov, 'Public provision of complementary foods': cov,
                       'Treatment of SAM': cov,
                       'Vitamin A supplementation': cov, 'Zinc for treatment + ORS': cov,
                       'Zinc supplementation': cov})
anaem_progs = sc.odict({'Cash transfers': cov,
                        'Delayed cord clamping': cov, 'IFA fortification of maize': cov,
                        'Iron and iodine fortification of salt': cov,
                        'IYCF 1': cov, 'Kangaroo mother care': cov, 'Lipid-based nutrition supplements': cov,
                        'Long-lasting insecticide-treated bednets': cov,
                        'Micronutrient powders': cov, 'Oral rehydration salts': cov,
                        'Public provision of complementary foods': cov,
                        'Treatment of SAM': cov, 'Vitamin A supplementation': cov, 'Zinc for treatment + ORS': cov,
                        'Zinc supplementation': cov})
mort_progs = sc.odict({'Cash transfers': cov, 'IFA fortification of maize': cov,
                       'IFAS for pregnant women (community)': cov, 'IPTp': cov,
                       'IYCF 1': cov, 'Kangaroo mother care': cov, 'Lipid-based nutrition supplements': cov,
                       'Long-lasting insecticide-treated bednets': cov,
                       'Multiple micronutrient supplementation': cov,
                       'Oral rehydration salts': cov, 'Public provision of complementary foods': cov,
                       'Treatment of SAM': cov,
                       'Vitamin A supplementation': cov, 'Zinc for treatment + ORS': cov,
                       'Zinc supplementation': cov})

different_progs = [stunt_progs, wast_progs, anaem_progs, mort_progs]
prog_choices = sc.odict({'stunting': sc.odict({'Cost effectiveness': [], 'Cost': [], 'Impact': [], 'Program': []}),
                         'wasting': sc.odict({'Cost effectiveness': [], 'Cost': [], 'Impact': [], 'Program': []}),
                         'anaemia': sc.odict({'Cost effectiveness': [], 'Cost': [], 'Impact': [], 'Program': []}),
                         'mortality': sc.odict({'Cost effectiveness': [], 'Cost': [], 'Impact': [], 'Program': []})})
# run simulation for each country
num_CE = [5, 3, 3, 5]
for o, outcome in enumerate(['stunting', 'wasting', 'anaemia', 'mortality']):
    effective_progs = sc.odict()
    objective_progs = different_progs[o]
    for round in list(range(num_CE[o])):
        costs = sc.odict()
        impacts = sc.odict()
        total_cost = sc.odict()
        total_impact = sc.odict()
        total_CE = sc.odict()
        for country in countries[:5]:
            costs[country], impacts[country] = cost_impact(country, prog_list, objective_progs, effective_progs, outcome)
        for p, prog in enumerate(objective_progs.keys()):
            total_cost[prog] = 0
            total_impact[prog] = 0
            for i in list(range(len(countries[:5]))):
                total_cost[prog] += costs.values()[i][p]
                total_impact[prog] += np.nansum(impacts.values()[i][p])
            if total_impact[prog] <= 0:
                total_impact[prog] = np.nan
            try:
                total_CE[prog] = total_cost[prog] / total_impact[prog]
            except RuntimeWarning:
                total_CE[prog] = np.nan
        try:
            location = np.nanargmin(total_CE.values())
        except ValueError:
            break
        effective_progs.append(objective_progs.keys()[location], 0.95)
        prog_choices[outcome]['Cost effectiveness'].append(total_CE[objective_progs.keys()[location]])
        prog_choices[outcome]['Cost'].append(total_cost[objective_progs.keys()[location]])
        prog_choices[outcome]['Impact'].append(total_impact[objective_progs.keys()[location]])
        prog_choices[outcome]['Program'].append(objective_progs.keys()[location])

        del objective_progs[objective_progs.keys()[location]]

print(prog_choices['stunting'])
CE_book = xw.Workbook('Global_cost_effectiveness26082019.xlsx')
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
        if prog_choices[o][m]:
            if measure == 'Cost':
                CE_sheet.write(row, column, 0)
                column += 1
                for e, element in enumerate(prog_choices[o][m]):
                    CE_sheet.write(row, column, prog_choices[o][m][e])
                    column += 1
                row += 1
                column -= e + 3
            elif measure == 'Impact':
                CE_sheet.write(row, column, 0)
                column += 1
                CE_sheet.write_row(row, column, prog_choices[o][m])
                row += 1
                column -= 2
            else:
                CE_sheet.write(row, column, "")
                column += 1
                CE_sheet.write_row(row, column, prog_choices[o][m])
                row += 1
                column -= 2
        else:
            CE_sheet.write(row, column, "")
            row += 1
            column -= 1
    column -= 1

CE_book.close()
print('Finished!')
