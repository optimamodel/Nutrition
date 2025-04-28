import nutrition.ui as nu
from nutrition.results import reduce_results, write_results
from nutrition.optimization import Optim
import sciris as sc
import sys

doplot = False

# load in data to create model
p = nu.Project("eg")
#p.load_data("demo", name="eg") 
p.load_data(inputspath='C:\\Users\\tharindu.wickram\\Burnet Institute\\WG-Modelling-Nutrition - Documents\\Applications\\WB multi_country 2025\\Databooks\\AGO_databook.xlsx', name='AGO')

### TEST MMS / IFAS dependency
kwargs1 = {"name": "SQLNS",
           "model_name": "AGO",
           "scen_type": "coverage",
           "progvals": sc.odict({"Small quantity lipid-based nutrition supplements": [0.18,0.36,0.54,0.72,0.9,0.9,0.9,0.9,0.9,0.9],
                                 "Treatment of SAM": [0.136]}),
           "growth": "fixed coverage"}

kwargs2 = {"name": "SQLNS+TSAM",
           "model_name": "AGO",
           "scen_type": "coverage",
           "progvals": sc.odict({"Small quantity lipid-based nutrition supplements": [0.18,0.36,0.54,0.72,0.9,0.9,0.9,0.9,0.9,0.9],
                                 "Treatment of SAM": [0.19,0.37, 0.55,0.72,0.9,0.9,0.9,0.9,0.9]}),
           "growth": "fixed coverage"}

kwargs3 = {"name": "TSAM",
           "model_name": "AGO",
           "scen_type": "coverage",
           "progvals": sc.odict({"Small quantity lipid-based nutrition supplements": [0.0],
                                 "Treatment of SAM": [0.19,0.37, 0.55,0.72,0.9,0.9,0.9,0.9,0.9]}),
           "growth": "fixed coverage"}

kwargs4 = {"name": "TSAM+IYCF",
           "model_name": "AGO",
           "scen_type": "coverage",
           "progvals": sc.odict({"Small quantity lipid-based nutrition supplements": [0.18,0.36,0.54,0.72,0.9,0.9,0.9,0.9,0.9,0.9],
                                 "Treatment of SAM": [0.19,0.37, 0.55,0.72,0.9,0.9,0.9,0.9,0.9],
                                 "IYCF 1": [0.126,0.37, 0.55,0.72,0.9,0.9,0.9,0.9,0.9],
                                 "Vitamin A supplementation": [0.05,0.37, 0.55,0.72,0.9,0.9,0.9,0.9,0.9]}),
           "growth": "fixed coverage"}


if __name__ == "__main__":

    scen_list = nu.make_scens([kwargs1, kwargs2, kwargs3, kwargs4])
    #scen_list = nu.make_scens([kwargs1, kwargs2, kwargs3, kwargs3a])
    p.add_scens(scen_list)
    results = p.run_scens(n_samples=0)

    # optims = [Optim(**kwargs8)]
    # p.add_optims(optims)
    # results = p.run_optim(parallel=False)
    # p.write_results("optim_results.xlsx")

all_reduce = reduce_results(results)
write_results(results=results, reduced_results=all_reduce, filename="scen_results_AGO3.xlsx")

