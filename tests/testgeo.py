import nutrition.ui as nu
from nutrition.geospatial import Geospatial
import sciris as sc

# load in data to create model
p = nu.Project("Demo")
# three identical regions (same spreadsheet)
p.load_data("demo", "region1", name="Demo1", resampling=False)
p.load_data("demo", "region2", name="Demo2", resampling=False)
# p.load_data('demo', 'region3', name='Demo3', resampling=False)


kwargs = {
    "name": "test1",
    "modelnames": ["Demo1", "Demo2"],
    "weights": sc.odict(
        {
            "Minimize the number of child deaths": [1.0],
            "thrive": [1.0],
        }
    ),
    "fix_curr": False,
    "fix_regionalspend": False,
    "add_funds": 0,
    "prog_set": ["IFA fortification of maize", "IYCF 1", "Lipid-based nutrition supplements", "Multiple micronutrient supplementation", "Micronutrient powders", "Kangaroo mother care", "Public provision of complementary foods", "Treatment of SAM", "Vitamin A supplementation", "Mg for eclampsia", "Zinc supplementation", "Iron and iodine fortification of salt"],
    "growth": "fixed coverage",
}
if __name__ == "__main__":
    geo = Geospatial(**kwargs)
    results = p.run_geo(geo=geo, maxiter=2, swarmsize=0, maxtime=2, parallel=True, runbalanced=True, n_runs=2)
    p.reduce_results()
    p.plot(toplot=["clust_annu_alloc"], geo=True)
    p.write_results("geo_results.xlsx")
    p.save("geo_test")
