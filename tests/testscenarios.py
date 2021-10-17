import nutrition.ui as nu
import sciris as sc
import sys

x=1500
sys.setrecursionlimit(x)

#pd.set_option('mode.chained_assignment', None)

doplot = True
resampling = False
ramping = True
n_runs = 3
sample_size = n_runs

# load in data to create model
"""" If the model is run for a single run using 'p.run_scens()' then set resampling=False
    to make sure that the default point estimators are used from 
    the databook with out considering any randomness!"""
p = nu.Project('eg')
p.load_data('demo', 'testing', name='eg', resampling=resampling)

### define custom scenarios
kwargs1 = {'name':'Treat SAM 100%',
           'model_name': 'eg',
           'scen_type': 'coverage',
            'progvals': sc.odict({'Treatment of SAM': [0.9, 0.5, 0.8]})}

kwargs2 = sc.dcp(kwargs1)
kwargs2.update({'name': 'IYCF 1 100%',
                'progvals': sc.odict({'IYCF 1': [1]})})

kwargs3 = {'name': 'IYCF at $10 mil',
         'model_name': 'eg',
         'scen_type': 'budget',
           'progvals': sc.odict({'IYCF 1': [1e7, 2e7, 1.5e6, 2.5e7],
                                 'IPTp': [2e7, 2.8e7, 2.8e6, 4.25e7]})}

### testing FE bugs
kwargs4 = {'name': 'FE check 1',
           'model_name': 'eg',
           'scen_type': 'budget',
           'progvals': sc.odict({u'IFA fortification of maize': [2000000],
                                    u'IPTp': [2000000],
                                     u'Iron and iodine fortification of salt':[],
                                     u'IYCF 1':[],
                                     u'Long-lasting insecticide-treated bednets':[],
                                     u'Micronutrient powders':[],
                                     u'Multiple micronutrient supplementation': [],
                                     u'Vitamin A supplementation': [],
                                     u'Zinc for treatment + ORS': []})}

kwargs5 = {'name': 'FE check 2',
           'model_name': 'eg',
           'scen_type': 'budget',
           'progvals': sc.odict({u'IFA fortification of maize': [2000000],
                                    u'IPTp': [2000000],
                                     u'Iron and iodine fortification of salt':[],
                                     u'IYCF 1':[],
                                     u'Long-lasting insecticide-treated bednets':[0],
                                     u'Micronutrient powders':[],
                                     u'Multiple micronutrient supplementation': [],
                                     u'Vitamin A supplementation': [],
                                     u'Zinc for treatment + ORS': []})}

kwargs5 = {'name': 'Check WASH',
           'model_name': 'eg',
           'scen_type': 'budget',
           'progvals': sc.odict({'WASH: Handwashing': [1e6]})}

kwargs6 = {'name': 'Check bednets',
           'model_name': 'eg',
           'scen_type': 'budget',
           'progvals': sc.odict({'Long-lasting insecticide-treated bednets': [0]})}

kwargs7 = {'name': 'IYCF',
           'model_name': 'eg',
           'scen_type': 'coverage',
           'progvals': sc.odict({'IYCF 1': [0.6, 0.2, 0.5, 0.95, 0.8]})}

kwargs8 = {'name': 'Treat SAM 100%',
               'model_name': 'Maximize thrive',
               'mults': [1],
               'weights': sc.odict({'thrive': 1}),
               'prog_set': ['Vitamin A supplementation', 'IYCF 1', 'IFA fortification of maize',
                            'Balanced energy-protein supplementation',
                            'Public provision of complementary foods',
                            'Iron and iodine fortification of salt'],
               'fix_curr': False,
               'add_funds': 0,
               'filter_progs': True}

if __name__ == '__main__':
    scen_list = nu.make_scens([kwargs1, kwargs7, kwargs3])
    p.add_scens(scen_list)

    #p.run_scens() # make sure to set resampling=False
    p.multirun_scens(n_runs=n_runs, ramping=ramping)
    p.reduce()
    #p.mean()
#p.run_scens()
if doplot:
    p.plot()
#costeff = p.get_costeff()
p.write_results('scen_results_test.xlsx')