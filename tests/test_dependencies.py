import nutrition.ui as nu
from nutrition.results import reduce_results, write_results
import sciris as sc
import sys

doplot = False

# load in data to create model
p = nu.Project("eg")
p.load_data("demo", "testing", name="eg")

### define custom scenarios
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
           "enforce_constraints_year": 0}

if __name__ == "__main__":

    scen_list = nu.make_scens([kwargs1, kwargs2, kwargs3, kwargs4])
    p.add_scens(scen_list)

    results = p.run_scens(n_samples=1)

if doplot:
    p.plot()

all_reduce = reduce_results(results)
write_results(results=results, reduced_results=all_reduce, filename="scen_results_test.xlsx")

