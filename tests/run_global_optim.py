import nutrition.ui as nu
from nutrition.optimization import Optim
from nutrition.geospatial import Geospatial
import sciris as sc

time_trends = False
# initialise project
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

malaria_list = ['Cambodia', 'Indonesia', 'Laos', 'Myanmar',
                'Philippines', 'Thailand', 'Vietnam', 'Papua New Guinea', 'Haiti', 'Guatemala', 'Iraq',
                'Libya', 'Yemen', 'Afghanistan', 'Bangladesh',
                'India', 'Nepal', 'Pakistan', 'Angola', 'Central African Republic', 'Congo',
                'Democratic Republic of the Congo', 'Equatorial Guinea', 'Gabon', 'Burundi', 'Comoros',
                'Ethiopia', 'Kenya', 'Madagascar', 'Malawi', 'Mozambique', 'Rwanda', 'Somalia', 'Tanzania',
                'Uganda', 'Zambia', 'Botswana', 'Namibia', 'South Africa', 'Eswatini', 'Zimbabwe', 'Benin',
                'Burkina Faso', 'Cameroon', 'Chad', 'Cote dIvoire', 'The Gambia', 'Ghana', 'Guinea',
                'Guinea-Bissau', 'Liberia', 'Mali', 'Mauritania', 'Niger', 'Nigeria', 'Sao Tome and Principe', 'Senegal',
                'Sierra Leone', 'Togo', 'South Sudan', 'Sudan']

poverty_list = ['China', 'North Korea', 'Cambodia', 'Indonesia', 'Laos', 'Maldives', 'Myanmar',
                'Philippines', 'Sri Lanka', 'Timor-Leste', 'Vietnam', 'Fiji', 'Kiribati',
                'Federated States of Micronesia', 'Papua New Guinea', 'Samoa', 'Solomon Islands', 'Tonga', 'Vanuatu',
                'Armenia', 'Kyrgyzstan', 'Mongolia', 'Tajikistan', 'Turkmenistan',
                'Uzbekistan', 'Albania', 'Bosnia and Herzegovina', 'Bulgaria', 'Macedonia', 'Romania',
                'Serbia', 'Moldova', 'Ukraine', 'Belize', 'Cuba', 'Dominican Republic',
                'Grenada', 'Guyana', 'Haiti', 'Jamaica', 'Saint Lucia', 'Saint Vincent and the Grenadines', 'Suriname',
                'Bolivia', 'Ecuador', 'Peru', 'Colombia', 'Costa Rica', 'El Salvador', 'Guatemala', 'Honduras',
                'Nicaragua', 'Venezuela', 'Brazil', 'Paraguay', 'Egypt', 'Iran', 'Iraq', 'Jordan',
                'Libya', 'Morocco', 'Palestine', 'Tunisia', 'Turkey', 'Yemen', 'Afghanistan', 'Bangladesh',
                'Bhutan', 'India', 'Nepal', 'Pakistan', 'Angola', 'Central African Republic', 'Congo',
                'Democratic Republic of the Congo', 'Gabon', 'Burundi', 'Comoros', 'Djibouti',
                'Ethiopia', 'Kenya', 'Madagascar', 'Malawi', 'Mozambique', 'Rwanda', 'Somalia', 'Tanzania',
                'Uganda', 'Zambia', 'Botswana', 'Lesotho', 'Namibia', 'South Africa', 'Eswatini', 'Zimbabwe', 'Benin',
                'Burkina Faso', 'Cameroon', 'Cape Verde', 'Chad', 'Cote dIvoire', 'The Gambia', 'Ghana', 'Guinea',
                'Guinea-Bissau', 'Liberia', 'Mali', 'Mauritania', 'Niger', 'Nigeria', 'Sao Tome and Principe', 'Senegal',
                'Sierra Leone', 'Togo', 'Georgia', 'South Sudan', 'Sudan']

p = nu.Project('Global_optim')
# run simulation for each country
for country in country_list[0:3]:
    # load country
    p.load_data(country='optim_' + country, name='Global_optim_' + country, time_trend=time_trends)

    if country in malaria_list and country in poverty_list:
        kwargs = {'name': country,
                   'model_name': 'Global_optim_' + country,
                   'mults': [1],
                   'weights': sc.odict({'thrive': 1}),
                   'prog_set': ['Balanced energy-protein supplementation', 'Calcium supplementation', 'Cash transfers',
                                'Delayed cord clamping', 'IFA fortification of maize',
                                'IFA fortification of rice', 'IFA fortification of wheat flour', 'IFAS (community)',
                                'IFAS (health facility)', 'IFAS (retailer)', 'IFAS (school)',
                                'IFAS for pregnant women (community)', 'IFAS for pregnant women (health facility)',
                                'IPTp', 'Iron and iodine fortification of salt', 'IYCF 1', 'Kangaroo mother care',
                                'Lipid-based nutrition supplements', 'Long-lasting insecticide-treated bednets',
                                'Mg for eclampsia', 'Mg for pre-eclampsia', 'Micronutrient powders',
                                'Multiple micronutrient supplementation', 'Oral rehydration salts',
                                'Public provision of complementary foods', 'Treatment of SAM', 'Vitamin A supplementation',
                                'WASH: Handwashing', 'WASH: Hygenic disposal', 'WASH: Improved sanitation',
                                'WASH: Improved water source', 'WASH: Piped water', 'Zinc for treatment + ORS',
                                'Zinc supplementation'],
                   'fix_curr': False,
                   'add_funds': 0}
    elif country in malaria_list:
        kwargs = {'name': country,
                   'model_name': 'Global_optim_' + country,
                   'mults': [1],
                   'weights': sc.odict({'thrive': 1}),
                   'prog_set': ['Calcium supplementation',
                                'Delayed cord clamping', 'IFA fortification of maize',
                                'IFA fortification of rice', 'IFA fortification of wheat flour', 'IFAS (community)',
                                'IFAS (health facility)', 'IFAS (retailer)', 'IFAS (school)',
                                'IFAS for pregnant women (community)', 'IFAS for pregnant women (health facility)',
                                'IPTp', 'Iron and iodine fortification of salt', 'IYCF 1', 'Kangaroo mother care',
                                 'Long-lasting insecticide-treated bednets',
                                'Mg for eclampsia', 'Mg for pre-eclampsia', 'Micronutrient powders',
                                'Multiple micronutrient supplementation', 'Oral rehydration salts',
                                 'Treatment of SAM', 'Vitamin A supplementation',
                                'WASH: Handwashing', 'WASH: Hygenic disposal', 'WASH: Improved sanitation',
                                'WASH: Improved water source', 'WASH: Piped water', 'Zinc for treatment + ORS',
                                'Zinc supplementation'],
                   'fix_curr': False,
                   'add_funds': 0}
    elif country in poverty_list:
        kwargs = {'name': country,
                   'model_name': 'Global_optim_' + country,
                   'mults': [1],
                   'weights': sc.odict({'thrive': 1}),
                   'prog_set': ['Balanced energy-protein supplementation', 'Calcium supplementation', 'Cash transfers',
                                'Delayed cord clamping', 'IFA fortification of maize',
                                'IFA fortification of rice', 'IFA fortification of wheat flour', 'IFAS (community)',
                                'IFAS (health facility)', 'IFAS (retailer)', 'IFAS (school)',
                                'IFAS for pregnant women (community)', 'IFAS for pregnant women (health facility)',
                                'Iron and iodine fortification of salt', 'IYCF 1', 'Kangaroo mother care',
                                'Lipid-based nutrition supplements',
                                'Mg for eclampsia', 'Mg for pre-eclampsia', 'Micronutrient powders',
                                'Multiple micronutrient supplementation', 'Oral rehydration salts',
                                'Public provision of complementary foods', 'Treatment of SAM', 'Vitamin A supplementation',
                                'WASH: Handwashing', 'WASH: Hygenic disposal', 'WASH: Improved sanitation',
                                'WASH: Improved water source', 'WASH: Piped water', 'Zinc for treatment + ORS',
                                'Zinc supplementation'],
                   'fix_curr': False,
                   'add_funds': 0}
    else:
        kwargs = {'name': country,
                  'model_name': 'Global_optim_' + country,
                  'mults': [1],
                  'weights': sc.odict({'thrive': 1}),
                   'prog_set': ['Calcium supplementation',
                                'Delayed cord clamping', 'IFA fortification of maize',
                                'IFA fortification of rice', 'IFA fortification of wheat flour', 'IFAS (community)',
                                'IFAS (health facility)', 'IFAS (retailer)', 'IFAS (school)',
                                'IFAS for pregnant women (community)', 'IFAS for pregnant women (health facility)',
                                'Iron and iodine fortification of salt', 'IYCF 1', 'Kangaroo mother care',
                                'Mg for eclampsia', 'Mg for pre-eclampsia', 'Micronutrient powders',
                                'Multiple micronutrient supplementation', 'Oral rehydration salts',
                                'Treatment of SAM', 'Vitamin A supplementation',
                                'WASH: Handwashing', 'WASH: Hygenic disposal', 'WASH: Improved sanitation',
                                'WASH: Improved water source', 'WASH: Piped water', 'Zinc for treatment + ORS',
                                'Zinc supplementation'],
                  'fix_curr': False,
                  'add_funds': 0}

    optims = [Optim(**kwargs)]
    p.add_optims(optims)
    p.run_optim(parallel=True)
    p.write_results(country + '_optim_output.xlsx')

# global optimisation
kwargs_global = {'name': 'Global',
          'modelnames': 'Global_optim_' + country_list,
          'weights': 'thrive',
          'fix_curr': False,
          'fix_regionalspend': False,
          'add_funds': 0,
          'prog_set': ['Balanced energy-protein supplementation', 'Calcium supplementation', 'Cash transfers',
                        'Delayed cord clamping', 'IFA fortification of maize',
                        'IFA fortification of rice', 'IFA fortification of wheat flour', 'IFAS (community)',
                        'IFAS (health facility)', 'IFAS (retailer)', 'IFAS (school)',
                        'IFAS for pregnant women (community)', 'IFAS for pregnant women (health facility)',
                        'IPTp', 'Iron and iodine fortification of salt', 'IYCF 1', 'Kangaroo mother care',
                        'Lipid-based nutrition supplements', 'Long-lasting insecticide-treated bednets',
                        'Mg for eclampsia', 'Mg for pre-eclampsia', 'Micronutrient powders',
                        'Multiple micronutrient supplementation', 'Oral rehydration salts',
                        'Public provision of complementary foods', 'Treatment of SAM', 'Vitamin A supplementation',
                        'WASH: Handwashing', 'WASH: Hygenic disposal', 'WASH: Improved sanitation',
                        'WASH: Improved water source', 'WASH: Piped water', 'Zinc for treatment + ORS',
                        'Zinc supplementation']}

geo = Geospatial(**kwargs_global)
results = p.run_geo(geo=geo, maxiter=10, swarmsize=10, maxtime=50, parallel=True)
p.write_results('global_optim_output.xlsx')

