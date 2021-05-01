"""
Version:
"""

import numpy as np
import nutrition.ui as nu
import sciris as sc

origfilename = nu.ONpath/'tests'/'nutrition_2018-08-01.rslt'
newfilename  = nu.ONpath/'tests'/'nutrition_2018-08-02.rslt'
docompare    = True
dosave       = True

P = nu.demo()
P.run_scens()
newR = P.result().get_outputs(seq=True, asdict=True)

matches = 0
mismatches = 0
if docompare:
    origR = sc.loadobj(origfilename)
    keys = newR.keys()
    if origR.keys() != keys:
        print("WARNING, keys don't match!")
        
    for key in keys:
        try:
            comparison = sc.approx(newR[key], origR[key])
        except:
            comparison = newR[key] == origR[key]
        if sc.isiterable(comparison):
            comparison = np.array(comparison).all()
        if comparison:
            print('Match for %s' % key)
            matches += 1
        else:
            print('DOES NOT MATCH for %s:' % key)
            try:
                print(newR-origR)
            except:
                pass
            mismatches += 1

if dosave:
    sc.saveobj(newfilename, newR)

print('Done; there were %s matches and %s mismatches.' % (matches, mismatches))