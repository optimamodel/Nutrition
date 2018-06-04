"""
Version:
"""

import nutrition as on

P = on.project.Project()
P.default_scens(dorun=True)
result = P.get_results('test1')
fig = on.plotting.make_plots(result) # HARDCODED EXAMPLE








