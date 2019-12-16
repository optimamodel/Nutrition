from nutrition.geospatial import Geospatial
from nutrition.project import Project
from nutrition.results import write_results

country_list = ['China', 'North Korea', 'Cambodia', 'Indonesia', 'Laos', 'Malaysia', 'Maldives', 'Myanmar',
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

prog_list = ['Balanced energy-protein supplementation',
             'IFAS for pregnant women (community)',
             'IYCF 1', 'Lipid-based nutrition supplements',
             'Public provision of complementary foods', 'Vitamin A supplementation',
             'Zinc supplementation']


p = Project('Global_optim')

for country in country_list[:5]:
    p.load_data(country='costed_baseline_' + country, name=country, time_trend=True)

kwargs = {'name': 'test1',
              'modelnames': country_list[:5],
              'weights': 'stunted_prev',
              'fix_curr': True,
              'fix_regionalspend': False,
              'add_funds': 1e9,
              'prog_set': prog_list,
              'search_type': 'mixed',
              'spectrum': True}

geo = Geospatial(**kwargs)
results = p.run_geo(geo=geo, maxiter=1, swarmsize=1, maxtime=1, dosave=True, parallel=False)
#results = p.run_geo(geo=geo, dosave=True, parallel=False)
p.write_results('testing.xlsx')