import sys
#sys.path.append('C:/Users/debra.tenbrink/Documents/GitHub/Nutrition/') # I assume this is where you'll be running it from?
import nutrition.ui as nu
from nutrition.optimization import Optim
from nutrition.results import write_results
from nutrition.utils import run_parallel
from functools import partial
from nutrition.project import Project
import os
import sciris as sc


def parallel_optim(region, path=None):
    p = Project('WHA optimisation')

    p.load_data(inputspath=path + region + '_input.xlsx', name=region)

    ## define custom optimization
    kwargs = {'name': region,
              'mults': [1],
              'model_name': region,
              'weights': sc.odict({'thrive': 1,
                                   'Minimize the number of wasted children': 2.91,
                                   'Minimize child mortality rate': 2.91}),
              # The available programs need to be put below, I just filled it with common ones
              'prog_set': ['Balanced energy-protein supplementation','Cash transfers','IFA fortification of wheat flour',
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
    results = p.run_optim(maxiter=50, swarmsize=15, maxtime=560, parallel=False)

    return(p)

dirname = os.path.dirname(__file__)
input_path = dirname + '/inputs/'
output_path = dirname + '/outputs/'

country_list = ['China', 'North Korea', 'Cambodia', 'Indonesia', 'Laos']#, 'Malaysia', 'Maldives', 'Myanmar',
"""                'Philippines', 'Sri Lanka', 'Thailand', 'Timor-Leste', 'Vietnam', 'Fiji', 'Kiribati',
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
"""

if __name__ == '__main__':

    run_optim = partial(parallel_optim, path=input_path)
    results = []
    proj_list = run_parallel(run_optim, country_list, num_procs=4)
    # len(region_list))
    for p in proj_list:
        for res in p.results:
            for scenres in p.results[res]:
                if scenres.name == 'Baseline':
                    scenres.name = scenres.model_name + ' ' + scenres.name
                else:
                    scenres.name = scenres.model_name
                results.append(scenres)

    write_results(results, filename=output_path + 'test.xlsx')