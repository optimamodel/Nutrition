import xlsxwriter as xw
import sys
sys.path.append('/home/dom/Optima/')
import sciris as sc
from nutrition import project
from nutrition import ui
from functools import partial
import numpy as np
import multiprocessing

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

def calc_cost_impact(country, project, baseline, objective_progs, objective, eff_progs):
    cost = {}
    impact = {}
    effective_progs = {}
    if eff_progs:
        if len(eff_progs.keys()) > 1:
            for prog in eff_progs.keys():
                effective_progs[prog] = interp_cov(project, prog, [2018, 2024], 0.95)
        else:
            effective_progs[eff_progs.keys()[0]] = interp_cov(project, eff_progs.keys()[0], [2018, 2024], 0.95)
    for prog in objective_progs.keys():
        if prog == 'IPTp' or prog == 'Long-lasting insecticide-treated bednets':
            if project.datasets[-1].demo_data.demo['Percentage of population at risk of malaria'] <= 0.005:
                cost[prog] = np.nan
                impact[prog] = np.nan
                continue
        trial_progs = sc.dcp(effective_progs)
        trial_progs[prog] = interp_cov(project, prog, [2018, 2024], 0.95)
        kwargs = {'name': country,
                  'model_name': country,
                  'scen_type': 'coverage',
                  'progvals': trial_progs}
        scen_list = ui.make_scens([kwargs])
        project.add_scens(scen_list)
        project.run_scens_plus(prog_list, trial_progs)
        cost[prog] = (np.sum(project.results['scens'][-1].programs[prog].annual_spend) -
                     (len(project.results['scens'][-1].programs[prog].annual_spend)) *
                     project.results['scens'][-1].programs[prog].annual_spend[0])
        if objective == 'stunting':
            impact[prog] = np.sum(baseline.model.stunted) - np.sum(project.results['scens'][-1].model.stunted)
            #if prog == 'IYCF 1':
                #print('calc', country, np.sum(baseline.model.stunted) - np.sum(project.results['scens'][-1].model.stunted))
        elif objective == 'wasting':
            impact[prog] = np.sum(baseline.model.wasted) - np.sum(project.results['scens'][-1].model.wasted)
        elif objective == 'anaemia':
            impact[prog] = np.sum(baseline.model.child_anaemic) - np.sum(project.results['scens'][-1].model.child_anaemic)
        elif objective == 'mortality':
            impact[prog] = np.sum(baseline.model.child_deaths) - np.sum(project.results['scens'][-1].model.child_deaths)
    return cost, impact


def cost_impact(country, objective, objective_progs, eff_progs):
    progval = {'Balanced energy-protein supplementation': cov, 'Calcium supplementation': cov,
         'Delayed cord clamping': cov, 'IFA fortification of maize': cov, 'IFAS (community)': cov,
         'IFAS for pregnant women (community)': cov, 'Iron and iodine fortification of salt': cov,
         'IYCF 1': cov, 'Kangaroo mother care': cov, 'Lipid-based nutrition supplements': cov,
         'Micronutrient powders': cov, 'Multiple micronutrient supplementation': cov,
         'Zinc for treatment + ORS': cov, 'Public provision of complementary foods': cov, 'Treatment of SAM': cov,
         'Vitamin A supplementation': cov, 'Zinc supplementation': cov}

    prog_list = sc.dcp(progval.keys())

    p = project.Project(country + ' scaled up')
    p.load_data(country='lb_costed_baseline_' + country, name=country, time_trend=False)
    effective_progs = {}
    if eff_progs:
        if len(eff_progs.keys()) > 1:
            for prog in eff_progs.keys():
                effective_progs[prog] = interp_cov(p, prog, [2018, 2024], 0.95)
        else:
            effective_progs[eff_progs.keys()[0]] = interp_cov(p, eff_progs.keys()[0], [2018, 2024], 0.95)
    if effective_progs:
	if 'IPTp' in effective_progs.keys():
            if p.datasets[-1].demo_data.demo['Percentage of population at risk of malaria'] <= 0.005:
                #print(effective_progs)
                del effective_progs['IPTp']
                #print(effective_progs)
        elif 'Long-lasting insecticide-treated bednets' in effective_progs.keys():
            if p.datasets[-1].demo_data.demo['Percentage of population at risk of malaria'] <= 0.005:
                del effective_progs['Long-lasting insecticide-treated bednets']
        if effective_progs:
            baseline = p.run_baseline_plus(country, prog_list, effective_progs)
        else:
            baseline = p.run_baseline(country, prog_list)
    else:
        baseline = p.run_baseline(country, prog_list)

    cost, impact = calc_cost_impact(country, p, baseline, objective_progs, objective, effective_progs)
    #print('output', country, impact['IYCF 1'])
    val = [country, cost, impact]
    return val


def run_parallel(func, args_list, num_procs):
    """ Uses pool.map() to distribute parallel processes.
    args_list: an iterable of args (also iterable)
    func: function to parallelise, must have single explicit argument (i.e an iterable)
    """

    f = multiprocessing.Pool(processes=num_procs)
    res = f.map(func, args_list)
    return res

time_trends = False
type = 'scaled up'
# initialise project

countries = ['North Korea', 'Cambodia', 'Indonesia', 'Laos', 'Malaysia', 'Maldives', 'Myanmar',
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
progval = {'Balanced energy-protein supplementation': cov, 'Calcium supplementation': cov,
     'Delayed cord clamping': cov, 'IFA fortification of maize': cov, 'IFAS (community)': cov,
     'IFAS for pregnant women (community)': cov, 'Iron and iodine fortification of salt': cov,
     'IYCF 1': cov, 'Kangaroo mother care': cov, 'Lipid-based nutrition supplements': cov,
     'Micronutrient powders': cov, 'Multiple micronutrient supplementation': cov,
     'Zinc for treatment + ORS': cov, 'Public provision of complementary foods': cov, 'Treatment of SAM': cov,
     'Vitamin A supplementation': cov, 'Zinc supplementation': cov}

prog_list = sc.dcp(progval.keys())

stunt_progs = ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation',
               'IFAS for pregnant women (community)', 'Public provision of complementary foods',
               'Balanced energy-protein supplementation']
wast_progs = ['Zinc supplementation', 'Vitamin A supplementation']
anaem_progs = ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize']
mort_progs = ['Kangaroo mother care', 'Zinc for treatment + ORS',
              'IFAS for pregnant women (community)', 'Zinc supplementation', 'Vitamin A supplementation',
              'IYCF 1', 'IFA fortification of maize',
              'Balanced energy-protein supplementation',
              'Public provision of complementary foods', 'Treatment of SAM']

different_progs = [stunt_progs, wast_progs, anaem_progs, mort_progs]
prog_choices = sc.odict({'stunting': sc.odict({'Cost effectiveness': [], 'Cost': [], 'Impact': [], 'Program': []}),
 'wasting': sc.odict({'Cost effectiveness': [], 'Cost': [], 'Impact': [], 'Program': []}),
'anaemia': sc.odict({'Cost effectiveness': [], 'Cost': [], 'Impact': [], 'Program': []}),
'mortality': sc.odict({'Cost effectiveness': [], 'Cost': [], 'Impact': [], 'Program': []})})
# run simulation for each country
num_CE = [5, 2, 3, 10]
for o, outcome in enumerate(['stunting', 'wasting', 'anaemia', 'mortality']):
    effective_progs = {}
    objective_progs = different_progs[o]
    for round in list(range(num_CE[o])):
        costs = {}
        impacts = {}
        total_cost = {}
        total_impact = {}
        total_CE = {}
        impact_cost = partial(cost_impact, objective=outcome, objective_progs=progval, eff_progs=effective_progs)
        CE_values = run_parallel(impact_cost, countries, 8)
        for prog, program in enumerate(objective_progs):
            total_cost[program] = 0
            total_impact[program] = 0
            for i in list(range(len(countries))):
                if ~np.isnan(CE_values[i][1][program]):
                    total_cost[program] += CE_values[i][1][program]
                if ~np.isnan(CE_values[i][2][program]):
                    #if program == 'IYCF 1':
                        #print('save', countries[i], CE_values[i][2][program])
                    total_impact[program] += CE_values[i][2][program]
            if total_impact[program] <= 0:
                #print(outcome, 'getting negative impact for program', program, total_impact[program])
                total_impact[program] = np.nan
            try:
                total_CE[program] = total_cost[program] / total_impact[program]
            except RuntimeWarning:
                total_CE[program] = np.nan
        try:
            #location = np.nanargmin(total_CE.values())
            program_choice = objective_progs[round]
        except ValueError:
            break
        effective_progs[program_choice] = 0.95
        prog_choices[outcome]['Cost effectiveness'].append(total_CE[program_choice])
        prog_choices[outcome]['Cost'].append(total_cost[program_choice])
        prog_choices[outcome]['Impact'].append(total_impact[program_choice])
        prog_choices[outcome]['Program'].append(program_choice)
        print(outcome, prog_choices[outcome]['Program'], prog_choices[outcome]['Cost effectiveness'])
        #del objective_progs[program_choice]

print(prog_choices)
CE_book = xw.Workbook('LBC_Global_cost_effectiveness01112019.xlsx')
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
        if prog_choices[objective][measure]:
            if measure == 'Cost':
                CE_sheet.write(row, column, 0)
                column += 1
                for e, element in enumerate(prog_choices[objective][measure]):
                    CE_sheet.write(row, column, prog_choices[objective][measure][e])
                    column += 1
                row += 1
                column -= e + 3
            elif measure == 'Impact':
                CE_sheet.write(row, column, 0)
                column += 1
                CE_sheet.write_row(row, column, prog_choices[objective][measure])
                row += 1
                column -= 2
            else:
                CE_sheet.write(row, column, "")
                column += 1
                CE_sheet.write_row(row, column, prog_choices[objective][measure])
                row += 1
                column -= 2
        else:
            CE_sheet.write(row, column, "")
            row += 1
            column -= 1
    column -= 1

CE_book.close()
print('Finished!')