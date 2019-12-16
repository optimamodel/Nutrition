import nutrition.ui as nu
from nutrition.project import Project
import sciris as sc

time_trends = [True, False]
type = ['baseline', 'scaled up']
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

# run simulation for each country
cov = 1.0
progval = sc.odict({'Balanced energy-protein supplementation': cov, 'Calcium supplementation': cov, 'Cash transfers': cov,
                    'Delayed cord clamping': cov, 'IFA fortification of maize': cov,
                    'IFA fortification of rice': cov, 'IFA fortification of wheat flour': cov, 'IFAS (community)': cov,
                    'IFAS (health facility)': cov, 'IFAS (retailer)': cov, 'IFAS (school)': cov,
                    'IFAS for pregnant women (community)': cov, 'IFAS for pregnant women (health facility)': cov,
                    'IPTp': cov, 'Iron and iodine fortification of salt': cov, 'IYCF 1': cov, 'Kangaroo mother care': cov,
                    'Lipid-based nutrition supplements': cov, 'Long-lasting insecticide-treated bednets': cov,
                    'Mg for eclampsia': cov, 'Mg for pre-eclampsia': cov, 'Micronutrient powders': cov,
                    'Multiple micronutrient supplementation': cov, 'Oral rehydration salts': cov,
                    'Public provision of complementary foods': cov, 'Treatment of SAM': cov, 'Vitamin A supplementation': cov,
                    'Zinc for treatment + ORS': cov, 'Zinc supplementation': cov})
prog_list = sc.dcp(progval.keys())
stunt_progval = sc.odict({'IFAS for pregnant women (community)': cov, 'IPTp': cov, 'IYCF 1': cov,
                          'Lipid-based nutrition supplements': cov, 'Vitamin A supplementation': cov,
                          'Zinc supplementation': cov})

wast_progval = sc.odict({'Cash transfers': cov, 'Vitamin A supplementation': cov, 'Zinc supplementation': cov})

anaem_progval = sc.odict({'IFA fortification of maize': cov, 'Iron and iodine fortification of salt': cov,
                          'Long-lasting insecticide-treated bednets': cov, 'Micronutrient powders': cov})

mort_progval = sc.odict({'IFA fortification of maize': cov,'IFAS for pregnant women (community)': cov,
                         'IYCF 1': cov, 'Kangaroo mother care': cov, 'Oral rehydration salts': cov,
                         'Vitamin A supplementation': cov, 'Zinc supplementation': cov})

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

#progval = sc.odict()
'''
p = Project('Global_' + type)
for c, country in enumerate(country_list):
    # load country
    p.load_data(country='baseline_' + country, name=country + " " + type, time_trend=time_trends[1])
    progset = p.models[-1].prog_info.base_progset()
    progvals = sc.odict([(prog, []) for prog in progset])
    kwargs = {'name': country,
              'model_name': country + " " + type,
              'scen_type': 'coverage',
              'progvals': mort_progval}
    scen_list = nu.make_scens([kwargs])
    p.add_scens(scen_list)
#p.run_scens()
p.run_scens_plus(prog_list, mort_progval.keys())
p.write_results('Global_mortality_' + type + '_reduced_progs.xlsx')

r = Project('Global_' + type)
for c, country in enumerate(country_list):
    # load country
    r.load_data(country='baseline_' + country, name=country + " " + type, time_trend=time_trends[1])
    progset = r.models[-1].prog_info.base_progset()
    progvals = sc.odict([(prog, []) for prog in progset])
    kwargs = {'name': country,
              'model_name': country + " " + type,
              'scen_type': 'coverage',
              'progvals': anaem_progval}
    scen_list = nu.make_scens([kwargs])
    r.add_scens(scen_list)
#p.run_scens()
r.run_scens_plus(prog_list, anaem_progval.keys())
r.write_results('Global_anaemia_' + type + '_reduced_progs.xlsx')

q = Project('Global_' + type)
for c, country in enumerate(country_list):
    # load country
    q.load_data(country='baseline_' + country, name=country + " " + type, time_trend=time_trends[1])
    progset = q.models[-1].prog_info.base_progset()
    progvals = sc.odict([(prog, []) for prog in progset])
    kwargs = {'name': country,
              'model_name': country + " " + type,
              'scen_type': 'coverage',
              'progvals': wast_progval}
    scen_list = nu.make_scens([kwargs])
    q.add_scens(scen_list)
#p.run_scens()
q.run_scens_plus(prog_list, wast_progval.keys())
q.write_results('Global_wasting_' + type + '_reduced_progs.xlsx')

s = Project('Global_' + type)
for c, country in enumerate(country_list):
    # load country
    s.load_data(country='baseline_' + country, name=country + " " + type, time_trend=time_trends[1])
    progset = s.models[-1].prog_info.base_progset()
    progvals = sc.odict([(prog, []) for prog in progset])
    kwargs = {'name': country,
              'model_name': country + " " + type,
              'scen_type': 'coverage',
              'progvals': stunt_progval}
    scen_list = nu.make_scens([kwargs])
    s.add_scens(scen_list)
#p.run_scens()
s.run_scens_plus(prog_list, stunt_progval.keys())
s.write_results('Global_stunting_' + type + '_reduced_progs.xlsx')

t = Project('Global_' + type)
for c, country in enumerate(country_list):
    # load country
    t.load_data(country='baseline_' + country, name=country + " " + type, time_trend=time_trends[1])
    progset = t.models[-1].prog_info.base_progset()
    progvals = sc.odict([(prog, []) for prog in progset])
    kwargs = {'name': country,
              'model_name': country + " " + type,
              'scen_type': 'coverage',
              'progvals': progval}
    scen_list = nu.make_scens([kwargs])
    t.add_scens(scen_list)
t.run_scens()
#t.run_scens_plus(prog_list, progval.keys())
t.write_results('Global_' + type + '_full.xlsx')
'''
#type = 'baseline'
u = Project('Global_' + type)
for c, country in enumerate(country_list):
    # load country
    u.load_data(country='costed_baseline_' + country, name=country + " " + type, time_trend=time_trends[1])
    progset = u.models[-1].prog_info.base_progset()
    progvals = sc.odict([(prog, []) for prog in progset])
    kwargs = {'name': country,
              'model_name': country + " " + type,
              'scen_type': 'coverage',
              'progvals': progvals}
    scen_list = nu.make_scens([kwargs])
    u.add_scens(scen_list)
u.run_scens()
#p.run_scens_plus(prog_list, mort_progval.keys())
u.write_results('Global_' + type + '_reduced_progs.xlsx')



