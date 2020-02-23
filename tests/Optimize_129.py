from nutrition.geospatial import Geospatial
from nutrition.project import Project
import sciris as sc

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

# Bottom 50% of countries by GDP per capita
country_list = ['Burundi', 'Somalia', 'Malawi', 'Niger', 'Central African Republic', 'Mozambique',
                'Democratic Republic of the Congo', 'Sierra Leone', 'Madagascar', 'Afghanistan', 'Togo', 'Uganda',
                'Burkina Faso', 'Chad', 'The Gambia', 'Liberia', 'Guinea-Bissau', 'Rwanda', 'Haiti', 'Ethiopia',
                'Tajikistan', 'Mali', 'Benin', 'Guinea', 'Nepal', 'Yemen', 'Tanzania', 'South Sudan', 'Mauritania',
                'Syria', 'Lesotho', 'Kyrgyzstan', 'Myanmar', 'Comoros', 'Senegal', 'Cambodia', 'Cameroon', 'Pakistan',
                'Zambia', 'Cote dIvoire', 'Bangladesh', 'Kenya', 'Zimbabwe', 'Kiribati', 'North Korea', 'Congo',
                'Sao Tome and Principe', 'Uzbekistan', 'Nigeria', 'India', 'Timor-Leste', 'Ghana', 'Solomon Islands',
                'Nicaragua', 'Vietnam', 'Laos', 'Egypt', 'Honduras', 'Ukraine', 'Papua New Guinea', 'Moldova',
                'Djibouti', 'Philippines', 'Sudan', 'Morocco']

#Stunting
prog_list = ['Balanced energy-protein supplementation',
             'IFAS for pregnant women (community)',
             'IYCF 1', 'Lipid-based nutrition supplements',
#             'Public provision of complementary foods',
             'Vitamin A supplementation',
             'Zinc supplementation']

#Wasting
#prog_list = ['Vitamin A supplementation',
#             'Zinc supplementation',
#             'Cash transfers']

#Anaemia
#prog_list = ['Lipid-based nutrition supplements',
#             'Micronutrient powders',
#             'Iron and iodine fortification of salt']

#Mortality
#prog_list = ['Kangaroo mother care',
#             'Zinc for treatment + ORS',
#             'IFAS for pregnant women (community)',
#             'Zinc supplementation',
#             'Vitamin A supplementation',
#             'IYCF 1',
#             'IFA fortification of maize',
#             'Balanced energy-protein supplementation',
#             'Public provision of complementary foods',
#             'Treatment of SAM']

#GHI
#prog_list = ['Kangaroo mother care',
#             'Zinc for treatment + ORS',
#             'IFAS for pregnant women (community)',
#             'Zinc supplementation',
#             'Vitamin A supplementation',
#             'IYCF 1',
#             'IFA fortification of maize',
#             'Balanced energy-protein supplementation',
#             'Public provision of complementary foods',
#             'Treatment of SAM',
#             'Lipid-based nutrition supplements',
#             'Micronutrient powders',
#             'Iron and iodine fortification of salt',
#             'Cash transfers']

GHI_weighting = sc.odict({'child_mortrate': 2, 'stunted_prev': 1, 'wasted_prev': 1, 'child_anaemprev': 1})

p = Project('Global_optim')

for country in country_list:
    p.load_data(country='costed_baseline_' + country, name=country, time_trend=True)

kwargs = {'name': 'test1',
              'modelnames': country_list,
              'weights': 'stunted_prev',
              'mults': [0, 0.025, 0.05, 0.075, 0.1, 0.3, 0.6, 1],
              'fix_curr': True,
              'fix_regionalspend': False,
              'add_funds': 5e9,
              'prog_set': prog_list,
              'search_type': 'mixed',
              'spectrum': True}

geo = Geospatial(**kwargs)
#results = p.run_geo(geo=geo, maxiter=1, swarmsize=1, maxtime=1, dosave=True, parallel=False)
results = p.run_geo(geo=geo, dosave=True, parallel=False)
p.write_results('gdp_stunting.xlsx')
