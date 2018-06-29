"""
Version:
"""

import numpy as np
import nutrition.ui as nu
import sciris.core as sc

origfilename = nu.ONpath('tests')+'nutrition_2018-06-29_a.rslt'
newfilename  = nu.ONpath('tests')+'nutrition_2018-06-29.rslt'
docompare    = True
dosave       = True

P = nu.demo()
P.run_scens()
newR = P.result()[0].get_outputs(seq=True, asdict=True)

matches = 0
mismatches = 0
if docompare:
    origR = sc.loadobj(origfilename)
    keys = newR.keys()
    if origR.keys() != keys:
        print("WARNING, keys don't match!")
        
    for key in keys:
        comparison = newR[key] == origR[key]
        if sc.isiterable(comparison):
            comparison = np.array(comparison).all()
        if comparison:
            print('Match for %s' % key)
            matches += 1
        else:
            print('DOES NOT MATCH for %s' % key)
            mismatches += 1

if dosave:
    sc.saveobj(newfilename, newR)

print('Done; there were %s matches and %s mismatches.' % (matches, mismatches))