import sys
sys.path.append('/home/dom/Optima/tests')
import datetime
import Total_CE_v2_parallel as gce
import global_for_bounds as gb
import By_country_CE_parallel_v2 as cce
import by_country_for_bounds as cb
import warnings
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)

ToDo = [
    'global CE',
    #'global bounds',
    'country CE',
    #'country bounds'
]

bounds = ['UBE', 'LBE', 'UBC', 'LBC']

fulldate = datetime.datetime.now()
date = fulldate.strftime('%x')[3:5] + fulldate.strftime('%x')[:2] + '20' + fulldate.strftime('%x')[6:8]
if __name__ == '__main__':
    if 'global CE' in ToDo:
        global_prog_order = gce.run_total_ce(date=date)

    if 'global bounds' in ToDo and 'global CE' in ToDo:
        for bound in bounds:
            gb.run_global_bounds(date, bound, global_prog_order)

    elif 'global bounds' in ToDo and 'global CE' not in ToDo:
        print('Cannot calculate bounds without first running global level cost effectiveness!')

    if 'country CE' in ToDo:
        country_prog_order = cce.run_country_ce(date)

    if 'country bounds' in ToDo and 'country CE' in ToDo:
        for bound in bounds:
            cb.run_country_bounds(date, bound, country_prog_order)

    elif 'country bounds' in ToDo and 'country CE' not in ToDo:
        print('Cannot calculate bounds without first running country level cost effectiveness!')

    print('Done!')
