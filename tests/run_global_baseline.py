import nutrition.ui as nu
from nutrition.project import Project
import sciris as sc
import warnings



def run_baseline_scaleup(date, data_type, scen_type, trends):
    warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
    warnings.filterwarnings("ignore", category=RuntimeWarning)
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

    # initialise project
    # Full country list
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
    '''
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
    '''
    '''LIC list
    country_list = ['Afghanistan', 'Burundi', 'Benin', 'Burkina Faso', 'Central African Republic', 'Democratic Republic of the Congo',
                    'Comoros', 'Ethiopia', 'Guinea', 'The Gambia', 'Guinea-Bissau', 'Haiti', 'Liberia', 'Madagascar',
                    'Mali', 'Mozambique', 'Malawi', 'Niger', 'Nepal', 'North Korea', 'Rwanda', 'Senegal', 'Sierra Leone',
                     'Somalia', 'South Sudan', 'Syria', 'Chad', 'Togo', 'Tajikistan', 'Tanzania', 'Uganda', 'Yemen', 'Zimbabwe']
    '''

    ''' LMIC list
    country_list = ['Angola', 'Bangladesh', 'Bolivia', 'Bhutan', 'Cote dIvoire', 'Cameroon', 'Congo', 'Cape Verde',
                    'Djibouti', 'Egypt', 'Federated States of Micronesia', 'Georgia', 'Ghana', 'Honduras', 'Indonesia',
                    'India', 'Kenya', 'Kyrgyzstan', 'Cambodia', 'Kiribati', 'Laos', 'Sri Lanka', 'Lesotho', 'Morocco',
                    'Moldova', 'Myanmar', 'Mongolia', 'Mauritania', 'Nigeria', 'Nicaragua', 'Pakistan', 'Philippines',
                    'Papua New Guinea', 'Palestine', 'Sudan', 'Solomon Islands', 'El Salvador', 'Sao Tome and Principe',
                    'Eswatini', 'Timor-Leste', 'Tunisia', 'Ukraine', 'Uzbekistan', 'Vietnam', 'Vanuatu', 'Zambia']
    '''
    ''' UMIC list
    country_list = ['Albania', 'Armenia', 'Azerbaijan', 'Bulgaria', 'Bosnia and Herzegovina', 'Belarus', 'Belize', 
                    'Brazil', 'Botswana', 'China', 'Colombia', 'Costa Rica', 'Cuba', 'Dominican Republic', 'Algeria', 
                    'Ecuador', 'Fiji', 'Gabon', 'Equatorial Guinea', 'Grenada', 'Guatemala', 'Guyana', 'Iran', 
                    'Iraq', 'Jamaica', 'Jordan', 'Kazakhstan', 'Lebanon', 'Libya', 'Saint Lucia', 'Maldives', 
                    'Macedonia', 'Montenegro', 'Mauritius', 'Malaysia', 'Namibia', 'Peru', 'Paraguay', 'Romania', 
                    'Russian Federation', 'Serbia', 'Suriname', 'Thailand', 'Turkmenistan', 'Tonga',
                    'Saint Vincent and the Grenadines', 'Venezuela', 'Samoa', 'Turkey', 'South Africa']
    '''

    # run simulation for each country
    cov = 1.0
    '''Including nutrition sensitive interventions (IPTp, LLINs, Cash transfers) '''
    progvals = sc.odict({'Balanced energy-protein supplementation': cov, 'Calcium supplementation': cov, 'Cash transfers': cov,
                        'Delayed cord clamping': cov, 'IFA fortification of maize': cov,
                        'IFAS (community)': cov,
                        #'IFAS for pregnant women (community)': cov,
                        'IPTp': cov, 'Iron and iodine fortification of salt': cov, 'IYCF 1': cov, 'Kangaroo mother care': cov,
                        'Lipid-based nutrition supplements': cov, 'Long-lasting insecticide-treated bednets': cov,
                        'Multiple micronutrient supplementation': cov,
                        'Public provision of complementary foods': cov, 'Treatment of SAM': cov, 'Vitamin A supplementation': cov,
                        'Zinc for treatment + ORS': cov})

    '''Nutrition specific interventions only
    progvals = sc.odict(
        {'Balanced energy-protein supplementation': cov, 'Calcium supplementation': cov,
         'Delayed cord clamping': cov, 'IFA fortification of maize': cov,
         'IFAS (community)': cov,
         #'IFAS for pregnant women (community)': cov,
         'Iron and iodine fortification of salt': cov, 'IYCF 1': cov, 'Kangaroo mother care': cov,
         'Lipid-based nutrition supplements': cov,
         'Multiple micronutrient supplementation': cov,
         'Public provision of complementary foods': cov, 'Treatment of SAM': cov, 'Vitamin A supplementation': cov,
         'Zinc for treatment + ORS': cov})
    '''
    prog_list = sc.dcp(progvals.keys())

    #progval = sc.odict()

    type = scen_type.lower()
    time_trend = trends
    if time_trend:
        trends_name = 'trends_'
    else:
        trends_name = ''

    u = Project('Global_' + type)
    for c, country in enumerate(country_list):
        # load country
        if data_type.lower() == 'jhe':
            loc_name = 'JHE stunting wasting/jhe_'
        else:
            loc_name = 'jme_'
        u.load_data(country=loc_name + 'costed_baseline_' + country, name=country + " " + type, time_trend=time_trend)
        if type == 'baseline':
            progset = u.models[-1].prog_info.base_progset()
            progvals = sc.odict([(prog, []) for prog in progset])
        elif type == 'scaleup':
            for p, prog in enumerate(prog_list):
                progvals[prog] = interp_cov(u, prog_list[p], [2018, 2024], 0.95)
        kwargs = {'name': country,
                  'model_name': country + " " + type,
                  'scen_type': 'coverage',
                  'progvals': progvals}
        scen_list = nu.make_scens([kwargs])
        u.add_scens(scen_list)
    u.run_scens()
    #p.run_scens_plus(prog_list, mort_progval.keys())
    if data_type.lower() == 'jhe':
        data_type_pre = 'jhe_'
    else:
        data_type_pre = ''
    u.write_results('Results/' + date + '/' + data_type_pre + 'global_' + type + '_' + trends_name + date + '.xlsx')

    return



