import nutrition.ui as nu
import sciris as sc
from scipy import special as spec

time_trends = False
type = 'baseline'
type = 'scaled up'
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
                    'Zinc for treatment + ORS': cov, 'Zinc supplementation': cov}) #, 'WASH: Handwashing': cov,
                    #'WASH: Hygenic disposal': cov, 'WASH: Improved sanitation': cov, 'WASH: Improved water source': cov,
                    #'WASH: Piped water': cov})
prog_list = sc.dcp(progval.keys())
#progval = sc.odict({'IYCF 1': cov, 'Zinc supplementation': cov, 'Vitamin A supplementation': cov,
                    #'Cash transfers': cov, 'Micronutrient powders': cov, 'Delayed cord clamping': cov,
                    #'Iron and iodine fortification of salt': cov, 'Kangaroo mother care': cov,
                    #'IFA fortification of maize': cov, 'Treatment of SAM': cov})

#progval = sc.odict()
total = spec.comb(len(progval.keys()), 1) # + spec.comb(len(progval.keys()), 2) + spec.comb(len(progval.keys()), 3)
prog_combs = []
for i in list(range(int(spec.comb(len(progval.keys()), 1)))):
    prog_combs.append(progval.keys()[i])

#for i in list(range(int(spec.comb(len(progval.keys()), 1)) - 1)):
#    for j in list(range(i + 1, int(spec.comb(len(progval.keys()), 1)))):
        #prog_combs.append([progval.keys()[i], progval.keys()[j]])
'''
for i in list(range(int(spec.comb(len(progval.keys()), 1)) - 2)):
    for j in list(range(i + 1, int(spec.comb(len(progval.keys()), 1)) - 1)):
        for k in list(range(j + 1, int(spec.comb(len(progval.keys()), 1)))):
            prog_combs.append([progval.keys()[i], progval.keys()[j], progval.keys()[k]])
'''
prog_names = sc.dcp(prog_combs)
name_list = ['Bal EP', 'Ca supp', 'Cash', 'Delay CC', 'IFA maize', 'IFA rice', 'IFA wheat', 'IFAS comm',
             'IFAS HF', 'IFAS ret', 'IFAS sch', 'IFAS PW com', 'IFAS PW HF', 'IPTp', 'FE + I', 'IYCF 1',
             'KMC', 'Lipid', 'Bednets', 'Mg E', 'Mg PE', 'MNP', 'MMS', 'ORS', 'PPCF', 'Treat SAM',
             'Vit A', 'Zn + ORS', 'Zn supp']
for q, prog in enumerate(prog_names):
    if isinstance(prog, str):
        for r, ram in enumerate(prog_list):
            if prog == ram:
                prog_names[q] = name_list[r]
    else:
        for i, item in enumerate(prog):
            for r, ram in enumerate(prog_list):
                if item == ram:
                    prog_names[q][i] = name_list[r]

count = 1
p = nu.Project('Global_' + type)
scen_list = []
print(len(prog_combs))
for prog in prog_combs[24:]:
    for country in country_list:
        # load country
        if count <= int(spec.comb(len(progval.keys()), 1)):
            p.load_data(country='baseline_' + country, name=country + " " + prog, time_trend=time_trends)
            kwargs = {'name': country,
                      'model_name': country + " " + prog,
                      'scen_type': 'coverage',
                      'progvals': sc.odict({prog: cov})}
        elif count <= int(spec.comb(len(progval.keys()), 1) + spec.comb(len(progval.keys()), 2)):
            p.load_data(country='baseline_' + country, name=country + " " + prog[0] + " " + prog[1], time_trend=time_trends)
            kwargs = {'name': country,
                      'model_name': country + " " + prog[0] + " " + prog[1],
                      'scen_type': 'coverage',
                      'progvals': sc.odict({prog[0]: cov, prog[1]: cov})}
        else:
            p.load_data(country='baseline_' + country, name=country + " " + prog[0] + " " + prog[1] + " " + prog[2], time_trend=time_trends)
            kwargs = {'name': country,
                      'model_name': country + " " + prog[0] + " " + prog[1] + " " + prog[2],
                      'scen_type': 'coverage',
                      'progvals': sc.odict({prog[0]: cov, prog[1]: cov, prog[2]: cov})}
        #scen_list.append(nu.make_scens([kwargs]))
        scen_list = nu.make_scens([kwargs])
        p.add_scens(scen_list)
    p.run_scens_plus(prog_list, prog)
    p.write_results(filename='Pop_global' + type + '_output_' + prog + '.xlsx')
    count += 1
    '''
    p.add_scens_collected(scen_list)
    p.run_scens_collected()
    p.write_results_collected(int(total), len(country_list), filename='Global_' + type + '_output_test.xlsx', short_names=prog_names)
    '''






