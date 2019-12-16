import xlsxwriter as xw
import sys
sys.path.append('/home/dom/Optima')
from nutrition.utils import run_parallel
import sciris as sc


time_trends = False
type = 'scaled up'

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

'''Calculates cost, impact and CE of each intervention scale up for a country and returns results until
 a CE threshold is crossed for the specified outcome'''
def calc_CE(country, objective, proj, baseline, progs, prog_list, tol):
    import numpy as np
    from nutrition import ui
    stunt_choices = {'South Africa': ['IYCF 1', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'Vitamin A supplementation', 'Public provision of complementary foods'],
                     'India': ['IYCF 1', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Vitamin A supplementation', 'Public provision of complementary foods'],
                     'Indonesia': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Philippines': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Pakistan': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Botswana': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Iraq': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Equatorial Guinea': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Gabon': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Maldives': ['IYCF 1', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'Vitamin A supplementation', 'Public provision of complementary foods'],
                     'Turkmenistan': ['IYCF 1', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'Vitamin A supplementation', 'Public provision of complementary foods'],
                     'Madagascar': ['IYCF 1', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods', 'Balanced energy-protein supplementation'],
                     'Mali': ['IYCF 1', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods', 'Balanced energy-protein supplementation'],
                     'Sierra Leone': ['IYCF 1', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods', 'Balanced energy-protein supplementation'],
                     'Sao Tome and Principe': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Papua New Guinea': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Haiti': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Bangladesh': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Nepal': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Comoros': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Ethiopia': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Malawi': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Mozambique': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Benin': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'The Gambia': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Guinea-Bissau': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Mauritania': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Senegal': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Cambodia': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Laos': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Angola': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Burundi': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Somalia': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Tanzania': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Eswatini': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Zimbabwe': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Cote dIvoire': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Ghana': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Niger': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Nigeria': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Thailand': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Vietnam': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'North Korea': ['IYCF 1', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods', 'Balanced energy-protein supplementation'],
                     'Uzbekistan': ['IYCF 1', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods', 'Balanced energy-protein supplementation'],
                     'Saint Lucia': ['IYCF 1', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Vitamin A supplementation', 'Lipid-based nutrition supplements'],
                     'Romania': ['IYCF 1', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Vitamin A supplementation', 'Lipid-based nutrition supplements'],
                     'Russian Federation': ['IYCF 1', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Vitamin A supplementation', 'Lipid-based nutrition supplements'],
                     'Armenia': ['IYCF 1', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Vitamin A supplementation', 'Public provision of complementary foods'],
                     'Azerbaijan': ['IYCF 1', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Vitamin A supplementation', 'Public provision of complementary foods'],
                     'Bulgaria': ['IYCF 1', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Vitamin A supplementation', 'Public provision of complementary foods'],
                     'Montenegro': ['IYCF 1', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Vitamin A supplementation', 'Public provision of complementary foods'],
                     'Ukraine': ['IYCF 1', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Vitamin A supplementation', 'Public provision of complementary foods'],
                     'Belize': ['IYCF 1', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Vitamin A supplementation', 'Public provision of complementary foods'],
                     'Guyana': ['IYCF 1', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Vitamin A supplementation', 'Public provision of complementary foods'],
                     'Jamaica': ['IYCF 1', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Vitamin A supplementation', 'Public provision of complementary foods'],
                     'Georgia': ['IYCF 1', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Vitamin A supplementation', 'Public provision of complementary foods'],
                     'Bosnia and Herzegovina': ['IYCF 1', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Vitamin A supplementation', 'Public provision of complementary foods'],
                     'Serbia': ['IYCF 1', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Vitamin A supplementation', 'Public provision of complementary foods'],
                     'Suriname': ['IYCF 1', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Vitamin A supplementation', 'Public provision of complementary foods'],
                     'Saint Vincent and the Grenadines': ['IYCF 1', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Vitamin A supplementation', 'Public provision of complementary foods'],
                     'Brazil': ['IYCF 1', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Vitamin A supplementation', 'Public provision of complementary foods'],
                     'Cuba': ['IYCF 1', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Vitamin A supplementation', 'Public provision of complementary foods'],
                     'Belarus': ['IYCF 1', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Vitamin A supplementation'],
                     'Burkina Faso': ['IYCF 1', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods', 'Balanced energy-protein supplementation'],
                     'Rwanda': ['IYCF 1', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods', 'Lipid-based nutrition supplements'],
                     'Yemen': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Afghanistan': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'South Sudan': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Congo': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Kenya': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Uganda': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Zambia': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Cameroon': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Guinea': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Togo': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Myanmar': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Libya': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Grenada': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Lipid-based nutrition supplements'],
                     'Costa Rica': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Lipid-based nutrition supplements'],
                     'Mauritius': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Lipid-based nutrition supplements'],
                     'Turkey': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Lipid-based nutrition supplements'],
                     'Malaysia': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Lipid-based nutrition supplements'],
                     'Timor-Leste': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Kiribati': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Federated States of Micronesia': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Solomon Islands': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Syria': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Bhutan': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Djibouti': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Sri Lanka': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Fiji': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Kyrgyzstan': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Albania': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Moldova': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Colombia': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'El Salvador': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Honduras': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Iran': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Jordan': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Lebanon': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Palestine': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Lesotho': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'China': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Samoa': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Vanuatu': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Mongolia': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Tajikistan': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Bolivia': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Ecuador': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Peru': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Nicaragua': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Paraguay': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Algeria': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Egypt': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Morocco': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Tunisia': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Cape Verde': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Kazakhstan': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Macedonia': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)'],
                     'Dominican Republic': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)'],
                     'Democratic Republic of the Congo': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Chad': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Liberia': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Central African Republic': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Namibia': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'Public provision of complementary foods'],
                     'Tonga': ['IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation'],
                     'Sudan': ['Zinc supplementation', 'IYCF 1', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Guatemala': ['Zinc supplementation', 'IYCF 1', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Public provision of complementary foods'],
                     'Venezuela': ['Zinc supplementation', 'IYCF 1', 'Vitamin A supplementation', 'IFAS for pregnant women (community)', 'Lipid-based nutrition supplements']}


    wast_choices = {'South Africa': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'India': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Indonesia': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Philippines': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Pakistan': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Botswana': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Iraq': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Equatorial Guinea': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Gabon': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Maldives': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Turkmenistan': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Madagascar': ['Zinc supplementation', 'Cash transfers'],
                    'Mali': ['Zinc supplementation'],
                    'Sierra Leone': ['Zinc supplementation'],
                    'Sao Tome and Principe': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Papua New Guinea': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Haiti': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Bangladesh': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Nepal': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Comoros': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Ethiopia': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Malawi': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Mozambique': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Benin': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'The Gambia': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Guinea-Bissau': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Mauritania': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Senegal': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Cambodia': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Laos': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Angola': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Burundi': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Somalia': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Tanzania': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Eswatini': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Zimbabwe': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Cote dIvoire': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Ghana': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Niger': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Nigeria': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Thailand': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Vietnam': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'North Korea': ['Zinc supplementation'],
                    'Uzbekistan': ['Zinc supplementation'],
                    'Saint Lucia': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Romania': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Russian Federation': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Armenia': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Azerbaijan': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Bulgaria': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Montenegro': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Ukraine': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Belize': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Guyana': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Jamaica': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Georgia': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Bosnia and Herzegovina': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Serbia': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Suriname': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Saint Vincent and the Grenadines': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Brazil': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Cuba': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Belarus': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Burkina Faso': ['Zinc supplementation'],
                    'Rwanda': ['Zinc supplementation'],
                    'Yemen': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Afghanistan': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'South Sudan': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Congo': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Kenya': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Uganda': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Zambia': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Cameroon': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Guinea': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Togo': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Myanmar': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Libya': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Grenada': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Costa Rica': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Mauritius': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Turkey': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Malaysia': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Timor-Leste': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Kiribati': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Federated States of Micronesia': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Solomon Islands': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Syria': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Bhutan': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Djibouti': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Sri Lanka': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Fiji': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Kyrgyzstan': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Albania': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Moldova': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Colombia': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'El Salvador': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Honduras': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Iran': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Jordan': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Lebanon': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Palestine': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Lesotho': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'China': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Samoa': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Vanuatu': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Mongolia': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Tajikistan': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Bolivia': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Ecuador': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Peru': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Nicaragua': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Paraguay': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Algeria': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Egypt': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Morocco': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Tunisia': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Cape Verde': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Kazakhstan': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Macedonia': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Dominican Republic': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Democratic Republic of the Congo': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Chad': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Liberia': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Central African Republic': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Namibia': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Tonga': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Sudan': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Guatemala': ['Zinc supplementation', 'Vitamin A supplementation'],
                    'Venezuela': ['Zinc supplementation', 'Vitamin A supplementation']}


    anaem_choices = {'South Africa': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'India': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Indonesia': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Philippines': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Pakistan': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Botswana': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Iraq': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Equatorial Guinea': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Gabon': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Maldives': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Turkmenistan': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Madagascar': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Mali': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Sierra Leone': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Sao Tome and Principe': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Papua New Guinea': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Haiti': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Bangladesh': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Nepal': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Comoros': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Ethiopia': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Malawi': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Mozambique': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Benin': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'The Gambia': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Guinea-Bissau': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Mauritania': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Senegal': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Cambodia': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Laos': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Angola': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Burundi': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Somalia': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Tanzania': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Eswatini': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Zimbabwe': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Cote dIvoire': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Ghana': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Niger': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Nigeria': ['Iron and iodine fortification of salt', 'Micronutrient powders'],
                     'Thailand': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Vietnam': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'North Korea': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Uzbekistan': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Saint Lucia': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Romania': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Russian Federation': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Armenia': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Azerbaijan': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Bulgaria': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Montenegro': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Ukraine': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Belize': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Guyana': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Jamaica': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Georgia': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Bosnia and Herzegovina': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Serbia': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Suriname': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Saint Vincent and the Grenadines': ['Iron and iodine fortification of salt', 'Micronutrient powders'],
                     'Brazil': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Cuba': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Belarus': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Burkina Faso': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Rwanda': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Yemen': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Afghanistan': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'South Sudan': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Congo': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Kenya': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Uganda': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Zambia': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Cameroon': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Guinea': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Togo': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Myanmar': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Libya': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Grenada': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Costa Rica': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Mauritius': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize', 'Zinc supplementation'],
                     'Turkey': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Malaysia': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Timor-Leste': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Kiribati': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Federated States of Micronesia': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Solomon Islands': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Syria': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Bhutan': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Djibouti': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Sri Lanka': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Fiji': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Kyrgyzstan': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Albania': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Moldova': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Colombia': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'El Salvador': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Honduras': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Iran': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Jordan': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Lebanon': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Palestine': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Lesotho': ['Iron and iodine fortification of salt', 'Micronutrient powders'],
                     'China': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Samoa': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Vanuatu': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Mongolia': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Tajikistan': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Bolivia': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Ecuador': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Peru': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Nicaragua': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Paraguay': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Algeria': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Egypt': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Morocco': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Tunisia': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Cape Verde': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Kazakhstan': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Macedonia': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Dominican Republic': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Democratic Republic of the Congo': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Chad': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Liberia': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Central African Republic': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Namibia': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Tonga': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Sudan': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Guatemala': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize'],
                     'Venezuela': ['Iron and iodine fortification of salt', 'Micronutrient powders', 'IFA fortification of maize']}


    mort_choices = {'South Africa': ['Zinc for treatment + ORS', 'Kangaroo mother care', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Vitamin A supplementation'],
                    'India': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'Zinc for treatment + ORS', 'Vitamin A supplementation'],
                    'Indonesia': ['Kangaroo mother care', 'Zinc for treatment + ORS', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'Vitamin A supplementation'],
                    'Philippines': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'Zinc for treatment + ORS', 'Vitamin A supplementation'],
                    'Pakistan': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'Zinc for treatment + ORS', 'Vitamin A supplementation'],
                    'Botswana': ['Kangaroo mother care', 'Zinc for treatment + ORS', 'IFAS for pregnant women (community)', 'IFA fortification of maize', 'Vitamin A supplementation'],
                    'Iraq': ['Kangaroo mother care', 'IFA fortification of maize', 'IFAS for pregnant women (community)', 'Zinc for treatment + ORS', 'Zinc supplementation'],
                    'Equatorial Guinea': ['Kangaroo mother care', 'IFA fortification of maize', 'IFAS for pregnant women (community)', 'Zinc for treatment + ORS', 'Zinc supplementation'],
                    'Gabon': ['Kangaroo mother care', 'IFA fortification of maize', 'Zinc for treatment + ORS', 'IFAS for pregnant women (community)', 'Zinc supplementation'],
                    'Maldives': ['IFA fortification of maize', 'IFAS for pregnant women (community)', 'Kangaroo mother care', 'Zinc for treatment + ORS'],
                    'Turkmenistan': ['Kangaroo mother care', 'IFA fortification of maize', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'Zinc for treatment + ORS'],
                    'Madagascar': ['Kangaroo mother care', 'IYCF 1', 'Zinc supplementation', 'Zinc for treatment + ORS', 'IFAS for pregnant women (community)'],
                    'Mali': ['Kangaroo mother care', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'IYCF 1', 'Zinc for treatment + ORS'],
                    'Sierra Leone': ['Kangaroo mother care', 'Zinc supplementation', 'IYCF 1', 'IFAS for pregnant women (community)', 'Zinc for treatment + ORS'],
                    'Sao Tome and Principe': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'IFA fortification of maize', 'Zinc for treatment + ORS'],
                    'Papua New Guinea': ['Kangaroo mother care', 'Zinc for treatment + ORS', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'Vitamin A supplementation'],
                    'Haiti': ['Kangaroo mother care', 'Zinc supplementation', 'Zinc for treatment + ORS', 'Vitamin A supplementation', 'IFAS for pregnant women (community)'],
                    'Bangladesh': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'Zinc for treatment + ORS', 'Vitamin A supplementation'],
                    'Nepal': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'IYCF 1', 'Vitamin A supplementation'],
                    'Comoros': ['Kangaroo mother care', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Vitamin A supplementation', 'IYCF 1'],
                    'Ethiopia': ['Kangaroo mother care', 'Zinc supplementation', 'Vitamin A supplementation', 'IYCF 1', 'IFAS for pregnant women (community)'],
                    'Malawi': ['Kangaroo mother care', 'IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)'],
                    'Mozambique': ['Kangaroo mother care', 'IYCF 1', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'Vitamin A supplementation'],
                    'Benin': ['Kangaroo mother care', 'Zinc supplementation', 'IYCF 1', 'Vitamin A supplementation', 'Zinc for treatment + ORS'],
                    'The Gambia': ['Kangaroo mother care', 'IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)'],
                    'Guinea-Bissau': ['Kangaroo mother care', 'Vitamin A supplementation', 'IYCF 1', 'Zinc supplementation', 'IFAS for pregnant women (community)'],
                    'Mauritania': ['Zinc supplementation', 'Vitamin A supplementation', 'IYCF 1', 'Zinc for treatment + ORS', 'Kangaroo mother care'],
                    'Senegal': ['Kangaroo mother care', 'Zinc supplementation', 'Vitamin A supplementation', 'Zinc for treatment + ORS', 'IFAS for pregnant women (community)'],
                    'Cambodia': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'Zinc for treatment + ORS', 'IYCF 1'],
                    'Laos': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'Zinc for treatment + ORS', 'Vitamin A supplementation'],
                    'Angola': ['Kangaroo mother care', 'Zinc for treatment + ORS', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Vitamin A supplementation'],
                    'Burundi': ['Kangaroo mother care', 'IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)'],
                    'Somalia': ['Kangaroo mother care', 'IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'Zinc for treatment + ORS'],
                    'Tanzania': ['Kangaroo mother care', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'IYCF 1', 'IFA fortification of maize'],
                    'Eswatini': ['Kangaroo mother care', 'Zinc for treatment + ORS', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)'],
                    'Zimbabwe': ['Kangaroo mother care', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Vitamin A supplementation', 'Zinc for treatment + ORS'],
                    'Cote dIvoire': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'Zinc for treatment + ORS', 'Zinc supplementation', 'Vitamin A supplementation'],
                    'Ghana': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'Zinc for treatment + ORS', 'Zinc supplementation', 'IFA fortification of maize'],
                    'Niger': ['Kangaroo mother care', 'IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'Zinc for treatment + ORS'],
                    'Nigeria': ['Kangaroo mother care', 'Zinc for treatment + ORS', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'Vitamin A supplementation'],
                    'Thailand': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'Zinc for treatment + ORS', 'Zinc supplementation', 'IFA fortification of maize'],
                    'Vietnam': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'IYCF 1', 'IFA fortification of maize'],
                    'North Korea': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'IYCF 1', 'Zinc for treatment + ORS'],
                    'Uzbekistan': ['IFAS for pregnant women (community)', 'Zinc supplementation', 'IFA fortification of maize', 'Kangaroo mother care', 'IYCF 1'],
                    'Saint Lucia': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'IFA fortification of maize', 'Zinc for treatment + ORS', 'Zinc supplementation'],
                    'Romania': ['Kangaroo mother care', 'IFA fortification of maize', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'Zinc for treatment + ORS'],
                    'Russian Federation': ['IFA fortification of maize', 'IFAS for pregnant women (community)', 'Kangaroo mother care', 'Zinc supplementation', 'Zinc for treatment + ORS'],
                    'Armenia': ['IFAS for pregnant women (community)', 'Kangaroo mother care', 'IFA fortification of maize', 'Zinc supplementation', 'Zinc for treatment + ORS'],
                    'Azerbaijan': ['IFAS for pregnant women (community)', 'Kangaroo mother care', 'IFA fortification of maize', 'Zinc supplementation', 'Zinc for treatment + ORS'],
                    'Bulgaria': ['Kangaroo mother care', 'IFA fortification of maize', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'Zinc for treatment + ORS'],
                    'Montenegro': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'IFA fortification of maize'],
                    'Ukraine': ['IFAS for pregnant women (community)', 'IFA fortification of maize', 'Kangaroo mother care', 'Zinc supplementation', 'IYCF 1'],
                    'Belize': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'IFA fortification of maize', 'Zinc for treatment + ORS', 'Zinc supplementation'],
                    'Guyana': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'IFA fortification of maize', 'Zinc for treatment + ORS', 'Zinc supplementation'],
                    'Jamaica': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'IFA fortification of maize', 'Zinc for treatment + ORS', 'Zinc supplementation'],
                    'Georgia': ['Kangaroo mother care', 'IFA fortification of maize', 'IFAS for pregnant women (community)', 'Zinc for treatment + ORS', 'Zinc supplementation'],
                    'Bosnia and Herzegovina': ['Kangaroo mother care', 'IFA fortification of maize', 'IFAS for pregnant women (community)', 'Zinc for treatment + ORS'],
                    'Serbia': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'IFA fortification of maize'],
                    'Suriname': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'IFA fortification of maize', 'Zinc for treatment + ORS', 'Zinc supplementation'],
                    'Saint Vincent and the Grenadines': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'IFA fortification of maize', 'Zinc for treatment + ORS', 'Zinc supplementation'],
                    'Brazil': ['IFA fortification of maize', 'Kangaroo mother care', 'IFAS for pregnant women (community)', 'Zinc for treatment + ORS', 'Zinc supplementation'],
                    'Cuba': ['IFA fortification of maize', 'IFAS for pregnant women (community)', 'Kangaroo mother care', 'Zinc for treatment + ORS', 'Zinc supplementation'],
                    'Belarus': ['IFA fortification of maize', 'IFAS for pregnant women (community)', 'Kangaroo mother care'],
                    'Burkina Faso': ['Kangaroo mother care', 'Zinc supplementation', 'IYCF 1', 'IFAS for pregnant women (community)', 'Zinc for treatment + ORS'],
                    'Rwanda': ['Kangaroo mother care', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'IYCF 1', 'Zinc for treatment + ORS'],
                    'Yemen': ['Kangaroo mother care', 'Vitamin A supplementation', 'Zinc supplementation', 'Zinc for treatment + ORS', 'IFAS for pregnant women (community)'],
                    'Afghanistan': ['Kangaroo mother care', 'IYCF 1', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Vitamin A supplementation'],
                    'South Sudan': ['Kangaroo mother care', 'IYCF 1', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)'],
                    'Congo': ['Kangaroo mother care', 'Zinc for treatment + ORS', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'Vitamin A supplementation'],
                    'Kenya': ['Kangaroo mother care', 'Zinc for treatment + ORS', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Vitamin A supplementation'],
                    'Uganda': ['Kangaroo mother care', 'Zinc supplementation', 'IYCF 1', 'IFAS for pregnant women (community)', 'Vitamin A supplementation'],
                    'Zambia': ['Kangaroo mother care', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Zinc for treatment + ORS', 'Vitamin A supplementation'],
                    'Cameroon': ['Kangaroo mother care', 'Zinc for treatment + ORS', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)'],
                    'Guinea': ['Kangaroo mother care', 'Zinc supplementation', 'IYCF 1', 'Vitamin A supplementation', 'Zinc for treatment + ORS'],
                    'Togo': ['Kangaroo mother care', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Zinc for treatment + ORS', 'Vitamin A supplementation'],
                    'Myanmar': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'Zinc for treatment + ORS', 'Vitamin A supplementation'],
                    'Libya': ['Kangaroo mother care', 'IFA fortification of maize', 'IFAS for pregnant women (community)', 'Zinc for treatment + ORS', 'Zinc supplementation'],
                    'Grenada': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'IFA fortification of maize', 'Zinc supplementation', 'Zinc for treatment + ORS'],
                    'Costa Rica': ['Kangaroo mother care', 'IFA fortification of maize', 'IFAS for pregnant women (community)', 'Zinc for treatment + ORS', 'Zinc supplementation'],
                    'Mauritius': ['Kangaroo mother care', 'IFAS for pregnant women (community)'],
                    'Turkey': ['Kangaroo mother care', 'IFA fortification of maize', 'IFAS for pregnant women (community)', 'Zinc for treatment + ORS', 'Zinc supplementation'],
                    'Malaysia': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'IFA fortification of maize', 'Zinc for treatment + ORS', 'Zinc supplementation'],
                    'Timor-Leste': ['Kangaroo mother care', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Zinc for treatment + ORS', 'Vitamin A supplementation'],
                    'Kiribati': ['Kangaroo mother care', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'IYCF 1', 'Vitamin A supplementation'],
                    'Federated States of Micronesia': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'IYCF 1', 'Vitamin A supplementation'],
                    'Solomon Islands': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'Zinc for treatment + ORS', 'Vitamin A supplementation'],
                    'Syria': ['Kangaroo mother care', 'IFA fortification of maize', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'IYCF 1'],
                    'Bhutan': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'IFA fortification of maize', 'Zinc supplementation', 'Zinc for treatment + ORS'],
                    'Djibouti': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'Zinc for treatment + ORS', 'Vitamin A supplementation'],
                    'Sri Lanka': ['Kangaroo mother care', 'IFA fortification of maize', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'IYCF 1'],
                    'Fiji': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'Zinc for treatment + ORS', 'Zinc supplementation', 'Vitamin A supplementation'],
                    'Kyrgyzstan': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'IFA fortification of maize', 'Zinc for treatment + ORS'],
                    'Albania': ['Kangaroo mother care', 'IFA fortification of maize', 'IFAS for pregnant women (community)', 'Zinc supplementation'],
                    'Moldova': ['IFAS for pregnant women (community)', 'IFA fortification of maize', 'Kangaroo mother care', 'Zinc supplementation', 'IYCF 1'],
                    'Colombia': ['Kangaroo mother care', 'IFA fortification of maize', 'IFAS for pregnant women (community)', 'Zinc for treatment + ORS', 'Zinc supplementation'],
                    'El Salvador': ['Kangaroo mother care', 'IFA fortification of maize', 'IFAS for pregnant women (community)', 'Zinc for treatment + ORS', 'Zinc supplementation'],
                    'Honduras': ['Kangaroo mother care', 'Zinc for treatment + ORS', 'IFAS for pregnant women (community)', 'IFA fortification of maize', 'Vitamin A supplementation'],
                    'Iran': ['Kangaroo mother care', 'IFA fortification of maize', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'Zinc for treatment + ORS'],
                    'Jordan': ['Kangaroo mother care', 'IFA fortification of maize', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'Zinc for treatment + ORS'],
                    'Lebanon': ['Kangaroo mother care', 'IFA fortification of maize', 'IFAS for pregnant women (community)', 'Zinc for treatment + ORS', 'Zinc supplementation'],
                    'Palestine': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'IFA fortification of maize', 'Zinc supplementation', 'Zinc for treatment + ORS'],
                    'Lesotho': ['Kangaroo mother care', 'Zinc for treatment + ORS', 'Zinc supplementation', 'Vitamin A supplementation', 'IFAS for pregnant women (community)'],
                    'China': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'Zinc for treatment + ORS', 'IFA fortification of maize'],
                    'Samoa': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'IYCF 1', 'IFA fortification of maize'],
                    'Vanuatu': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'Zinc for treatment + ORS', 'Vitamin A supplementation'],
                    'Mongolia': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'Zinc for treatment + ORS', 'IFA fortification of maize'],
                    'Tajikistan': ['Kangaroo mother care', 'Zinc supplementation', 'Zinc for treatment + ORS', 'Vitamin A supplementation', 'IFAS for pregnant women (community)'],
                    'Bolivia': ['Kangaroo mother care', 'IFA fortification of maize', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'Zinc for treatment + ORS'],
                    'Ecuador': ['Kangaroo mother care', 'IFA fortification of maize', 'IFAS for pregnant women (community)', 'Zinc for treatment + ORS', 'Zinc supplementation'],
                    'Peru': ['Kangaroo mother care', 'IFA fortification of maize', 'IFAS for pregnant women (community)', 'Zinc for treatment + ORS', 'Zinc supplementation'],
                    'Nicaragua': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'IFA fortification of maize', 'Zinc supplementation', 'Zinc for treatment + ORS'],
                    'Paraguay': ['Kangaroo mother care', 'IFA fortification of maize', 'IFAS for pregnant women (community)', 'Zinc for treatment + ORS', 'Zinc supplementation'],
                    'Algeria': ['Kangaroo mother care', 'IFA fortification of maize', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'Zinc for treatment + ORS'],
                    'Egypt': ['Kangaroo mother care', 'IFA fortification of maize', 'Zinc for treatment + ORS', 'Zinc supplementation', 'IFAS for pregnant women (community)'],
                    'Morocco': ['Kangaroo mother care', 'IFA fortification of maize', 'Zinc for treatment + ORS', 'IFAS for pregnant women (community)', 'Zinc supplementation'],
                    'Tunisia': ['Kangaroo mother care', 'IFA fortification of maize', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'Zinc for treatment + ORS'],
                    'Cape Verde': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'IFA fortification of maize', 'Zinc supplementation', 'Zinc for treatment + ORS'],
                    'Kazakhstan': ['Kangaroo mother care', 'IFA fortification of maize', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'Zinc for treatment + ORS'],
                    'Macedonia': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'IFA fortification of maize', 'Zinc supplementation', 'Zinc for treatment + ORS'],
                    'Dominican Republic': ['Kangaroo mother care', 'IFA fortification of maize', 'IFAS for pregnant women (community)', 'Zinc for treatment + ORS', 'Zinc supplementation'],
                    'Democratic Republic of the Congo': ['Kangaroo mother care', 'Zinc supplementation', 'IYCF 1', 'Vitamin A supplementation', 'Zinc for treatment + ORS'],
                    'Chad': ['Kangaroo mother care', 'Vitamin A supplementation', 'Zinc supplementation', 'IYCF 1', 'Zinc for treatment + ORS'],
                    'Liberia': ['Kangaroo mother care', 'Vitamin A supplementation', 'IYCF 1', 'Zinc supplementation', 'Zinc for treatment + ORS'],
                    'Central African Republic': ['Kangaroo mother care', 'Vitamin A supplementation', 'Zinc supplementation', 'IYCF 1', 'Zinc for treatment + ORS'],
                    'Namibia': ['Kangaroo mother care', 'Zinc for treatment + ORS', 'Zinc supplementation', 'IFAS for pregnant women (community)', 'Vitamin A supplementation'],
                    'Tonga': ['Kangaroo mother care', 'IFAS for pregnant women (community)', 'Zinc supplementation', 'Zinc for treatment + ORS', 'IFA fortification of maize'],
                    'Sudan': ['Kangaroo mother care', 'IFA fortification of maize', 'Zinc for treatment + ORS', 'Zinc supplementation', 'Vitamin A supplementation'],
                    'Guatemala': ['Kangaroo mother care', 'Zinc for treatment + ORS', 'IFAS for pregnant women (community)', 'IFA fortification of maize', 'Zinc supplementation'],
                    'Venezuela': ['Kangaroo mother care', 'IFA fortification of maize', 'IFAS for pregnant women (community)', 'Zinc for treatment + ORS', 'Zinc supplementation']}


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
                                      (np.sum(new_baseline.model.child_anaemic) - np.sum(p.results['scens'][-1].model.child_anaemic))
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
        objective_CE.append(effectiveness)
        objective_cost.append((np.sum(p.results['scens'][-1].programs[prog].annual_spend) -
                              (len(p.results['scens'][-1].programs[prog].annual_spend)) *
                              p.results['scens'][-1].programs[prog].annual_spend[0]))
        if objective == 'stunting':
            objective_impact.append(np.sum(baseline.model.stunted) - np.sum(p.results['scens'][-1].model.stunted))
        elif objective == 'wasting':
            objective_impact.append(np.sum(baseline.model.wasted) - np.sum(p.results['scens'][-1].model.wasted))
        elif objective == 'anaemia':
            objective_impact.append(np.sum(baseline.model.child_anaemic) - np.sum(p.results['scens'][-1].model.child_anaemic))
        elif objective == 'mortality':
            objective_impact.append(np.sum(baseline.model.child_deaths) - np.sum(p.results['scens'][-1].model.child_deaths))
        new_baseline = p.results['scens'][-1]
        #del programs[programs.keys()[location]] # delete most CE program for next round
    objective_progs = effective_progs.keys()
    return objective_CE, objective_cost, objective_impact, objective_progs

'''Main function to run CE analysis for all outcomes by country'''
def run_analysis(country):
    from nutrition import project
    cov = 0.95
    prog_list = ['Balanced energy-protein supplementation', 'Calcium supplementation',
                 'Delayed cord clamping', 'IFA fortification of maize',
                 'IFA fortification of rice', 'IFA fortification of wheat flour',
                 'IFAS for pregnant women (community)',
                 'Iron and iodine fortification of salt', 'IYCF 1', 'Kangaroo mother care',
                 'Lipid-based nutrition supplements',
                 'Micronutrient powders',
                 'Multiple micronutrient supplementation', 'Zinc for treatment + ORS',
                 'Public provision of complementary foods', 'Treatment of SAM', 'Vitamin A supplementation',
                 'Zinc supplementation']

    stunt_progs = sc.odict({'Balanced energy-protein supplementation': cov,
                            'IFAS for pregnant women (community)': cov,
                            'IYCF 1': cov, 'Kangaroo mother care': cov, 'Lipid-based nutrition supplements': cov,
                            'Multiple micronutrient supplementation': cov,
                            'Zinc for treatment + ORS': cov, 'Public provision of complementary foods': cov,
                            'Treatment of SAM': cov,
                            'Vitamin A supplementation': cov, 'Zinc supplementation': cov})
    wast_progs = sc.odict({'Balanced energy-protein supplementation': cov,
                           'IFAS for pregnant women (community)': cov,
                           'IYCF 1': cov, 'Kangaroo mother care': cov, 'Lipid-based nutrition supplements': cov,
                           'Multiple micronutrient supplementation': cov,
                           'Zinc for treatment + ORS': cov, 'Public provision of complementary foods': cov,
                           'Treatment of SAM': cov,
                           'Vitamin A supplementation': cov, 'Zinc supplementation': cov})
    anaem_progs = sc.odict({'Delayed cord clamping': cov, 'IFA fortification of maize': cov,
                            'Iron and iodine fortification of salt': cov,
                            'IYCF 1': cov, 'Kangaroo mother care': cov, 'Lipid-based nutrition supplements': cov,
                            'Micronutrient powders': cov, 'Zinc for treatment + ORS': cov,
                            'Public provision of complementary foods': cov,
                            'Treatment of SAM': cov, 'Vitamin A supplementation': cov, 'Zinc supplementation': cov})
    mort_progs = sc.odict({'IFA fortification of maize': cov,
                           'IFAS for pregnant women (community)': cov,
                           'IYCF 1': cov, 'Kangaroo mother care': cov, 'Lipid-based nutrition supplements': cov,
                           'Multiple micronutrient supplementation': cov,
                           'Zinc for treatment + ORS': cov, 'Public provision of complementary foods': cov,
                           'Treatment of SAM': cov,
                           'Vitamin A supplementation': cov, 'Zinc supplementation': cov})

    tol = [20000, 200000, 50000, 150000] # CE thresholds for each outcome
    p = project.Project(country + ' scaled up')
    p.load_data(country='lb_costed_baseline_' + country, name=country, time_trend=False)
    baseline = p.run_baseline(country, prog_list)
    stunting_CE, stunting_cost, stunting_impact, best_stunting_progs = calc_CE(country, 'stunting', p, baseline,
                                                                               stunt_progs, prog_list, tol[0])
    wasting_CE, wasting_cost, wasting_impact, best_wasting_progs = calc_CE(country, 'wasting', p, baseline,
                                                                           wast_progs, prog_list, tol[1])
    anaemia_CE, anaemia_cost, anaemia_impact, best_anaemia_progs = calc_CE(country, 'anaemia', p, baseline,
                                                                               anaem_progs, prog_list, tol[2])
    mortality_CE, mortality_cost, mortality_impact, best_mortality_progs = calc_CE(country, 'mortality', p, baseline,
                                                                               mort_progs, prog_list, tol[3])
    CE_data = [[stunting_CE, stunting_cost, stunting_impact, best_stunting_progs],
               [wasting_CE, wasting_cost, wasting_impact, best_wasting_progs],
               [anaemia_CE, anaemia_cost, anaemia_impact, best_anaemia_progs],
               [mortality_CE, mortality_cost, mortality_impact, best_mortality_progs]]
    return CE_data
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
CE_outputs = run_parallel(run_analysis, countries, 8)

for c, country in enumerate(countries):
    CE_data[country] = CE_outputs[c]
print(CE_data)

CE_book = xw.Workbook('LBC_Country_CE_23092019.xlsx')
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








