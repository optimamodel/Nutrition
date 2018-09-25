"""
main.py -- main module for the Optima Nutrition webapp.
    
Last update: 2018sep23
"""

import sciris as sc
import scirisweb as sw
from . import config, rpcs, apptasks # analysis:ignore

def make_app(**kwargs):
    T = sc.tic()
    app = sw.ScirisApp(name='Optima Nutrition', filepath=__file__, config=config, RPC_dict=rpcs.RPC_dict, **kwargs) # Create the ScirisApp object.  NOTE: app.config will thereafter contain all of the configuration parameters, including for Flask.
    sw.make_default_users(app)
    print('>> Webapp initialization complete (elapsed time: %0.2f s)' % sc.toc(T, output=True))
    return app

def run(**kwargs):
    app = make_app(**kwargs) # Make the app
    app.run() # Run the client page with Flask and a Twisted server.
    return None

if __name__ == '__main__':
    run()
