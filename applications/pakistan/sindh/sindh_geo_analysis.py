import sys
sys.path.append('/home/debra/Nutrition/')  # I think this will be the correct path on the server
from nutrition.project import Project
from nutrition.optimization import Optim
from nutrition.scenarios import Scen
from nutrition.results import write_results
from nutrition.utils import run_parallel
from functools import partial
from nutrition import utils
from nutrition.scenarios import Scen
from nutrition.geospatial import Geospatial
import sciris as sc


input_path = 'Databooks/'
output_path = 'Outputs/'

region_list = ['SUJAWAL', 'THATTA', 'JACOBABAD',
                 'KASHMOR', 'SHIKARPUR', 'LARKANA', 'KAMBAR SHAHDAD KOT', 'SUKKUR',
                 'GHOTKI', 'KHAIRPUR', 'NAUSHAHRO FEROZE', 'SHAHEED BENAZIRABAD', 'DADU', 'JAMSHORO', 'HYDERABAD',
                 'TANDO ALLAHYAR','TANDO MUHAMMAD KHAN', 'MATIARI', 'BADIN', 'SANGHAR', 'MIRPUR KHAS', 'UMER KOT',
                 'THARPARKAR', 'KARACHI WEST', 'MALIR', 'KARACHI SOUTH', 'KARACHI EAST', 'KARACHI CENTRAL', 'KORANGI']

add_funds = [5e6, 10e6, 20e6] # Extra budget amounts

if __name__ == '__main__':

    p = Project('Sindh')
    for region in region_list:
        p.load_data(inputspath=input_path + region + '_input.xlsx', name=region, time_trend=False)
    for funds in add_funds:
        kwargs = {'name': 'Sindh',
                  'modelnames': region_list,
                  'weights': sc.odict({'Minimize the number of child deaths': 1.0/11.0,
                                       #'Minimize the prevalence of wasting in children': pop_size_tot,
                                       #'Minimize the prevalence of stunting in children': pop_size_tot}),
                                       #'thrive': 1,
                                       'Minimize the total number of wasted children under 5': 1,
                                       'Minimize the total number of stunted children under 5': 1}),
                  # The available programs need to be put below, I just filled it with common ones
                  'prog_set': ['Balanced energy-protein supplementation', 'Cash transfers',
                               'IFA fortification of wheat flour',
                               'IYCF 1', 'IYCF 2', 'IYCF 3', 'IFAS for pregnant women (community)',
                               'IFAS for pregnant women (health facility)', 'Lipid-based nutrition supplements',
                               'Management of MAM',
                               'Multiple micronutrient supplementation', 'Micronutrient powders', 'Kangaroo mother care',
                               'Treatment of SAM', 'Vitamin A supplementation',
                               'Zinc for treatment + ORS', 'Iron and iodine fortification of salt'],
                  'fix_curr': True,
                  'add_funds': funds
                  }

        geo = Geospatial(**kwargs)
        #results = p.run_geo(geo=geo, maxiter=10, swarmsize=10, maxtime=20, dosave=True, parallel=False)
        results = p.run_geo(geo=geo, dosave=True, parallel=True, num_procs=8)
        write_results(results, filename=output_path + 'Sindh_geospatial_test' + "{:.0e}".format(funds) + '.xlsx')
