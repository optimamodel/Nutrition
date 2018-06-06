'''
Test Nutrition using new framework.
'''

import nutrition.ui as nt


torun = [
'blank_project',
'make_model',
        ]

if 'blank_project' in torun:
    P = nt.Project()


if 'make_model' in torun:
    P = nt.Project(workbookfile=)


print('Done.')