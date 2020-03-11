import sys
sys.path.append('C:\\Users\\dominic.delport\\Documents\\GitHub\\Nutrition\\tests')
import datetime
import run_global_baseline as rgb

ToDo = [
    'standard',
    #'jhe'
]

fulldate = datetime.datetime.now()
date = fulldate.strftime('%x')[3:5] + fulldate.strftime('%x')[:2] + '20' + fulldate.strftime('%x')[6:8]

if 'standard' in ToDo:
    for scenario in ['baseline', 'scaleup']:
        for trends in [False, True]:
            rgb.run_baseline_scaleup(date, 'standard', scenario, trends)

if 'jhe' in ToDo:
    for scenario in ['baseline', 'scaleup']:
        for trends in [False, True]:
            rgb.run_baseline_scaleup(date, 'jhe', scenario, trends)

print('Done!')
