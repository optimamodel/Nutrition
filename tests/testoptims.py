import nutrition.ui as nu
from nutrition.optimization import Optim
import sciris as sc


# load in data to create model

doplot = False
dosave = True

# load in data to create model
p = nu.Project("eg")
p.load_data("demo", "national", name="eg")


## define custom optimization
kwargs1 = {"name": "test1", "model_name": "eg", "mults": [1, 2], "weights": sc.odict({"thrive": 1}), "prog_set": ["Vitamin A supplementation", "IYCF 1"], "fix_curr": False, "add_funds": 1e7}

kwargs2 = {"name": "test2", "model_name": "eg", "mults": [1, 2], "weights": "thrive", "prog_set": ["IFAS (community)", "IFAS (health facility)", "IYCF 1", "Lipid-based nutrition supplements", "Multiple micronutrient supplementation", "Micronutrient powders", "Public provision of complementary foods", "Treatment of SAM", "Vitamin A supplementation", "Zinc supplementation", "Calcium supplementation", "Mg for eclampsia", "Mg for pre-eclampsia"], "fix_curr": False}

# custom objective
kwargs3 = {"name": "test3", "model_name": "eg", "mults": [1, 2], "weights": sc.odict({"thrive": 1, "Minimize the number of child deaths": 7.6, "Child mortality rate": -1}), "prog_set": ["IFAS (community)", "IFAS (health facility)", "IYCF 1", "Lipid-based nutrition supplements", "Multiple micronutrient supplementation", "Micronutrient powders", "Public provision of complementary foods", "Treatment of SAM", "Vitamin A supplementation", "Zinc supplementation"], "fix_curr": False}

optims = [Optim(**kwargs2)]
p.add_optims(optims)
p.run_optim(parallel=False)
if doplot:
    p.plot(optim=True)
if dosave:
    p.write_results("optim_results.xlsx")
