import nutrition.ui as nu
import sciris as sc

# load in data to create model
p = nu.Project('eg')
p.load_data('demo', 'demo', name='eg')

### define custom scenarios
kwargs1 = {'name':'Treat SAM 100%',
           'model_name': 'eg',
           'scen_type': 'coverage',
            'progvals': sc.odict({'Treatment of SAM': [1]})}

kwargs2 = sc.dcp(kwargs1)
kwargs2.update({'name': 'IYCF 1 100%',
                'progvals': sc.odict({'IYCF 1': [1]})})

kwargs3 = {'name': 'IYCF at $10 mil',
         'model_name': 'eg',
         'scen_type': 'budget',
           'progvals': sc.odict({'IYCF 1': [1e7],
                                 'IPTp': [1e7]})}

scen_list = nu.make_scens([kwargs1, kwargs2, kwargs3])
p.add_scens(scen_list)
p.run_scens()
p.plot()
res = p.get_costeff()