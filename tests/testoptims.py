import nutrition.ui as nu
from nutrition.optimization import Optim
import sciris as sc

if __name__ == '__main__':
    doplot = False
    dosave = True

    # load in data to create model
    p = nu.Project('eg')
    p.load_data('nigeria', 'national', name='eg')

    ## define custom optimization
    weight = 4
    kwargs1 = {'name':'test1',
               'model_name': 'eg',
               'mults': [1],
               'weights': sc.odict({'stunted_prev': 1, 'wasted_prev': 1, 'child_anaemprev': 1, 'pw_anaemprev': 1, 'nonpw_anaemprev': 1}),
               'prog_set': ['Calcium supplementation','Cash transfers','IFA fortification of maize','IFA fortification of rice',
                            'IFA fortification of wheat flour', 'IFAS (retailer)','IFAS (school)','IFAS for pregnant women (community)',
                             'IFAS for pregnant women (health facility)','IPTp','IYCF 1','IYCF 2',
                             'Long-lasting insecticide-treated bednets',
                             'Micronutrient powders','Multiple micronutrient supplementation',
                             'Treatment of SAM','Vitamin A supplementation',
                             'Zinc for treatment + ORS'],
               'fix_curr': True,
               'add_funds': 232e6,
               'relative_reduction': True,
               'outcome_reductions': sc.odict({'stunted_prev': sc.odict({'reduction': 20, 'year': 2025, 'weighting': weight}),
                                               'child_anaemprev': sc.odict({'reduction': 28.46, 'year': 2025, 'weighting': weight}),
                                               'pw_anaemprev': sc.odict({'reduction': 50, 'year': 2025, 'weighting': weight}),
                                               'nonpw_anaemprev': sc.odict({'reduction': 14.03, 'year': 2025, 'weighting': weight}),
                                               'wasted_prev': sc.odict({'reduction': 2.64, 'year': 2025, 'weighting': weight})})}

    kwargs2 = {'name': 'test2',
              'model_name': 'eg',
              'mults':[1,2],
               'weights': 'thrive',
              'prog_set':  ['IFAS (community)', 'IFAS (health facility)', 'IYCF 1', 'Lipid-based nutrition supplements',
               'Multiple micronutrient supplementation', 'Micronutrient powders',
               'Public provision of complementary foods', 'Treatment of SAM',
               'Vitamin A supplementation', 'Zinc supplementation', 'Calcium supplementation', 'Mg for eclampsia', 'Mg for pre-eclampsia'],
              'fix_curr': False}

    # custom objective
    kwargs3 = {'name': 'test3',
               'model_name': 'eg',
               'mults':[1,2],
               'weights': sc.odict({'thrive':                               1,
                                    'Minimize the number of child deaths':  7.6,
                                    'Child mortality rate':                 -1
                                    }),
               'prog_set':  ['IFAS (community)', 'IFAS (health facility)', 'IYCF 1', 'Lipid-based nutrition supplements',
                             'Multiple micronutrient supplementation', 'Micronutrient powders',
                             'Public provision of complementary foods', 'Treatment of SAM',
                             'Vitamin A supplementation', 'Zinc supplementation'],
               'fix_curr': False}

    optims = [Optim(**kwargs1)]
    p.add_optims(optims)
    p.run_optim(parallel=False)
    if doplot: p.plot(optim=True)
    if dosave: p.write_results('Nigeria_optim_progress_w_4_mixed.xlsx')

'''
['Balanced energy-protein supplementation', 'Calcium supplementation', 'Cash transfers',
     'Delayed cord clamping', 'IFA fortification of maize',
     'IFA fortification of rice', 'IFA fortification of wheat flour', 'IFAS (community)',
     'IFAS (health facility)', 'IFAS (retailer)', 'IFAS (school)',
     'IFAS for pregnant women (community)', 'IFAS for pregnant women (health facility)',
     'IPTp', 'Iron and iodine fortification of salt', 'IYCF 1', 'Kangaroo mother care',
     'Lipid-based nutrition supplements', 'Long-lasting insecticide-treated bednets',
     'Mg for eclampsia', 'Mg for pre-eclampsia', 'Micronutrient powders',
     'Multiple micronutrient supplementation', 'Oral rehydration salts',
     'Public provision of complementary foods', 'Treatment of SAM', 'Vitamin A supplementation',
     'Zinc for treatment + ORS', 'Zinc supplementation'],
 '''