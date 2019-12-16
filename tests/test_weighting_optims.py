import nutrition.ui as nu
from nutrition.optimization import Optim
from nutrition.geospatial import Geospatial as geo
import sciris as sc
test_no = 'First'
time_trends = False
# initialise project
totalfunds = 0
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

goals = dict({'Stunting 2030': 0.0, 'Wasting 2030': 0.0, 'Child Mortality': 25/1000,
                  'Maternal Mortality': 0.7/1000})
progress = dict()
improved = dict()
adapt_weights = dict({'stunted_prev': 2, 'wasted_prev': 1, 'pw_mortrate': 0, 'child_mortrate': 0})
p = nu.Project('Global_optim')
# run simulation for each country
boc_optim = sc.odict()
boc_optims = sc.odict()
for country in country_list:
    # load country
    p.load_data(country='optim_' + country, name='Global_optim_' + country, time_trend=time_trends)
    # TODO: Another loop for weighting choices
    if country in malaria_list and country in poverty_list:
        kwargs = {'name': country,
                   'model_name': 'Global_optim_' + country,
                   'mults': [1],
                   'weights': adapt_weights,
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
                                'Zinc for treatment + ORS', 'Zinc supplementation', 'WASH: Handwashing',
                                'WASH: Hygenic disposal', 'WASH: Improved sanitation', 'WASH: Improved water source',
                                'WASH: Piped water'],
                   'fix_curr': False,
                   'add_funds': 0}
    elif country in malaria_list:
        kwargs = {'name': country,
                   'model_name': 'Global_optim_' + country,
                   'mults': [1],
                   'weights': adapt_weights,
                   'prog_set': ['Calcium supplementation',
                                'Delayed cord clamping', 'IFA fortification of maize',
                                'IFA fortification of rice', 'IFA fortification of wheat flour', 'IFAS (community)',
                                'IFAS (health facility)', 'IFAS (retailer)', 'IFAS (school)',
                                'IFAS for pregnant women (community)', 'IFAS for pregnant women (health facility)',
                                'IPTp', 'Iron and iodine fortification of salt', 'IYCF 1', 'Kangaroo mother care',
                                 'Long-lasting insecticide-treated bednets', 'Mg for eclampsia', 'Mg for pre-eclampsia',
                                'Micronutrient powders', 'Multiple micronutrient supplementation', 'Oral rehydration salts',
                                 'Treatment of SAM', 'Vitamin A supplementation', 'Zinc for treatment + ORS',
                                'Zinc supplementation', 'WASH: Handwashing', 'WASH: Hygenic disposal',
                                'WASH: Improved sanitation', 'WASH: Improved water source', 'WASH: Piped water'],
                   'fix_curr': False,
                   'add_funds': 0}
    elif country in poverty_list:
        kwargs = {'name': country,
                   'model_name': 'Global_optim_' + country,
                   'mults': [1],
                   'weights': adapt_weights,
                   'prog_set': ['Balanced energy-protein supplementation', 'Calcium supplementation', 'Cash transfers',
                                'Delayed cord clamping', 'IFA fortification of maize',
                                'IFA fortification of rice', 'IFA fortification of wheat flour', 'IFAS (community)',
                                'IFAS (health facility)', 'IFAS (retailer)', 'IFAS (school)',
                                'IFAS for pregnant women (community)', 'IFAS for pregnant women (health facility)',
                                'Iron and iodine fortification of salt', 'IYCF 1', 'Kangaroo mother care',
                                'Lipid-based nutrition supplements', 'Mg for eclampsia', 'Mg for pre-eclampsia',
                                'Micronutrient powders', 'Multiple micronutrient supplementation', 'Oral rehydration salts',
                                'Public provision of complementary foods', 'Treatment of SAM', 'Vitamin A supplementation',
                                'Zinc for treatment + ORS', 'Zinc supplementation',
                                'WASH: Handwashing', 'WASH: Hygenic disposal', 'WASH: Improved sanitation',
                                'WASH: Improved water source', 'WASH: Piped water'],
                   'fix_curr': False,
                   'add_funds': 0}
    else:
        kwargs = {'name': country,
                  'model_name': 'Global_optim_' + country,
                  'mults': [1],
                  'weights': adapt_weights,
                   'prog_set': ['Calcium supplementation', 'Delayed cord clamping', 'IFA fortification of maize',
                                'IFA fortification of rice', 'IFA fortification of wheat flour', 'IFAS (community)',
                                'IFAS (health facility)', 'IFAS (retailer)', 'IFAS (school)',
                                'IFAS for pregnant women (community)', 'IFAS for pregnant women (health facility)',
                                'Iron and iodine fortification of salt', 'IYCF 1', 'Kangaroo mother care',
                                'Mg for eclampsia', 'Mg for pre-eclampsia', 'Micronutrient powders',
                                'Multiple micronutrient supplementation', 'Oral rehydration salts',
                                'Treatment of SAM', 'Vitamin A supplementation', 'Zinc for treatment + ORS',
                                'Zinc supplementation', 'WASH: Handwashing', 'WASH: Hygenic disposal',
                                'WASH: Improved sanitation', 'WASH: Improved water source', 'WASH: Piped water'],
                  'fix_curr': False,
                  'add_funds': 0}

    optims = [Optim(**kwargs)]
    p.add_optims(optims)
    boc_optim.update({country: p.run_optim(maxiter=5, swarmsize=5, maxtime=60, parallel=False)})
    goals.update(
        {'Stunting 2025': 0.6 * p.results[country][0].model.stunted_prev[00],
                  'Wasting 2025': 0.6 * p.results[country][0].model.wasted_prev[00]})
    improved.update(
        {'Stunting 2030': p.results[country][1].model.stunted_prev[00] - p.results[country][1].model.stunted_prev[-1],
         'Wasting 2030': p.results[country][1].model.wasted_prev[00] - p.results[country][1].model.wasted_prev[-1],
         'Child Mortality': p.results[country][1].model.child_mortrate[00] - p.results[country][1].model.child_mortrate[-1],
         'Maternal Mortality': p.results[country][1].model.pw_mortrate[00] - p.results[country][1].model.pw_mortrate[-1]})
    progress.update(
        {'Stunting 2025': (p.results[country][1].model.stunted_prev[8] - goals['Stunting 2025']) / (0.4 *
                          p.results[country][0].model.stunted_prev[00]),
         'Wasting 2025': (p.results[country][1].model.wasted_prev[8] - goals['Wasting 2025']) / (0.4 *
                         p.results[country][0].model.wasted_prev[00]),
         'Stunting 2030': (p.results[country][1].model.stunted_prev[-1]) / p.results[country][0].model.stunted_prev[00],
         'Wasting 2030': (p.results[country][1].model.wasted_prev[-1]) / p.results[country][0].model.wasted_prev[00],
         'Child Mortality': (p.results[country][1].model.child_mortrate[-1] - goals['Child Mortality']) / abs(
                     p.results[country][1].model.child_mortrate[00] - goals['Child Mortality']),
         'Maternal Mortality': (p.results[country][1].model.pw_mortrate[-1] - goals['Maternal Mortality']) / abs(
                     p.results[country][1].model.pw_mortrate[00] - goals['Maternal Mortality'])})
    totalfunds += sum(p.results[country][1].model.scenario.vals[:27])

    p.write_results(country + '_optim_output.xlsx')

sc.saveobj(test_no + '_bocs.obj', boc_optims)
bocs = geo.get_bocs(boc_optims, totalfunds)

# TODO: A loop for geospatial optimisation with optimising weighting choices
'''
import os.path
if os.path.exists('bocs.obj'):  # Use this only when testing same scenarios repeatedly
    print('Loading BOCS from bocs.obj...')
    boc_optims = sc.loadobj('bocs.obj')
else:
    print('Creating BOCs afresh...')
'''