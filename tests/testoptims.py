import nutrition.ui as nu
from nutrition.optimization import Optim
import sciris as sc
"""
Description of new inputs:

'relative_reduction' : Boolean, True if relative reduction objective function is desired, False if standard function is desired
'outcome_reductions' : Odict of odicts for each objective, with categories: 'target_reduction', 'year', 'index_weighting', 'max_reduction'
'target_reduction' : (Optional) Policy based targets for relative reduction in an outcome, used to weight each objective relative to each other
'year': (Optional) Year by which target should be measured, default is final year
'index weighting': (Optional) Index used in the objective function, can be used to vary weights on objectives but mainly impacts the 
weighting of progress vs. equality in optimization, default is w = 1
'max reduction' : Maximum relative reduction for each target based upon a single target optimization, should be evaluated first
"""

if __name__ == '__main__':
    doplot = False
    dosave = True

    # load in data to create model
    p = nu.Project('eg')
    p.load_data('nigeria', 'national', name='eg')
    outcome_weight = sc.odict()
    weight = 1
    ## define custom optimization
    ''' Loop to determine maximum reduction in each target:
    
    for outcome in ['stunted_prev', 'wasted_prev', 'child_anaemprev', 'pw_anaemprev', 'nonpw_anaemprev']:
        kwargs1 = {'name': outcome,
                   'model_name': 'eg',
                   'mults': [1],
                   'weights': sc.odict({outcome: 1}),
                   'prog_set': ['Calcium supplementation','Cash transfers','IFA fortification of maize','IFA fortification of rice',
                                'IFA fortification of wheat flour', 'IFAS (retailer)','IFAS (school)','IFAS for pregnant women (community)',
                                 'IFAS for pregnant women (health facility)','IPTp','IYCF 1','IYCF 2',
                                 'Long-lasting insecticide-treated bednets',
                                 'Micronutrient powders','Multiple micronutrient supplementation',
                                 'Treatment of SAM','Vitamin A supplementation', 'Zinc for treatment + ORS'],
                   'fix_curr': True,
                   'add_funds': 232e6,
                   'relative_reduction': False,
                   'outcome_reductions': sc.odict()}

        optims = [Optim(**kwargs1)]
        p.add_optims(optims)
        p.run_optim(maxiter=10, swarmsize=15, maxtime=100, parallel=False)
        if outcome == 'stunted_prev':
            outcome_weighting.append(outcome, 100 * (1 - p.results[outcome][1].model.stunted_prev[-1] / p.results[outcome][1].model.stunted_prev[0]))
        elif outcome == 'wasted_prev':
            outcome_weighting.append(outcome, 100 * (1 - p.results[outcome][1].model.wasted_prev[-1] / p.results[outcome][1].model.wasted_prev[0]))
        elif outcome == 'child_anaemprev':
            outcome_weighting.append(outcome, 100 * (1 - p.results[outcome][1].model.child_anaemprev[-1] / p.results[outcome][1].model.child_anaemprev[0]))
        elif outcome == 'pw_anaemprev':
            outcome_weighting.append(outcome, 100 * (1 - p.results[outcome][1].model.pw_anaemprev[-1] / p.results[outcome][1].pw_anaemprev[0]))
        elif outcome == 'nonpw_anaemprev':
            outcome_weighting.append(outcome, 100 * (1 - p.results[outcome][1].model.nonpw_anaemprev[-1] / p.results[outcome][1].nonpw_anaemprev[0]))
    '''

    # maximum achievable reductions
    outcome_weight = {'stunted_prev': 29.55, 'wasted_prev': 2.46, 'child_anaemprev': 28.46, 'pw_anaemprev': 72.24, 'nonpw_anaemprev': 14.03}
    kwargs_final = {'name': 'test1',
               'model_name': 'eg',
               'mults': [1],
               'weights': sc.odict({'stunted_prev': 1, 'wasted_prev': 1, 'child_anaemprev': 1, 'pw_anaemprev': 1,
                                    'nonpw_anaemprev': 1}),
               'prog_set': ['Calcium supplementation', 'Cash transfers', 'IFA fortification of maize',
                            'IFA fortification of rice',
                            'IFA fortification of wheat flour', 'IFAS (retailer)', 'IFAS (school)',
                            'IFAS for pregnant women (community)',
                            'IFAS for pregnant women (health facility)', 'IPTp', 'IYCF 1', 'IYCF 2',
                            'Long-lasting insecticide-treated bednets',
                            'Micronutrient powders', 'Multiple micronutrient supplementation',
                            'Treatment of SAM', 'Vitamin A supplementation',
                            'Zinc for treatment + ORS'],
               'fix_curr': True,
               'add_funds': 232e6,
               'relative_reduction': True,
               'outcome_reductions': sc.odict(
                   {'stunted_prev': sc.odict({'target_reduction': 20, 'year': 2025, 'index_weighting': weight, 'max_reduction': outcome_weight['stunted_prev']}),
                    'child_anaemprev': sc.odict({'target_reduction': 50, 'year': 2025, 'index_weighting': weight, 'max_reduction': outcome_weight['child_anaemprev']}),
                    'pw_anaemprev': sc.odict({'target_reduction': 50, 'year': 2025, 'index_weighting': weight, 'max_reduction': outcome_weight['pw_anaemprev']}),
                    'nonpw_anaemprev': sc.odict({'target_reduction': 50, 'year': 2025, 'index_weighting': weight, 'max_reduction': outcome_weight['nonpw_anaemprev']}),
                    'wasted_prev': sc.odict({'target_reduction': 10, 'year': 2025, 'index_weighting': weight, 'max_reduction': outcome_weight['wasted_prev']})})}

    optims = [Optim(**kwargs_final)]
    p.add_optims(optims)
    p.run_optim(parallel=False)
    if doplot: p.plot(optim=True)
    if dosave: p.write_results('Nigeria_optim_weighted.xlsx')

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