import nutrition.ui as nu
from functools import partial
p = nu.Project('PNG')
p.load_data(inputspath='PNG 2019 databook_' + 'Highlands' + ' 20190322.xlsx', name='PNG_Highlands')
p.load_data(inputspath='PNG 2019 databook_' + 'Islands' + ' 20190322.xlsx', name='PNG_Islands')
p.load_data(inputspath='PNG 2019 databook_' + 'Southern' + ' 20190322.xlsx', name='PNG_Southern')
kwargs = {'name': 'test1',
              'modelnames': ['PNG_Highlands', 'PNG_Islands', 'PNG_Southern'],# 'PNG_Momase'],
              'weights': 'child_deaths',
              'fix_curr': False,
              'fix_regionalspend': False,
              'add_funds': 5e6,
              'prog_set': ['IFA fortification of maize', 'IYCF 1', 'Lipid-based nutrition supplements',
                            'Multiple micronutrient supplementation', 'Micronutrient powders', 'Kangaroo mother care',
                            'Public provision of complementary foods', 'Treatment of SAM',  'Vitamin A supplementation',
                           'Mg for eclampsia', 'Zinc supplementation', 'Iron and iodine fortification of salt'][:3]}
self = nu.Geospatial(**kwargs)
base_allocs = [3965752.71613903, 3452324.20189087, 2908124.86513123]
money = 10000
changed_allocs12 = [base_allocs[0]-money, base_allocs[1]+money, base_allocs[2]]
changed_allocs13 = [base_allocs[0]-money, base_allocs[1], base_allocs[2]+money]
changed_allocs21 = [base_allocs[0]+money, base_allocs[1]-money, base_allocs[2]]
changed_allocs23 = [base_allocs[0], base_allocs[1]-money, base_allocs[2]+money]
changed_allocs31 = [base_allocs[0]+money, base_allocs[1], base_allocs[2]-money]
changed_allocs32 = [base_allocs[0], base_allocs[1]+money, base_allocs[2]-money]
list_allocs = [base_allocs, changed_allocs12, changed_allocs13, changed_allocs21, changed_allocs23, changed_allocs31, changed_allocs32]
cumulative_result = []

for i in list(range(7)):
    regional_allocs = list_allocs[i]
    regions = self.make_regions(add_funds=regional_allocs, rem_curr=not False, mults=[1])
    run_optim = partial(p.run_optim, key=-1, maxiter=4, swarmsize=4, maxtime=15,
                        parallel=False, dosave=True, runbaseline=False)
    # Run results in parallel or series.
    # can run in parallel b/c child processes in series
    results = [run_optim(region) for region in regions]

    # Flatten list.
    results = [item for sublist in results for item in sublist]

    # Remove multiple to plot by name (total hack)
    for res in results:
        res.mult = None
        res.name = res.name.replace('(x1)', '')

    cumulative_result.append([sum(results[0].model.child_deaths), sum(results[1].model.child_deaths), sum(results[2].model.child_deaths)])
    print(i)
diff12 = []
diff13 = []
diff21 = []
diff23 = []
diff31 = []
diff32 = []
for j in [0, 1, 2]:
    diff12.append(cumulative_result[1][j] - cumulative_result[0][j])
    diff13.append(cumulative_result[2][j] - cumulative_result[0][j])
    diff21.append(cumulative_result[3][j] - cumulative_result[0][j])
    diff23.append(cumulative_result[4][j] - cumulative_result[0][j])
    diff31.append(cumulative_result[5][j] - cumulative_result[0][j])
    diff32.append(cumulative_result[6][j] - cumulative_result[0][j])
print(sum(diff12), sum(diff13), sum(diff21), sum(diff23), sum(diff31), sum(diff32))

