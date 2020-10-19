import sys
#sys.path.append('C:/Users/dominic.delport/Documents/GitHub/Nutrition/')  # I think this will be the correct path on the server
sys.path.append('C:/Users/debra.tenbrink/Documents/GitHub/Nutrition/')  # I think this will be the correct path on the server
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


input_path = 'databooks/'
output_path = 'outputs/'
num_procs = 4

region_list = ['AWARAN', 'BARKHAN', 'CHAGAI',
                 'DERA BUGTI', 'GWADAR', 'HARNAI', 'JAFFARABAD', 'JHAL MAGSI',
                 'KACHHI', 'KALAT', 'KECH', 'KHARAN', 'KHUZDAR', 'KILLA ABDULLAH', 'KILLA SAIFULLAH',
                 'KOHLU', 'LASBELA', 'LEHRI', 'LORALAI', 'MASTUNG', 'MUSAKHEL', 'NASIRABAD',
                 'NUSHKI', 'PANJGUR', 'PISHIN', 'QUETTA', 'SHERANI', 'SIBI', 'SOHBATPUR', 'WASHUK', 'ZHOB', 'ZIARAT']

#add_funds = [5e6, 10e6, 20e6] # Extra budget amounts
add_funds = [0, 5e6, 10e6, 20e6] # Extra budget amounts

if __name__ == '__main__':

    p = Project('Balochistan')
    for region in region_list:
        p.load_data(inputspath=input_path + region + '_input.xlsx', name=region, time_trend=False)
    for funds in add_funds:
        kwargs = {'name': 'Balochistan',
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
                  'fix_curr': False,
                  'add_funds': funds
                  }

        geo = Geospatial(**kwargs)
        #results = p.run_geo(geo=geo, maxiter=1, swarmsize=1, maxtime=2, dosave=True, parallel=False)
        results = p.run_geo(geo=geo, dosave=True, parallel=True)

        write_results(results, filename=output_path + 'Balochistan_geospatial' + "{:.0e}".format(funds) + '.xlsx')
