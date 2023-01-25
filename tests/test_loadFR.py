import nutrition.ui as nu
from nutrition.optimization import Optim
from nutrition.geospatial import Geospatial
from nutrition.results import reduce_results, write_results
from nutrition.utils import get_translator
from copy import deepcopy as dc
import sciris as sc

# from at_tools import gdrive_folder

# load in data to create model
p = nu.Project("CHD")


optimization_interventions = ['Balanced energy-protein supplementation', 'Delayed cord clamping',
                              'IFAS for pregnant women (health facility)', 'IPTp', 'IYCF 1', 'Kangaroo mother care',
                              'Lipid-based nutrition supplements', 'Long-lasting insecticide-treated bednets',
                              'Mg for pre-eclampsia', 'Micronutrient powders',
                              'Public provision of complementary foods',
                              'Treatment of SAM', 'Vitamin A supplementation']

ref_progs = ['IPTp', 'Long-lasting insecticide-treated bednets']

if __name__ == '__main__':
    all_results = []

    """Baseline budget extraction"""


    p.load_data(inputspath='C:\\Users\\nick.scott\\Downloads\\FR_test.xlsx', name='test')