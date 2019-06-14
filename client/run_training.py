#!/usr/bin/env python


import sys

print('')
print('#########################################')
print('Starting Optima Nutrition Training server...')
print('#########################################')

# Process arguments
kwargs = {}
for i,arg in enumerate(sys.argv[1:]):
    try:
        k = arg.split("=")[0]
        v = arg.split("=")[1]
        kwargs[k] = v
        print('Including kwarg: "%s" = %s' % (k,v))
    except Exception as E:
        errormsg = 'Failed to parse argument key="%s", value="%s": %s' % (k, v, str(E))
        raise Exception(errormsg)

kwargs['SERVER_PORT'] = 9101
kwargs['REDIS_URL'] = 'redis://127.0.0.1:6379/10'

# Run the server
import nutrition_app as onwa
onwa.main.run(**kwargs)

