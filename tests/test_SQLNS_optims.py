import nutrition.ui as nu
from nutrition.results import reduce_results, write_results
from nutrition.optimization import Optim
import sciris as sc
import sys


# load in data to create model

doplot = False
dosave = True
if __name__ == '__main__':
    p = nu.Project("eg")
    p.load_data(inputspath='C:\\Users\\tharindu.wickram\\Burnet Institute\\WG-Modelling-Nutrition - Documents\\Applications\\WB multi_country 2025\\Databooks\\AGO_databook.xlsx', name='AGO')
    
    kwargs1 = {"name": "test1", "model_name": "AGO", "mults": [1], "weights": sc.odict({"Minimize the number of wasted children": [1]}), "prog_set": ["Small quantity lipid-based nutrition supplements", "Treatment of SAM"], "fix_curr": False, "add_funds": 1e7}
    
    
    
    optims = [Optim(**kwargs1)]
    p.add_optims(optims)
    p.run_optim(parallel=False)
    if doplot:
        p.plot(optim=True)
    if dosave:
        p.write_results("SQLNS_AGO_optim_tests.xlsx")

    
