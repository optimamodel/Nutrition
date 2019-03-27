import nutrition.ui as nu
from nutrition.optimization import Optim
from nutrition.geospatial import Geospatial
from copy import deepcopy as dc
import sciris as sc

# load in data to create model
p = nu.Project('PNG')
region = ['National','Highlands', 'Islands', 'Momase', 'Southern']
invest = [1e6,2e6,3e6,4e6,5e6]
saturate = 0.95
interventions = ['Balanced energy-protein supplementation','Calcium supplementation','Cash transfers','Delayed cord clamping',
                     'Family planning','IFA fortification of maize','IFA fortification of rice','IFA fortification of wheat flour',
                     'IFAS (community)','IFAS (health facility)','IFAS (retailer)','IFAS (school)','IFAS for pregnant women (community)',
                     'IFAS for pregnant women (health facility)','IPTp','Iron and iodine fortification of salt','IYCF 1','IYCF 2','IYCF 3',
                     'Kangaroo mother care','Lipid-based nutrition supplements','Long-lasting insecticide-treated bednets','Mg for eclampsia',
                     'Mg for pre-eclampsia','Micronutrient powders','Multiple micronutrient supplementation','Oral rehydration salts',
                     'Public provision of complementary foods','Treatment of SAM','Vitamin A supplementation','WASH: Handwashing',
                     'WASH: Hygenic disposal','WASH: Improved sanitation','WASH: Improved water source','WASH: Piped water',
                     'Zinc for treatment + ORS','Zinc supplementation']

for r in range (0,len(region)):
    p.load_data(inputspath='PNG 2019 databook_' + region[r] + ' 20190322.xlsx',name=region[r])

    # get baseline data
    p.run_scens()
    progbudget_base = p.results['scens'][0].get_allocs()

    # run investment scenarios for each intervention and investment amount
    for i in range (0,len(invest)):
        kwargs = [None]*len(interventions)
        for x in range(0,len(interventions)):
            kwargs[x] = {'name': interventions[x],
                     'model_name': region[r],
                     'scen_type': 'budget',
                     'progvals': sc.odict({interventions[x]: [invest[i]+progbudget_base[interventions[x]][0]]})}

        scen_list = nu.make_scens(kwargs)
        p.add_scens(scen_list)
        p.run_scens()
        p.write_results(region[r]+'_interventions'+str(i+1)+'.xlsx', key=0)

    # run a saturated coverage scenario for each intervention
    kwargs_cov = [None] * len(interventions)
    for x in range(0, len(interventions)):
        kwargs_cov[x] = {'name': interventions[x],
                     'model_name': region[r],
                     'scen_type': 'coverage',
                     'progvals': sc.odict({interventions[x]: [saturate]})}
    scen_list = nu.make_scens(kwargs_cov)
    p.add_scens(scen_list)
    p.run_scens()
    p.write_results(region[r]+'_interventions_sat.xlsx', key=0)

    # set of interventions to use in optimisation
    interventions_opt = ['Balanced energy-protein supplementation','Calcium supplementation','Cash transfers','Delayed cord clamping',
                     'IFA fortification of maize','IFA fortification of rice','IFA fortification of wheat flour',
                     'IFAS (community)','IFAS for pregnant women (community)','IPTp','Iron and iodine fortification of salt','IYCF 1',
                     'Kangaroo mother care','Lipid-based nutrition supplements','Long-lasting insecticide-treated bednets','Mg for eclampsia',
                     'Mg for pre-eclampsia','Micronutrient powders','Multiple micronutrient supplementation','Oral rehydration salts',
                     'Public provision of complementary foods','Treatment of SAM','Vitamin A supplementation',
                     'Zinc for treatment + ORS','Zinc supplementation']

    '''
    #Don't use this for now. Was trying to do multiple additional funds at once
    budget0 = 0.
    for i in range(0, len(interventions_opt)):
        budget0 += progbudget_base[interventions_opt[i]][0]
    
    mults = [1] * (len(invest) + 1)
    for i in range(0, len(invest)):
        mults[i+1] = (budget0+invest[i])/(budget0)
    
    optim_kwargs = {'name': 'optim',
               'model_name': 'PNG',
               'mults':mults,
               'weights': sc.odict({'thrive': 1}),
               'prog_set':  interventions_opt,
               'fix_curr': True,
               'add_funds':[0]}
    '''

    optim_budget= [None]*len(invest)
    for i in range(0, len(invest)):
        optim_kwargs = {'name': 'optim',
                   'model_name': region[r],
                   'mults':[1],
                   'weights': sc.odict({'thrive': 1}),
                   'prog_set': interventions_opt,
                   'fix_curr': True,
                   'add_funds': invest[i]}

        optims = [Optim(**optim_kwargs)]
        p.add_optims(optims)
        p.run_optim(parallel=False)
        optim_budget[i] = p.results['optim'][-1].get_allocs()

    optim_kwargs = [None]*len(invest)
    for x in range(0, len(invest)):
        optim_kwargs[x] = {'name': 'optim'+str(x),
                     'model_name': region[r],
                     'scen_type': 'budget',
                     'progvals': optim_budget[x]}

    scen_list = nu.make_scens(optim_kwargs)
    p.add_scens(scen_list)
    p.run_scens()
    p.write_results(region[r]+'_interventions_optim.xlsx', key=0)

#p.write_results('PNG_interventions_optim.xlsx')



# Geospatial
p.load_data(inputspath='PNG 2019 databook_Highlands 20190322.xlsx',name='PNG_Highlands')
p.load_data(inputspath='PNG 2019 databook_Islands 20190322.xlsx',name='PNG_Islands')
p.load_data(inputspath='PNG 2019 databook_Momase 20190322.xlsx',name='PNG_Momase')
p.load_data(inputspath='PNG 2019 databook_Southern 20190322.xlsx',name='PNG_Southern')


for i in range(0, len(invest)):
    kwargs = {'name': 'PNG_geo',
              'modelnames': ['PNG_Highlands', 'PNG_Islands', 'PNG_Momase','PNG_Southern'],
              'weights': 'thrive',
              'fix_curr': True,
              'fix_regionalspend': True,
              'add_funds': invest[i],
              'prog_set': interventions_opt}

    geo = Geospatial(**kwargs)
    results = p.run_geo(geo=geo, maxiter=25, swarmsize=40, maxtime=200, parallel=True)
    p.write_results('PNG_geo_optim'+str(i+1)+'.xlsx')
    #p.plot(geo=True)
