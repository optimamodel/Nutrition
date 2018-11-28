####
# tests the desired regions and program set

import nutrition.ui as nu
import sciris as sc

p = nu.Project('congo')

# individual program scale-up
# regions = ['bas_uele', 'equateur', 'haut_katanga',
#            'haut_lomami', 'haut_uele', 'ituri',
#            'kasai_central', 'kasai', 'kasai_oriental',
#            'kinshasa', 'kongo_central', 'kwango',
#            'kwilu', 'lomami', 'lualaba',
#            'mai_ndombe', 'maniema', 'mongala',
#            'nord_kivu', 'nord_ubangi', 'sankuru',
#            'sud_kivu', 'sub_ubangi', 'tanganyika',
#            'tshopo', 'tshuapa']

regions = ['kinshasa']

progset = ['Balanced energy-protein supplementation', 'Calcium supplementation',
           'Cash transfers', 'Family planning', 'IFA fortification of maize',
           'IFAS (school)', 'IFAS for pregnant women (health facility)',
           'IPTp', 'IYCF 1', 'IYCF 2', 'Mg for eclampsia', 'Mg for pre-eclampsia',
           'Micronutrient powders', 'Multiple micronutrient supplementation',
           'Oral rehydration salts', 'Treatment of SAM', 'Vitamin A supplementation',
           'WASH: Handwashing', 'Zinc for treatment + ORS']

for region in regions:
    p.load_data(country='congo', region=region, name=region)
    kwargs = []
    for prog in progset:
        kwarg = {'name': 'region: %s \n prog: %s'%(region, prog),
                  'model_name': region,
                  'scen_type': 'coverage',
                  'progvals': sc.odict({prog: [0.95]})}
        kwargs.append(kwarg)
    scens = nu.make_scens(kwargs)
    p.run_scens(scens)



