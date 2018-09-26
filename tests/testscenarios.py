import nutrition.ui as nu
import sciris as sc

doplot = False

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

scen_list = nu.make_scens([kwargs4, kwargs5])
p.add_scens(scen_list)
p.run_scens()
if doplot:
    p.plot()
costeff = p.get_costeff()
