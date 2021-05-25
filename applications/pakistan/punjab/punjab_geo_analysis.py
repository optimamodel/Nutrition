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


input_path = 'Databooks/'
output_path = 'Outputs/'


region_list = ['ATTOCK', 'BAHAWALNAGAR', 'BAHAWALPUR', 'BHAKKAR', 'CHAKWAL', 'CHINIOT', 'DERA GHAZI KHAN',
               'FAISALABAD', 'GUJRANWALA', 'GUJRAT',
               'HAFIZABAD', 'JHANG', 'JHELUM', 'KASUR', 'KHANEWAL', 'KHUSHAB', 'LAHORE', 'LAYYAH',
               'LODHRAN', 'MANDI BAHAUDDIN', 'MIANWALI', 'MULTAN', 'MUZAFFARGARH', 'NAROWAL', 'NANKANA SAHIB', 'OKARA',
               'PAKPATTAN', 'RAHIMYAR KHAN', 'RAJANPUR', 'RAWALPINDI', 'SAHIWAL', 'SARGODHA', 'SHEIKHUPURA', 'SIALKOT',
               'TOBA TEK SINGH', 'VEHARI']

add_funds = [1e6, 2e6, 5e6] # Extra budget amounts

if __name__ == '__main__':

    p = Project('Punjab')
    for region in region_list:
        p.load_data(inputspath=input_path + region + '_input.xlsx', name=region)
    for funds in add_funds:
        kwargs = {'name': 'Punjab',
                  'modelnames': region_list,
                  'weights': sc.odict({'Minimize the number of child deaths': 1.0,
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
                  'fix_regionalspend': True,
                  'add_funds': funds
                  }

        geo = Geospatial(**kwargs)
        #results = p.run_geo(geo=geo, maxiter=500, swarmsize=35, maxtime=560, dosave=True, parallel=True)
        results = p.run_geo(geo=geo, dosave=True, parallel=True)

        write_results(results, filename=output_path + 'Punjab_geospatial_20201220' + "{:.0e}".format(funds) + '.xlsx')


    p2 = Project('Punjab')
    for region in region_list:
        p2.load_data(inputspath=input_path + region + '_input.xlsx', name=region)
    kwargs = {'name': 'Punjab',
              'modelnames': region_list,
              'weights': sc.odict({'Minimize the number of child deaths': 1.0,
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
              'fix_regionalspend': True,
              'add_funds': 0
              }

    geo2 = Geospatial(**kwargs)
    #results2 = p2.run_geo(geo=geo2, maxiter=500, swarmsize=35, maxtime=560, dosave=True, parallel=True)
    results2 = p2.run_geo(geo=geo2, dosave=True, parallel=True)
    write_results(results2, filename=output_path + 'Punjab_district_opt_20201220.xlsx')
