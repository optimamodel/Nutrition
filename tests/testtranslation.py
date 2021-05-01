import nutrition.ui as nu
from nutrition.optimization import Optim
import sciris as sc


# load in data to create model

doplot = False
dosave = True

# load in data to create model
p = nu.Project('eg')
p.load_data(inputspath='demo_input_en_fr.xlsx', name='eg')


## define custom optimization
kwargs1 = {'name':'Treat SAM 100%',
           'model_name': 'eg',
           'scen_type': 'coverage',
            'progvals': sc.odict({'Treatment of SAM': [1]})}

kwargs2 = {'name':'test2',
          'model_name': 'eg',
          'mults':[1, 2],
           'weights': 'thrive',
          'prog_set':  ['IFAS (community)', 'IFAS (health facility)', 'IYCF 1', 'Lipid-based nutrition supplements',
           'Multiple micronutrient supplementation', 'Micronutrient powders',
           'Public provision of complementary foods', 'Treatment of SAM',
           'Vitamin A supplementation', 'Zinc supplementation', 'Calcium supplementation', 'Mg for eclampsia', 'Mg for pre-eclampsia'],
          'fix_curr': False}

# custom objective
scen_list = nu.make_scens([kwargs1])
p.add_scens(scen_list)
p.run_scens()
optims = [Optim(**kwargs2)]
p.add_optims(optims)
p.run_optim(parallel=False)
if doplot: p.plot(optim=True)
if dosave:
    p.write_results('translation_scen.xlsx', key=0)
    p.write_results('translation_optim.xlsx')
