import nutrition.ui as nu
from nutrition.results import reduce_results, write_results
from nutrition.optimization import Optim
import sciris as sc
import sys

doplot = False

# load in data to create model
p = nu.Project("eg")
p.load_data("demo", "testing", name="eg")

### TEST MMS / IFAS dependency
kwargs1 = {"name": "MMS",
           "model_name": "eg",
           "scen_type": "coverage",
           "progvals": sc.odict({"Multiple micronutrient supplementation": [0.95]}),
           "growth": "fixed coverage",
           "enforce_constraints_year": 0}

kwargs2 = {"name": "IFAS",
           "model_name": "eg",
           "scen_type": "coverage",
           "progvals": sc.odict({"IFAS for pregnant women (community)": [0.95]}),
           "growth": "fixed coverage",
           "enforce_constraints_year": 0}

kwargs3 = {"name": "MMS+IFAS",
           "model_name": "eg",
           "scen_type": "coverage",
           "progvals": sc.odict({"Multiple micronutrient supplementation": [0.95],
                                 "IFAS for pregnant women (community)": [0.95]}),
           "growth": "fixed coverage"}

kwargs4 = {"name": "MMS+IFAS budget",
           "model_name": "eg",
           "scen_type": "budget",
           "progvals": sc.odict({"Multiple micronutrient supplementation": [8908763],
                                 "IFAS for pregnant women (community)": [1720475]}),
           "growth": "fixed coverage",
           "enforce_constraints_year": 2}

### TEST PPCF/LNS dependency

kwargs5 = {"name": "PPCF",
           "model_name": "eg",
           "scen_type": "coverage",
           "progvals": sc.odict({"Public provision of complementary foods": [0.95]}),
           "growth": "fixed coverage",
           "enforce_constraints_year": 0}

kwargs6 = {"name": "LNS",
           "model_name": "eg",
           "scen_type": "coverage",
           "progvals": sc.odict({"Lipid-based nutrition supplements": [0.95]}),
           "growth": "fixed coverage",
           "enforce_constraints_year": 0}

kwargs7 = {"name": "PPCF+LNS",
           "model_name": "eg",
           "scen_type": "coverage",
           "progvals": sc.odict({"Public provision of complementary foods": [0.95],
                                 "Lipid-based nutrition supplements": [0.95]}),
           "growth": "fixed coverage",
           "enforce_constraints_year": 1}

### TEST dependency in optimisation
kwargs8 = {"name": "MMS IFAS dep",
           "model_name": "eg",
           "mults": [1],
           "weights": sc.odict({"Minimize the prevalence of ID anaemia in pregnant women": [1]}),
           "prog_set": ["Multiple micronutrient supplementation", "IFAS for pregnant women (community)"],
           "fix_curr": False,
           "add_funds": 1e8} # lots of money

if __name__ == "__main__":

    scen_list = nu.make_scens([kwargs1, kwargs2, kwargs3, kwargs4])
    #scen_list = nu.make_scens([kwargs5, kwargs6, kwargs7])
    p.add_scens(scen_list)
    results = p.run_scens(n_samples=0)

    # optims = [Optim(**kwargs8)]
    # p.add_optims(optims)
    # results = p.run_optim(parallel=False)
    # p.write_results("optim_results.xlsx")

all_reduce = reduce_results(results)
write_results(results=results, reduced_results=all_reduce, filename="scen_results_test.xlsx")

