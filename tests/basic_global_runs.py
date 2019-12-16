import nutrition.ui as nu
from nutrition.project import Project
import sciris as sc


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
cov = 0.95

prog_list = ['Balanced energy-protein supplementation', 'Calcium supplementation',
             'Delayed cord clamping', 'IFA fortification of maize',
             'IFA fortification of rice', 'IFA fortification of wheat flour',
             'IFAS for pregnant women (community)',
             'Iron and iodine fortification of salt', 'IYCF 1', 'Kangaroo mother care',
             'Lipid-based nutrition supplements',
             'Micronutrient powders',
             'Multiple micronutrient supplementation',
             'Public provision of complementary foods', 'Treatment of SAM', 'Vitamin A supplementation',
             'Zinc for treatment + ORS', 'Zinc supplementation']

trend = False
type = 'baseline'
trend = True
type = 'scaled up'

p = Project('Global_' + type)
for c, country in enumerate(country_list):
    # load country
    p.load_data(country='costed_baseline_' + country, name=country + " " + type, time_trend=trend)
    progval = sc.odict()
    if type == 'scaled up':
        for prog in prog_list:
            progval[prog] = interp_cov(p, prog, [2018, 2024], cov)  # scale up coverages to full by 2024
    kwargs = {'name': country,
              'model_name': country + " " + type,
              'scen_type': 'coverage',
              'progvals': progval}
    scen_list = nu.make_scens([kwargs])
    p.add_scens(scen_list)
p.run_scens()
if trend:
    p.write_results('Global_' + type + '_nutr_spec_trends29102019.xlsx')
else:
    p.write_results('Global_' + type + '_nutr_spec29102019.xlsx')

